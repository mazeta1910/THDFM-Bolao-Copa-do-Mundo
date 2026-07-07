from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from src.loader import (
    aplicar_resultados_externos,
    atualizar_resultado,
    importar_resultados_da_planilha,
    limpar_todos_resultados,
    remover_resultados,
    salvar_resultados,
    validar_bolao,
)
from src.ranking import (
    calcular_pontos_faixa,
    calcular_variacoes_da_rodada,
    calcular_variacoes_jogos,
    carregar_classificacao_referencia,
    classificacao_geral_ativa,
    comparar_classificacoes,
    exportar_classificacao,
    exportar_classificacao_premio_a,
    exportar_classificacao_texto,
    formatar_classificacao_compartilhar,
    formatar_classificacao_fase_texto,
    FASES_BOLAO,
    gerar_classificacao_32avos,
    gerar_classificacao_fase,
    gerar_classificacao_grupos_mais_32avos,
    gerar_classificacao_jogos,
    gerar_classificacao_premio_a,
    legenda_pesos_fase,
    legenda_pesos_jogos_linhas,
    jogos_recem_realizados,
    referencia_tem_secao_grupos_32avos,
    referencia_tem_secao_oitavas,
    resolver_referencia_geral_csv,
    resolver_secao_e_baseline_referencia,
    resumir_jogos_export,
    sugerir_jogos_provisorios,
)
from src.snapshot import (
    calcular_mudancas_posicao,
    calcular_variacoes,
    carregar_snapshot,
    salvar_snapshot,
    snapshot_de_classificacao,
)
from src.palpites_view import (
    formatar_palpites_provisorio_texto,
    formatar_palpites_texto,
    listar_palpites_jogos,
)
from src.grupos_ranking import times_iguais
from src.models import PontosJogo
from src.scoring import FASE_GRUPOS_MAX
from src.exports_manager import (
    atualizar_manifest,
    caminho_fase,
    caminho_palpites,
    caminho_ultimo,
    formatar_resumo_ultimo,
    limpar_exports_legados,
)
from src.share_options import (
    SelecaoCompartilhar,
    ajustar_selecao_disponivel,
    disponibilidade_compartilhar,
    parse_export_list,
    selecao_completa,
)
from src.thdfm_parser import parse_thdfm_csv

try:
    from src.image_export import (
        exportar_classificacao_fase_png,
        exportar_classificacao_png,
        exportar_palpites_png,
        exportar_palpites_provisorios_png,
        exportar_premio_a_png,
        exportar_rodada_completa_png,
    )

    _PNG_DISPONIVEL = True
except ImportError:
    _PNG_DISPONIVEL = False

from src.data_paths import (
    BOLAO_CSV,
    CLASSIFICACAO_18AVOS_CSV,
    CLASSIFICACOES_REAIS_CSV,
    CRAVADURA_CSV,
    DATA_DIR,
    PALPITES_PENALTIS_CSV,
    PALPITES_PRIMEIRA_FASE_CSV,
    REFERENCIA_CSV,
    REFERENCIA_GERAL_CSV,
    RESPOSTAS_32_AVOS_CSV,
    RESULTADOS_CSV,
    SNAPSHOT_JSON,
    candidatos_referencia_geral,
    ensure_data_layout,
    resolver_bolao_csv,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS = Path.home() / "Downloads"

CLASSIFICACAO_CSV = caminho_ultimo(DATA_DIR, "classificacao_csv")
CLASSIFICACAO_TXT = caminho_ultimo(DATA_DIR, "classificacao_txt")
CLASSIFICACAO_PNG = caminho_ultimo(DATA_DIR, "classificacao_png")
CLASSIFICACAO_PREMIO_A_CSV = caminho_ultimo(DATA_DIR, "premio_a_csv")
CLASSIFICACAO_PREMIO_A_PNG = caminho_ultimo(DATA_DIR, "premio_a_png")
CLASSIFICACAO_32AVOS_PNG = caminho_ultimo(DATA_DIR, "fase_32avos_png")
CLASSIFICACAO_GRUPOS_32AVOS_PNG = caminho_ultimo(DATA_DIR, "fase_grupos_32avos_png")
RODADA_PNG = caminho_ultimo(DATA_DIR, "rodada_png")
RANKING_GRUPOS_TXT = caminho_ultimo(DATA_DIR, "ranking_grupos_txt")


def _finalizar_exports(descricoes: dict[str, str]) -> None:
    removidos = limpar_exports_legados(DATA_DIR)
    manifest = atualizar_manifest(DATA_DIR, descricoes)
    print(f"\n{formatar_resumo_ultimo(DATA_DIR)}")
    if removidos:
        print(f"Limpeza: {len(removidos)} arquivo(s) antigo(s) removido(s) de data/.")
    print(f"Indice: {manifest}")


def _resolve_arquivo(path: Path, fallback_name: str) -> Path:
    if path.exists():
        return path
    fallback = DOWNLOADS / fallback_name
    return fallback if fallback.exists() else path


def _resolver_bolao_csv() -> Path:
    return resolver_bolao_csv(DATA_DIR, downloads=DOWNLOADS)


def carregar_bolao(arquivo: Path | None = None):
    ensure_data_layout(DATA_DIR)
    path = arquivo or _resolver_bolao_csv()
    if not path.exists():
        raise FileNotFoundError(f"Arquivo do bolão não encontrado: {path}")

    bolao = parse_thdfm_csv(path)
    aplicar_resultados_externos(bolao, RESULTADOS_CSV)
    _aplicar_palpites_penaltis_bolao(bolao)
    return bolao


def _aplicar_palpites_penaltis_bolao(bolao) -> None:
    from src.penaltis import (
        aplicar_palpites_penaltis,
        carregar_palpites_penaltis,
        carregar_palpites_penaltis_respostas,
        exportar_palpites_penaltis,
    )

    palpites = carregar_palpites_penaltis(PALPITES_PENALTIS_CSV)
    if not palpites and RESPOSTAS_32_AVOS_CSV.exists():
        palpites = carregar_palpites_penaltis_respostas(RESPOSTAS_32_AVOS_CSV)
        if palpites:
            exportar_palpites_penaltis(palpites, PALPITES_PENALTIS_CSV)
    aplicar_palpites_penaltis(bolao, palpites)


def _carregar_baseline_variacao() -> tuple[dict[str, dict] | None, set[int], bool]:
    snapshot = carregar_snapshot(SNAPSHOT_JSON)
    if snapshot is not None:
        return (
            snapshot.get("participantes"),
            set(snapshot.get("jogos_ids", [])),
            True,
        )

    referencia_path = _resolver_referencia_geral() or _resolve_arquivo(
        REFERENCIA_CSV, "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv"
    )
    if referencia_path.exists():
        secao, baseline = resolver_secao_e_baseline_referencia(referencia_path)
        referencia = carregar_classificacao_referencia(referencia_path, secao=secao)
        return snapshot_de_classificacao(referencia), set(baseline), False

    return None, set(), False


def _resolver_referencia_geral() -> Path | None:
    return resolver_referencia_geral_csv(DATA_DIR, downloads=DOWNLOADS)


def _classificacao_jogos(bolao) -> list:
    """Classificacao B: referencia importada + jogos novos desde a baseline da fase."""
    ref = _resolver_referencia_geral()
    return classificacao_geral_ativa(
        bolao,
        importada_path=ref,
        data_dir=DATA_DIR,
    )


def _classificacao_premio_a(bolao) -> tuple[list, bool]:
    """Classificacao A: palpitadura dos grupos + cravadura (quando REAL OFICIAL existir)."""
    return gerar_classificacao_premio_a(
        bolao.participantes,
        classificacoes_reais_path=CLASSIFICACOES_REAIS_CSV,
        palpites_grupos_path=PALPITES_PRIMEIRA_FASE_CSV,
        cravadura_path=CRAVADURA_CSV,
    )


def _tabelas_mata_mata(bolao) -> tuple[list | None, list | None]:
    """Tabelas extras de 32 avos quando houver jogos J73+ realizados."""
    if not any(j.realizado and j.id >= 73 for j in bolao.jogos):
        return None, None
    return (
        gerar_classificacao_32avos(bolao),
        _classificacao_jogos(bolao),
    )


def _atualizar_exports_classificacao(bolao) -> None:
    classificacao = _classificacao_jogos(bolao)
    premio_a, cravadura_ativa = _classificacao_premio_a(bolao)
    classificacao_32avos, classificacao_grupos_32avos = _tabelas_mata_mata(bolao)
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    variacoes = calcular_variacoes(classificacao, None)
    mudancas_posicao = calcular_mudancas_posicao(classificacao, None)
    exportar_classificacao(classificacao, CLASSIFICACAO_CSV)
    exportar_classificacao_premio_a(premio_a, CLASSIFICACAO_PREMIO_A_CSV)
    exportar_classificacao_texto(
        classificacao,
        CLASSIFICACAO_TXT,
        jogos_realizados=realizados,
        total_jogos=len(bolao.jogos),
        variacoes=variacoes,
        mudancas_posicao=mudancas_posicao,
        premio_a=premio_a,
        cravadura_ativa=cravadura_ativa,
        classificacao_32avos=classificacao_32avos,
        classificacao_grupos_32avos=classificacao_grupos_32avos,
    )
    if _PNG_DISPONIVEL:
        exportar_classificacao_png(
            classificacao,
            CLASSIFICACAO_PNG,
            jogos_realizados=realizados,
            total_jogos=len(bolao.jogos),
            variacoes=variacoes,
            mudancas_posicao=mudancas_posicao,
        )
        exportar_premio_a_png(
            premio_a,
            CLASSIFICACAO_PREMIO_A_PNG,
            cravadura_ativa=cravadura_ativa,
        )
        if classificacao_32avos is not None:
            _exportar_png_fase(bolao, "32avos", CLASSIFICACAO_32AVOS_PNG)
        if classificacao_grupos_32avos is not None:
            _exportar_png_fase(bolao, "grupos_mais_32avos", CLASSIFICACAO_GRUPOS_32AVOS_PNG)


def _salvar_baseline(bolao, *, mensagem_snapshot: bool = True) -> None:
    classificacao = _classificacao_jogos(bolao)
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    jogos_ids = [jogo.id for jogo in bolao.jogos if jogo.realizado]
    salvar_snapshot(
        SNAPSHOT_JSON,
        classificacao,
        jogos_realizados=realizados,
        jogos_ids=jogos_ids,
    )
    if mensagem_snapshot:
        print(f"Baseline salva em {SNAPSHOT_JSON.name}.")

    if _PNG_DISPONIVEL:
        variacoes = calcular_variacoes(classificacao, None)
        mudancas = calcular_mudancas_posicao(classificacao, None)
        exportar_classificacao_png(
            classificacao,
            CLASSIFICACAO_PNG,
            jogos_realizados=realizados,
            total_jogos=len(bolao.jogos),
            variacoes=variacoes,
            mudancas_posicao=mudancas,
        )
        print(f"Classificação em {CLASSIFICACAO_PNG.name}")


def cmd_importar(args: argparse.Namespace) -> int:
    path = Path(args.arquivo)
    bolao = parse_thdfm_csv(path)
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    print(f"Jogos: {len(bolao.jogos)}")
    print(f"Participantes: {len(bolao.participantes)}")
    print(f"Palpites: {len(bolao.palpites)}")
    print(f"Resultados preenchidos: {realizados}")
    return 0


def cmd_importar_resultados(args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    origem = Path(args.arquivo) if args.arquivo else BOLAO_CSV
    if not origem.exists():
        print(f"Arquivo não encontrado: {origem}", file=sys.stderr)
        return 1

    realizados, total = importar_resultados_da_planilha(origem, RESULTADOS_CSV)
    print(f"Importados {realizados} de {total} resultados a partir de {origem.name}")
    print(f"Salvo em {RESULTADOS_CSV.name}")

    bolao = carregar_bolao()
    erros = validar_bolao(bolao)
    if erros:
        print("Avisos na planilha:")
        for erro in erros:
            print(f"  - {erro}")
        return 1

    if not args.sem_baseline:
        _salvar_baseline(bolao)

    if args.conferir and REFERENCIA_CSV.exists():
        return cmd_conferir(argparse.Namespace())

    return 0


def cmd_importar_referencia(args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    origem = Path(args.arquivo)
    if not origem.exists():
        origem = _resolve_arquivo(origem, args.arquivo)
    if not origem.exists():
        print(f"Arquivo não encontrado: {args.arquivo}", file=sys.stderr)
        return 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_data_layout(DATA_DIR)
    if referencia_tem_secao_oitavas(origem) or origem.name == "classificacao_18avos.csv":
        destino = CLASSIFICACAO_18AVOS_CSV
    elif referencia_tem_secao_grupos_32avos(origem):
        destino = REFERENCIA_GERAL_CSV
    else:
        destino = REFERENCIA_CSV
    destino.parent.mkdir(parents=True, exist_ok=True)
    if origem.resolve() != destino.resolve():
        shutil.copy2(origem, destino)
    secao, baseline = resolver_secao_e_baseline_referencia(destino)
    classificacao = carregar_classificacao_referencia(destino, secao=secao)
    print(
        f"Classificação importada: {len(classificacao)} participantes em {destino.name}"
    )
    print("Essa tabela passa a ser usada pelo programa (classificar, compartilhar e PNG).")

    bolao = carregar_bolao()
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    jogos_ids = sorted(baseline & {j.id for j in bolao.jogos if j.realizado})
    if not jogos_ids:
        jogos_ids = [jogo.id for jogo in bolao.jogos if jogo.realizado]
    salvar_snapshot(
        SNAPSHOT_JSON,
        classificacao,
        jogos_realizados=realizados,
        jogos_ids=jogos_ids,
    )
    print(f"Baseline salva em {SNAPSHOT_JSON.name} ({realizados} jogos).")

    _atualizar_exports_classificacao(bolao)
    _finalizar_exports(
        {
            "classificacao_txt": "Texto completo para compartilhar",
            "classificacao_png": "Classificacao geral (premio B)",
            "classificacao_csv": "Planilha premio B",
            "premio_a_png": "Cravadura + palpitadura dos grupos",
            "fase_32avos_png": "Pontuacao parcial 32 avos (Placar/Vencedor/Gols/Soma)",
            "fase_grupos_32avos_png": "Pontuacao parcial grupos + 32 avos (detalhada)",
        }
    )
    print(f"Arquivos atualizados: {CLASSIFICACAO_TXT.name}, {CLASSIFICACAO_CSV.name}", end="")
    if _PNG_DISPONIVEL:
        print(f", {CLASSIFICACAO_PNG.name}")
    else:
        print()
        print("PNG não gerado: instale Pillow com 'pip install pillow'.", file=sys.stderr)
    return 0


def cmd_validar(args: argparse.Namespace) -> int:
    bolao = carregar_bolao()
    erros = validar_bolao(bolao)
    if erros:
        print("Erros encontrados:")
        for erro in erros:
            print(f"  - {erro}")
        return 1

    realizados = sum(1 for j in bolao.jogos if j.realizado)
    print("Bolão válido.")
    print(f"  Jogos: {len(bolao.jogos)}")
    print(f"  Participantes: {len(bolao.participantes)}")
    print(f"  Resultados: {realizados}/{len(bolao.jogos)}")
    return 0


def _parse_placar(texto: str) -> tuple[int, int]:
    match = re.match(r"^\s*(\d+)\s*[-xX]\s*(\d+)\s*$", texto)
    if not match:
        raise ValueError(f"Placar inválido: {texto!r}. Use o formato 2-1.")
    return int(match.group(1)), int(match.group(2))


def _resolver_vencedor_penaltis(jogo, texto: str) -> str:
    escolha = texto.strip()
    if not escolha:
        raise ValueError("Informe o time que passou nos penaltis.")
    if times_iguais(escolha, jogo.casa):
        return jogo.casa.strip()
    if times_iguais(escolha, jogo.fora):
        return jogo.fora.strip()
    raise ValueError(
        f"Time invalido: {escolha!r}. Use {jogo.casa.strip()} ou {jogo.fora.strip()}."
    )


def _registrar_resultado_jogo(
    bolao,
    jogo,
    casa: int,
    fora: int,
    *,
    vencedor_penaltis: str | None = None,
    perguntar_penaltis: bool = False,
    provisorio: bool = False,
) -> bool:
    """Registra placar. Retorna True se for placar parcial (jogo rolando)."""
    penaltis = vencedor_penaltis
    empate_mata_mata = jogo.id > FASE_GRUPOS_MAX and casa == fora

    if empate_mata_mata and not provisorio and not penaltis:
        if perguntar_penaltis:
            texto = input(
                f"Empate no mata-mata.\n"
                f"  Enter = placar parcial (jogo rolando)\n"
                f"  {jogo.casa.strip()} ou {jogo.fora.strip()} = passou nos penaltis\n"
                f"Escolha: "
            ).strip()
            if not texto:
                provisorio = True
            else:
                penaltis = _resolver_vencedor_penaltis(jogo, texto)
        else:
            raise ValueError(
                "Empate no mata-mata: use --provisorio (placar parcial) "
                "ou --penaltis (time que passou nos penaltis)."
            )

    if empate_mata_mata and not provisorio and not penaltis:
        raise ValueError(
            "Empate no mata-mata: informe --penaltis ou use --provisorio "
            "para placar parcial enquanto o jogo rola."
        )

    atualizar_resultado(
        bolao,
        jogo.id,
        casa,
        fora,
        vencedor_penaltis=None if provisorio else penaltis,
    )
    return provisorio


def cmd_resultado(args: argparse.Namespace) -> int:
    bolao = carregar_bolao()

    if args.remover:
        if not args.jogo:
            print("Informe --jogo com um ou mais IDs para remover.")
            return 1
        removidos = remover_resultados(bolao, args.jogo)
        for jogo in removidos:
            print(f"Jogo {jogo.id} ({jogo.casa} x {jogo.fora}): resultado removido")
        salvar_resultados(bolao, RESULTADOS_CSV)
        print(f"Resultados salvos em {RESULTADOS_CSV}")
        return 0

    if args.interativo:
        pendentes = [j for j in bolao.jogos if not j.realizado]
        if not pendentes:
            print("Todos os jogos já têm resultado.")
            return 0

        print("Enter pula o jogo; 'sair' ou 'cancelar' encerra.\n")
        try:
            for jogo in pendentes:
                texto = input(
                    f"Jogo {jogo.id}: {jogo.casa} x {jogo.fora} ({jogo.data})\n"
                    f"Placar [Enter pula / sair cancela]: "
                ).strip()
                if not texto:
                    continue
                if texto.lower() in {"sair", "s", "q", "quit", "cancelar", "c"}:
                    print("Encerrando. Resultados ja registrados serao salvos.")
                    break
                try:
                    casa, fora = _parse_placar(texto)
                    parcial = _registrar_resultado_jogo(
                        bolao, jogo, casa, fora, perguntar_penaltis=True
                    )
                    msg = f"  Registrado: {casa}-{fora}"
                    if parcial:
                        msg += " (parcial)"
                    elif jogo.vencedor_penaltis:
                        msg += f" (penaltis: {jogo.vencedor_penaltis})"
                    print(msg)
                except ValueError as exc:
                    print(f"  Erro: {exc}")
        except KeyboardInterrupt:
            print("\nInterrompido. Resultados ja registrados serao salvos.")
    else:
        if args.jogo is None or args.placar is None:
            print("Informe --jogo e --placar, ou use --interativo.")
            return 1
        if len(args.jogo) != 1:
            print("Informe apenas um jogo por vez ao registrar placar.")
            return 1
        casa, fora = _parse_placar(args.placar)
        jogo = next(j for j in bolao.jogos if j.id == args.jogo[0])
        penaltis = getattr(args, "penaltis", None)
        if penaltis:
            penaltis = _resolver_vencedor_penaltis(jogo, penaltis)
        parcial = _registrar_resultado_jogo(
            bolao,
            jogo,
            casa,
            fora,
            vencedor_penaltis=penaltis,
            perguntar_penaltis=getattr(args, "perguntar_penaltis", False),
            provisorio=getattr(args, "provisorio", False),
        )
        msg = f"Jogo {jogo.id} ({jogo.casa} x {jogo.fora}): {casa}-{fora}"
        if parcial:
            msg += " (parcial)"
        elif jogo.vencedor_penaltis:
            msg += f" (penaltis: {jogo.vencedor_penaltis})"
        print(msg)

    salvar_resultados(bolao, RESULTADOS_CSV)
    print(f"Resultados salvos em {RESULTADOS_CSV}")
    return 0


def _imprimir_classificacao(classificacao: list) -> None:
    print(f"{'Pos':>3}  {'Participante':<28} {'Placar':>6} {'Vencedor':>8} {'Gols casa':>9} {'Gols fora':>9} {'Soma':>5}")
    print("-" * 78)
    for linha in classificacao:
        print(
            f"{linha.posicao:>3}  {linha.participante:<28} "
            f"{linha.placar:>6} {linha.vencedor:>8} {linha.gols_casa:>9} {linha.gols_fora:>9} {linha.soma:>5}"
        )


def _contar_jogos_fase(bolao, fase_id: str) -> tuple[int, int]:
    fase = FASES_BOLAO[fase_id]
    realizados = sum(
        1 for jogo in bolao.jogos if jogo.realizado and jogo.id in fase.jogos_ids
    )
    return realizados, len(fase.jogos_ids)


def _exportar_png_fase(bolao, fase_id: str, path: Path) -> None:
    fase = FASES_BOLAO[fase_id]
    classificacao = gerar_classificacao_fase(bolao, fase_id)
    realizados, total = _contar_jogos_fase(bolao, fase_id)
    exportar_classificacao_fase_png(
        classificacao,
        path,
        titulo=fase.titulo,
        rodape=legenda_pesos_fase(fase_id),
        jogos_realizados=realizados,
        total_jogos=total,
        fase_id=fase_id,
    )


def cmd_fase(args: argparse.Namespace) -> int:
    fase_id = args.fase.lower()
    if fase_id not in FASES_BOLAO:
        opcoes = ", ".join(FASES_BOLAO)
        print(f"Fase invalida. Opcoes: {opcoes}")
        return 1

    bolao = carregar_bolao()
    classificacao = gerar_classificacao_fase(bolao, fase_id)
    realizados, total = _contar_jogos_fase(bolao, fase_id)
    texto = formatar_classificacao_fase_texto(
        classificacao,
        fase_id=fase_id,
        jogos_realizados=realizados,
        total_jogos=total,
    )
    print(texto)

    txt_path = caminho_fase(DATA_DIR, fase_id, "txt")
    png_path = caminho_fase(DATA_DIR, fase_id, "png")
    if not args.sem_arquivo:
        txt_path.write_text(texto + "\n", encoding="utf-8")
        print(f"\nTexto salvo em {txt_path}")
    if not args.sem_png:
        if not _PNG_DISPONIVEL:
            print("PNG nao gerado: instale Pillow.", file=sys.stderr)
        else:
            _exportar_png_fase(bolao, fase_id, png_path)
            print(f"Imagem salva em {png_path}")
    _finalizar_exports(
        {
            "classificacao_png": "Classificacao geral (premio B)",
            f"fase_{fase_id}": f"Pontuacao parcial detalhada ({fase_id})",
        }
    )
    return 0


def cmd_classificar(args: argparse.Namespace) -> int:
    bolao = carregar_bolao()
    classificacao = _classificacao_jogos(bolao)
    _imprimir_classificacao(classificacao)
    return 0


def cmd_ranking_grupos(args: argparse.Namespace) -> int:
    from src.grupos_ranking import formatar_ranking_grupos, gerar_ranking_grupos

    reais_path = Path(args.reais) if args.reais else CLASSIFICACOES_REAIS_CSV
    palpites_path = Path(args.palpites) if args.palpites else PALPITES_PRIMEIRA_FASE_CSV
    if not reais_path.exists():
        raise FileNotFoundError(f"Classificacoes reais nao encontradas: {reais_path}")
    if not palpites_path.exists():
        raise FileNotFoundError(f"Palpites da primeira fase nao encontrados: {palpites_path}")

    ranking, resumo = gerar_ranking_grupos(reais_path, palpites_path)
    texto = formatar_ranking_grupos(ranking, resumo, detalhe=args.detalhe)
    print(texto)

    if not args.sem_arquivo:
        RANKING_GRUPOS_TXT.write_text(texto + "\n", encoding="utf-8")
        print(f"\nTexto salvo em {RANKING_GRUPOS_TXT}")
    return 0


def cmd_exportar(args: argparse.Namespace) -> int:
    bolao = carregar_bolao()
    classificacao = _classificacao_jogos(bolao)
    exportar_classificacao(classificacao, CLASSIFICACAO_CSV)
    print(f"Classificação exportada para {CLASSIFICACAO_CSV}")
    return 0


def _variacoes_zeradas(classificacao: list) -> dict[str, int]:
    return {linha.participante.strip(): 0 for linha in classificacao}


def _calcular_variacoes_compartilhar(
    bolao,
    classificacao: list,
    *,
    baseline: dict[str, dict] | None,
    jogos_ids_baseline: set[int],
    tem_snapshot: bool,
    zerar_variacao: bool,
) -> dict[str, int | None]:
    if zerar_variacao:
        return _variacoes_zeradas(classificacao)
    if tem_snapshot:
        return calcular_variacoes_da_rodada(bolao, jogos_ids_baseline)
    if baseline is not None:
        return calcular_variacoes(classificacao, baseline)
    return {linha.participante.strip(): None for linha in classificacao}


def _resolver_selecao_compartilhar(
    args: argparse.Namespace,
    disponivel,
) -> SelecaoCompartilhar:
    from dataclasses import replace

    selecao = getattr(args, "selecao", None)
    export = getattr(args, "export", None)
    if selecao is not None:
        base = selecao
    elif export:
        base = parse_export_list(export)
    else:
        incluir_rodada = bool(getattr(args, "jogo", None))
        base = selecao_completa(incluir_rodada=incluir_rodada)

    if getattr(args, "sem_arquivo", False):
        base = replace(base, texto=False)
    if getattr(args, "sem_png", False):
        base = replace(
            base,
            classificacao_png=False,
            premio_a_png=False,
            fase_32avos_png=False,
            fase_grupos_32avos_png=False,
            rodada_png=False,
        )
    if getattr(args, "jogo", None) and selecao is None and not export:
        base = replace(base, rodada_png=True)
    return ajustar_selecao_disponivel(base, disponivel)


def cmd_confirmar_rodada(_args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    bolao = carregar_bolao()
    classificacao = _classificacao_jogos(bolao)
    realizados = sum(1 for jogo in bolao.jogos if jogo.realizado)
    jogos_ids = [jogo.id for jogo in bolao.jogos if jogo.realizado]
    salvar_snapshot(
        SNAPSHOT_JSON,
        classificacao,
        jogos_realizados=realizados,
        jogos_ids=jogos_ids,
    )
    print(f"Rodada confirmada. Baseline salva em {SNAPSHOT_JSON.name}.")
    print("Na proxima divulgacao, a coluna Rod comeca zerada.")
    return 0


def cmd_compartilhar(args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    bolao = carregar_bolao()
    classificacao = _classificacao_jogos(bolao)
    premio_a, cravadura_ativa = _classificacao_premio_a(bolao)
    classificacao_32avos, classificacao_grupos_32avos = _tabelas_mata_mata(bolao)
    disponivel = disponibilidade_compartilhar(
        tem_premio_a=bool(premio_a),
        classificacao_32avos=classificacao_32avos,
        classificacao_grupos_32avos=classificacao_grupos_32avos,
    )
    selecao = _resolver_selecao_compartilhar(args, disponivel)
    secoes = selecao.secoes_texto()
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    jogos_ids = [jogo.id for jogo in bolao.jogos if jogo.realizado]

    if args.zerar_variacao:
        baseline_participantes = snapshot_de_classificacao(classificacao)
        jogos_ids_anteriores = set(jogos_ids)
        tem_snapshot = True
    else:
        baseline_participantes, jogos_ids_anteriores, tem_snapshot = _carregar_baseline_variacao()

    variacoes = _calcular_variacoes_compartilhar(
        bolao,
        classificacao,
        baseline=baseline_participantes,
        jogos_ids_baseline=jogos_ids_anteriores,
        tem_snapshot=tem_snapshot,
        zerar_variacao=args.zerar_variacao,
    )
    mudancas_posicao = calcular_mudancas_posicao(classificacao, baseline_participantes)
    jogos_novos = (
        [] if args.zerar_variacao else jogos_recem_realizados(bolao, jogos_ids_anteriores)
        if tem_snapshot
        else []
    )

    jogo_ids_export = getattr(args, "jogo", None)
    if not jogo_ids_export:
        ultimos = getattr(args, "ultimos", None)
        if ultimos is not None:
            jogo_ids_export = sugerir_jogos_provisorios(
                bolao, jogos_ids_anteriores, limite=ultimos
            )
    legenda_rodada = None
    if jogo_ids_export:
        variacoes = calcular_variacoes_jogos(bolao, set(jogo_ids_export))
        jogos_novos = resumir_jogos_export(bolao, jogo_ids_export)
        ids_txt = ", ".join(str(jogo_id) for jogo_id in jogo_ids_export)
        legenda_rodada = f"TOTAL = pontos nos jogos {ids_txt} desta imagem"

    if not selecao.algum_export():
        print("Nenhum export selecionado.", file=sys.stderr)
        return 1

    jogo_ids = jogo_ids_export if jogo_ids_export else getattr(args, "jogo", None)
    if selecao.rodada_png and not jogo_ids:
        print(
            "Export rodada.png requer jogos com placar provisorio (informe IDs).",
            file=sys.stderr,
        )
        return 1

    if (
        selecao.texto
        or secoes.classificacao_geral
        or secoes.premio_a
        or secoes.fase_32avos
        or secoes.fase_grupos_32avos
    ):
        texto = formatar_classificacao_compartilhar(
            classificacao,
            jogos_realizados=realizados,
            total_jogos=len(bolao.jogos),
            variacoes=variacoes,
            mudancas_posicao=mudancas_posicao,
            jogos_novos=jogos_novos or None,
            legenda_rodada=legenda_rodada,
            premio_a=premio_a,
            cravadura_ativa=cravadura_ativa,
            classificacao_32avos=classificacao_32avos,
            classificacao_grupos_32avos=classificacao_grupos_32avos,
            secoes=secoes,
        )
        print(texto)
    else:
        print("Gerando exports selecionados (sem texto completo no terminal).")

    if selecao.texto and not args.sem_arquivo:
        exportar_classificacao_texto(
            classificacao,
            CLASSIFICACAO_TXT,
            jogos_realizados=realizados,
            total_jogos=len(bolao.jogos),
            variacoes=variacoes,
            mudancas_posicao=mudancas_posicao,
            jogos_novos=jogos_novos or None,
            legenda_rodada=legenda_rodada,
            premio_a=premio_a,
            cravadura_ativa=cravadura_ativa,
            classificacao_32avos=classificacao_32avos,
            classificacao_grupos_32avos=classificacao_grupos_32avos,
            secoes=secoes,
        )
        print(f"\nTexto salvo em {CLASSIFICACAO_TXT}")

    precisa_png = (
        selecao.classificacao_png
        or selecao.premio_a_png
        or selecao.fase_32avos_png
        or selecao.fase_grupos_32avos_png
        or selecao.rodada_png
    )
    if not args.sem_png and precisa_png:
        if not _PNG_DISPONIVEL:
            print(
                "PNG nao gerado: instale Pillow com 'pip install pillow' e rode de novo.",
                file=sys.stderr,
            )
        else:
            if selecao.classificacao_png:
                exportar_classificacao_png(
                    classificacao,
                    CLASSIFICACAO_PNG,
                    jogos_realizados=realizados,
                    total_jogos=len(bolao.jogos),
                    variacoes=variacoes,
                    mudancas_posicao=mudancas_posicao,
                    jogos_novos=jogos_novos or None,
                )
                print(f"Imagem salva em {CLASSIFICACAO_PNG}")
            if selecao.premio_a_png:
                exportar_premio_a_png(
                    premio_a,
                    CLASSIFICACAO_PREMIO_A_PNG,
                    cravadura_ativa=cravadura_ativa,
                )
                print(f"Imagem salva em {CLASSIFICACAO_PREMIO_A_PNG}")
            if selecao.fase_32avos_png and classificacao_32avos is not None:
                _exportar_png_fase(bolao, "32avos", CLASSIFICACAO_32AVOS_PNG)
                print(f"Imagem salva em {CLASSIFICACAO_32AVOS_PNG}")
            if selecao.fase_grupos_32avos_png and classificacao_grupos_32avos is not None:
                _exportar_png_fase(bolao, "grupos_mais_32avos", CLASSIFICACAO_GRUPOS_32AVOS_PNG)
                print(f"Imagem salva em {CLASSIFICACAO_GRUPOS_32AVOS_PNG}")

    descricoes_exports: dict[str, str] = {}
    if selecao.texto:
        descricoes_exports["classificacao_txt"] = "Texto completo para compartilhar"
    if selecao.classificacao_png:
        descricoes_exports["classificacao_png"] = "Classificacao geral (premio B)"
    if selecao.premio_a_png:
        descricoes_exports["premio_a_png"] = "Cravadura + palpitadura dos grupos"
    if selecao.fase_32avos_png and classificacao_32avos is not None:
        descricoes_exports["fase_32avos_png"] = (
            "Pontuacao parcial 32 avos (Placar/Vencedor/Gols/Soma)"
        )
    if selecao.fase_grupos_32avos_png and classificacao_grupos_32avos is not None:
        descricoes_exports["fase_grupos_32avos_png"] = (
            "Pontuacao parcial grupos + 32 avos (detalhada)"
        )

    jogo_ids = jogo_ids_export if jogo_ids_export else getattr(args, "jogo", None)
    if selecao.rodada_png and jogo_ids and not args.sem_png:
        if not _PNG_DISPONIVEL:
            print(
                "Imagem completa nao gerada: instale Pillow com 'pip install pillow'.",
                file=sys.stderr,
            )
        else:
            blocos = listar_palpites_jogos(bolao, jogo_ids)
            sem_placar = [bloco.jogo.id for bloco in blocos if not bloco.jogo.realizado]
            if sem_placar:
                ids = ", ".join(str(jogo_id) for jogo_id in sem_placar)
                print(f"Jogos sem placar provisorio: {ids}", file=sys.stderr)
                return 1
            rodada_path = RODADA_PNG
            totais_rodada = calcular_pontos_faixa(bolao, set(jogo_ids))
            destaques_rodada = {
                nome: PontosJogo(
                    placar=item.placar,
                    vencedor=item.vencedor,
                    gols_casa=item.gols_casa,
                    gols_fora=item.gols_fora,
                )
                for nome, item in totais_rodada.items()
            }
            variacoes_rodada = {nome: item.soma for nome, item in totais_rodada.items()}
            exportar_rodada_completa_png(
                classificacao,
                blocos,
                rodada_path,
                jogos_realizados=realizados,
                total_jogos=len(bolao.jogos),
                variacoes=variacoes_rodada,
                mudancas_posicao=mudancas_posicao,
                jogos_novos=jogos_novos or None,
                destaques_rodada=destaques_rodada,
                rodape_linhas=legenda_pesos_jogos_linhas(set(jogo_ids)),
                omitir_breadcrumb=True,
            )
            ids_txt = ", ".join(str(jogo_id) for jogo_id in jogo_ids)
            descricoes_exports["rodada_png"] = f"Classificacao + provisorio (J{ids_txt})"
            print(f"Imagem completa salva em {rodada_path}")

    if descricoes_exports:
        _finalizar_exports(descricoes_exports)

    if args.confirmar_rodada or args.zerar_variacao:
        salvar_snapshot(
            SNAPSHOT_JSON,
            classificacao,
            jogos_realizados=realizados,
            jogos_ids=jogos_ids,
        )
        if args.confirmar_rodada:
            print(f"Rodada confirmada. Baseline salva em {SNAPSHOT_JSON.name}.")

    return 0


def cmd_proximos(args: argparse.Namespace) -> int:
    bolao = carregar_bolao()
    pendentes = [j for j in bolao.jogos if not j.realizado]
    if not pendentes:
        print("Todos os jogos já têm resultado.")
        return 0

    limite = args.limite or len(pendentes)
    print(f"Próximos jogos sem resultado ({len(pendentes)} no total):\n")
    for jogo in pendentes[:limite]:
        print(f"  Jogo {jogo.id:>2}: {jogo.casa} x {jogo.fora}  ({jogo.data})")
    print("\nPara registrar:")
    print("  python -m src.cli resultado --jogo ID --placar 2-1")
    print("  python -m src.cli resultado --interativo")
    return 0


def cmd_palpites(args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    bolao = carregar_bolao()
    blocos = listar_palpites_jogos(bolao, args.jogo)

    if args.provisorio:
        realizados = [bloco for bloco in blocos if bloco.jogo.realizado]
        if not realizados:
            print("Nenhum dos jogos informados tem placar provisorio.", file=sys.stderr)
            return 1
        texto = formatar_palpites_provisorio_texto(blocos)
    else:
        texto = formatar_palpites_texto(blocos)
    print(texto)

    if not args.sem_arquivo:
        txt_path = caminho_palpites(DATA_DIR, args.provisorio, "txt")
        txt_path.write_text(texto + "\n", encoding="utf-8")
        print(f"\nTexto salvo em {txt_path}")

    if not args.sem_png:
        if not _PNG_DISPONIVEL:
            print(
                "PNG nao gerado: instale Pillow com 'pip install pillow' e rode de novo.",
                file=sys.stderr,
            )
        else:
            png_path = caminho_palpites(DATA_DIR, args.provisorio, "png")
            if args.provisorio:
                exportar_palpites_provisorios_png(blocos, png_path)
            else:
                exportar_palpites_png(blocos, png_path)
            print(f"Imagem salva em {png_path}")

    chave = "palpites_provisorios" if args.provisorio else "palpites"
    ids_txt = ", ".join(str(jogo_id) for jogo_id in args.jogo)
    _finalizar_exports({chave: f"Palpites dos jogos J{ids_txt}"})

    return 0


def cmd_baseline(_args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    bolao = carregar_bolao()
    _salvar_baseline(bolao, mensagem_snapshot=True)
    print(
        "Baseline pre-rodada salva. Use compartilhar durante os jogos; "
        "ao final, compartilhar --confirmar-rodada."
    )
    return 0


def cmd_conferir(_args: argparse.Namespace) -> int:
    referencia_path = _resolver_referencia_geral() or _resolve_arquivo(
        REFERENCIA_CSV, "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv"
    )
    if not referencia_path.exists():
        print(f"Arquivo de referência não encontrado: {referencia_path}")
        return 1

    bolao = carregar_bolao()
    calculada = gerar_classificacao_jogos(bolao)
    secao = "grupos_32avos" if referencia_tem_secao_grupos_32avos(referencia_path) else "grupos"
    referencia = carregar_classificacao_referencia(referencia_path, secao=secao)
    diferencas = comparar_classificacoes(calculada, referencia)

    if not diferencas:
        print("Classificação calculada confere com a referência.")
        return 0

    print("Diferenças entre cálculo automático e referência do Excel:")
    for diff in diferencas[:40]:
        print(f"  - {diff}")
    if len(diferencas) > 40:
        print(f"  ... e mais {len(diferencas) - 40} diferença(s)")
    print(
        "\nA tabela geral exibida usa a referência do Excel; "
        "novos jogos (J80+) serão somados automaticamente."
    )
    return 1


def _arquivos_reset() -> list[Path]:
    return [
        SNAPSHOT_JSON,
        REFERENCIA_CSV,
        CLASSIFICACAO_TXT,
        CLASSIFICACAO_PNG,
        CLASSIFICACAO_CSV,
    ]


def cmd_reset(args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    origem = Path(args.arquivo) if args.arquivo else _resolver_bolao_csv()
    if not origem.exists():
        print(f"Arquivo do bolão não encontrado: {origem}", file=sys.stderr)
        return 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_data_layout(DATA_DIR)
    BOLAO_CSV.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, BOLAO_CSV)
    print(f"Planilha ativa: {BOLAO_CSV.name} (copiada de {origem.name})")

    for path in _arquivos_reset():
        if path.exists():
            path.unlink()
            print(f"Removido: {path.name}")

    bolao = parse_thdfm_csv(BOLAO_CSV)
    if args.com_resultados:
        realizados_planilha, _ = importar_resultados_da_planilha(BOLAO_CSV, RESULTADOS_CSV)
        print(
            f"Resultados importados da planilha: {realizados_planilha} jogos em {RESULTADOS_CSV.name}"
        )
    else:
        limpar_todos_resultados(bolao)
        salvar_resultados(bolao, RESULTADOS_CSV)
        print(f"Resultados zerados em {RESULTADOS_CSV.name}")

    bolao = carregar_bolao()
    erros = validar_bolao(bolao)
    if erros:
        print("Erros na planilha:")
        for erro in erros:
            print(f"  - {erro}")
        return 1

    realizados = sum(1 for j in bolao.jogos if j.realizado)
    pendentes = [j for j in bolao.jogos if not j.realizado]
    print(f"\nBolão pronto: {len(bolao.jogos)} jogos, {len(bolao.participantes)} participantes.")
    print(f"Resultados registrados: {realizados}/{len(bolao.jogos)}")
    if pendentes:
        proximos = pendentes[:6]
        print("\nPróximos jogos:")
        for jogo in proximos:
            print(f"  Jogo {jogo.id}: {jogo.casa} x {jogo.fora} ({jogo.data})")
        if len(pendentes) > len(proximos):
            print(f"  ... e mais {len(pendentes) - len(proximos)} jogos")

    if not args.sem_baseline:
        _salvar_baseline(bolao, mensagem_snapshot=True)
        print("Variação na coluna Rodada começa no próximo compartilhar.")

    print("\nUse 'python -m src.cli resultado --interativo' após cada rodada.")
    return 0


def cmd_bandeiras(args: argparse.Namespace) -> int:
    from src.flag_cache import FLAG_DIR, baixar_todas_bandeiras

    print(f"Baixando bandeiras para {FLAG_DIR} ...")
    sucesso, total_falhas, falhas = baixar_todas_bandeiras(forcar=args.forcar)
    print(f"Concluido: {sucesso} bandeira(s) em cache.")
    if falhas:
        print(f"Falhas ({total_falhas}):")
        for item in falhas:
            print(f"  - {item}")
        return 1
    return 0


def cmd_menu(_args: argparse.Namespace) -> int:
    from src.menu import executar_menu

    return executar_menu()


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv == ["menu"]:
        from src.menu import executar_menu

        return executar_menu()

    parser = argparse.ArgumentParser(description="Bolão THDFM Copa do Mundo 2026")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_menu = subparsers.add_parser("menu", help="Menu interativo principal")
    p_menu.set_defaults(func=cmd_menu)

    p_importar = subparsers.add_parser("importar", help="Importa e resume o CSV do bolão")
    p_importar.add_argument("--arquivo", default=str(BOLAO_CSV))
    p_importar.set_defaults(func=cmd_importar)

    p_validar = subparsers.add_parser("validar", help="Valida integridade dos dados")
    p_validar.set_defaults(func=cmd_validar)

    p_resultado = subparsers.add_parser("resultado", help="Registra resultado de jogo(s)")
    p_resultado.add_argument("--jogo", type=int, nargs="+")
    p_resultado.add_argument("--placar", help="Formato: 2-1")
    p_resultado.add_argument(
        "--penaltis",
        help="Time que passou nos penaltis (empate final no mata-mata)",
    )
    p_resultado.add_argument(
        "--provisorio",
        action="store_true",
        help="Placar parcial (ex.: 0-0 com jogo rolando); nao exige penaltis",
    )
    p_resultado.add_argument(
        "--remover",
        action="store_true",
        help="Remove o placar dos jogos informados em --jogo",
    )
    p_resultado.add_argument("--interativo", action="store_true")
    p_resultado.set_defaults(func=cmd_resultado)

    p_classificar = subparsers.add_parser("classificar", help="Exibe classificação")
    p_classificar.set_defaults(func=cmd_classificar)

    p_ranking_grupos = subparsers.add_parser(
        "ranking-grupos",
        help="Ranking parcial da classificacao dos grupos (10 pts por time cravado)",
    )
    p_ranking_grupos.add_argument(
        "--reais",
        help="CSV com classificacoes reais por grupo",
    )
    p_ranking_grupos.add_argument(
        "--palpites",
        help="CSV de respostas da primeira fase (palpites de grupos)",
    )
    p_ranking_grupos.add_argument(
        "--detalhe",
        action="store_true",
        help="Mostra pontos por grupo na mesma linha",
    )
    p_ranking_grupos.add_argument(
        "--sem-arquivo",
        action="store_true",
        help="Nao salva ranking_grupos.txt",
    )
    p_ranking_grupos.set_defaults(func=cmd_ranking_grupos)

    p_fase = subparsers.add_parser(
        "fase",
        help="Pontuacao parcial detalhada por fase (Placar/Vencedor/Gols/Soma)",
    )
    p_fase.add_argument(
        "--fase",
        required=True,
        choices=sorted(FASES_BOLAO),
        help="grupos, 32avos, oitavas, quartas, semis ou finais",
    )
    p_fase.add_argument("--sem-arquivo", action="store_true")
    p_fase.add_argument("--sem-png", action="store_true")
    p_fase.set_defaults(func=cmd_fase)

    p_exportar = subparsers.add_parser("exportar", help="Exporta classificação para CSV")
    p_exportar.set_defaults(func=cmd_exportar)

    p_compartilhar = subparsers.add_parser(
        "compartilhar", help="Gera tabela em texto para enviar no grupo"
    )
    p_compartilhar.add_argument(
        "--sem-arquivo",
        action="store_true",
        help="Nao salva classificacao_grupo.txt",
    )
    p_compartilhar.add_argument(
        "--sem-png",
        action="store_true",
        help="Nao gera classificacao_grupo.png",
    )
    p_compartilhar.add_argument(
        "--sem-snapshot",
        action="store_true",
        help="Obsoleto: o snapshot so atualiza com --confirmar-rodada",
    )
    p_compartilhar.add_argument(
        "--confirmar-rodada",
        action="store_true",
        help="Marca fim da rodada e salva baseline fixa para a proxima variacao",
    )
    p_compartilhar.add_argument(
        "--zerar-variacao",
        action="store_true",
        help="Mostra Rodada zerada e confirma a classificacao atual como baseline",
    )
    p_compartilhar.add_argument(
        "--jogo",
        type=int,
        nargs="+",
        metavar="ID",
        help="Inclui palpites provisorios na imagem completa (ex: --jogo 51 52)",
    )
    p_compartilhar.add_argument(
        "--ultimos",
        type=int,
        metavar="N",
        help="Usa os ultimos N jogos novos (ou com placar) na imagem completa (ex: --ultimos 2)",
    )
    p_compartilhar.add_argument(
        "--export",
        nargs="+",
        metavar="ITEM",
        help=(
            "Exports: geral, premio_a, fase_32avos, fase_grupos_32avos, "
            "rodada, txt, completo (padrao: tudo)"
        ),
    )
    p_compartilhar.set_defaults(func=cmd_compartilhar)

    p_confirmar = subparsers.add_parser(
        "confirmar-rodada",
        help="Salva baseline da coluna Rod (sem gerar exports)",
    )
    p_confirmar.set_defaults(func=cmd_confirmar_rodada)

    p_baseline = subparsers.add_parser(
        "baseline",
        help="Salva classificacao atual como referencia da coluna Rodada",
    )
    p_baseline.set_defaults(func=cmd_baseline)

    p_proximos = subparsers.add_parser("proximos", help="Lista jogos sem resultado")
    p_proximos.add_argument(
        "--limite",
        type=int,
        help="Quantos jogos mostrar (padrão: todos os pendentes)",
    )
    p_proximos.set_defaults(func=cmd_proximos)

    p_palpites = subparsers.add_parser("palpites", help="Lista palpites de um ou mais jogos")
    p_palpites.add_argument(
        "--jogo",
        type=int,
        nargs="+",
        required=True,
        metavar="ID",
        help="ID(s) do(s) jogo(s), ex: --jogo 51 52",
    )
    p_palpites.add_argument("--sem-arquivo", action="store_true")
    p_palpites.add_argument("--sem-png", action="store_true")
    p_palpites.add_argument(
        "--provisorio",
        action="store_true",
        help="Mostra quesito e vencedor com base no placar provisorio (requer resultado lancado)",
    )
    p_palpites.set_defaults(func=cmd_palpites)

    p_conferir = subparsers.add_parser("conferir", help="Compara com classificação de referência")
    p_conferir.set_defaults(func=cmd_conferir)

    p_reset = subparsers.add_parser(
        "reset",
        help="Reinicia o bolão com uma planilha nova (zera resultados e snapshot)",
    )
    p_reset.add_argument(
        "--arquivo",
        help="CSV da fase de grupos (padrão: mais recente em data/)",
    )
    p_reset.add_argument(
        "--com-resultados",
        action="store_true",
        help="Importa placares das linhas PLACAR da planilha para resultados.csv",
    )
    p_reset.add_argument(
        "--sem-baseline",
        action="store_true",
        help="Nao gera snapshot nem PNG inicial",
    )
    p_reset.set_defaults(func=cmd_reset)

    p_importar_resultados = subparsers.add_parser(
        "importar-resultados",
        help="Importa placares das linhas PLACAR do CSV da planilha",
    )
    p_importar_resultados.add_argument(
        "--arquivo",
        help="CSV da fase de grupos (padrao: data/bolao.csv)",
    )
    p_importar_resultados.add_argument(
        "--sem-baseline",
        action="store_true",
        help="Nao atualiza snapshot nem PNG",
    )
    p_importar_resultados.add_argument(
        "--conferir",
        action="store_true",
        help="Compara com classificacao_referencia.csv apos importar",
    )
    p_importar_resultados.set_defaults(func=cmd_importar_resultados)

    p_importar_referencia = subparsers.add_parser(
        "importar-referencia",
        help="Importa a classificacao do Excel como tabela ativa do programa",
    )
    p_importar_referencia.add_argument(
        "--arquivo",
        required=True,
        help="CSV da aba CLASSIFICACAO PROVISORIA exportado do Excel",
    )
    p_importar_referencia.set_defaults(func=cmd_importar_referencia)

    p_bandeiras = subparsers.add_parser(
        "bandeiras", help="Baixa imagens reais das bandeiras para cache local"
    )
    p_bandeiras.add_argument(
        "--forcar",
        action="store_true",
        help="Baixa de novo mesmo se ja existir em data/flags/",
    )
    p_bandeiras.set_defaults(func=cmd_bandeiras)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
