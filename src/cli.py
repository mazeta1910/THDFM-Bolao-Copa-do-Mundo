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
    calcular_variacoes_da_rodada,
    calcular_variacoes_jogos,
    carregar_classificacao_referencia,
    comparar_classificacoes,
    exportar_classificacao,
    exportar_classificacao_texto,
    formatar_classificacao_compartilhar,
    gerar_classificacao,
    jogos_recem_realizados,
    resumir_jogos_export,
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
    nome_arquivo_palpites,
    nome_arquivo_rodada,
)
from src.thdfm_parser import parse_thdfm_csv

try:
    from src.image_export import (
        exportar_classificacao_png,
        exportar_palpites_png,
        exportar_palpites_provisorios_png,
        exportar_rodada_completa_png,
    )

    _PNG_DISPONIVEL = True
except ImportError:
    _PNG_DISPONIVEL = False

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADS = Path.home() / "Downloads"
BOLAO_CSV = DATA_DIR / "bolao.csv"
RESULTADOS_CSV = DATA_DIR / "resultados.csv"
CLASSIFICACAO_CSV = DATA_DIR / "classificacao.csv"
CLASSIFICACAO_TXT = DATA_DIR / "classificacao_grupo.txt"
CLASSIFICACAO_PNG = DATA_DIR / "classificacao_grupo.png"
SNAPSHOT_JSON = DATA_DIR / "classificacao_snapshot.json"
REFERENCIA_CSV = DATA_DIR / "classificacao_referencia.csv"

_ARQUIVOS_IGNORADOS = {
    "resultados.csv",
    "classificacao.csv",
    "classificacao_referencia.csv",
    "classificacao_grupo.txt",
    "classificacao_snapshot.json",
}


def _resolve_arquivo(path: Path, fallback_name: str) -> Path:
    if path.exists():
        return path
    fallback = DOWNLOADS / fallback_name
    return fallback if fallback.exists() else path


def _resolver_bolao_csv() -> Path:
    if BOLAO_CSV.exists():
        return BOLAO_CSV

    candidatos = [
        path
        for path in sorted(DATA_DIR.glob("*.csv"), key=lambda item: item.stat().st_mtime, reverse=True)
        if path.name.lower() not in _ARQUIVOS_IGNORADOS
        and "fase de grupos" in path.name.lower()
    ]
    if candidatos:
        return candidatos[0]

    return _resolve_arquivo(BOLAO_CSV, "BOLÃO THDFM WC26 - Fase de grupos.csv")


def carregar_bolao(arquivo: Path | None = None):
    path = arquivo or _resolver_bolao_csv()
    if not path.exists():
        raise FileNotFoundError(f"Arquivo do bolão não encontrado: {path}")

    bolao = parse_thdfm_csv(path)
    aplicar_resultados_externos(bolao, RESULTADOS_CSV)
    return bolao


def _carregar_baseline_variacao() -> tuple[dict[str, dict] | None, set[int], bool]:
    snapshot = carregar_snapshot(SNAPSHOT_JSON)
    if snapshot is not None:
        return (
            snapshot.get("participantes"),
            set(snapshot.get("jogos_ids", [])),
            True,
        )

    referencia_path = _resolve_arquivo(
        REFERENCIA_CSV, "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv"
    )
    if referencia_path.exists():
        referencia = carregar_classificacao_referencia(referencia_path)
        return snapshot_de_classificacao(referencia), set(), False

    return None, set(), False


def _classificacao_programa(bolao) -> list:
    """Total de pontos calculado dos palpites e resultados lancados."""
    return gerar_classificacao(bolao)


def _atualizar_exports_classificacao(bolao) -> None:
    classificacao = _classificacao_programa(bolao)
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    variacoes = calcular_variacoes(classificacao, None)
    mudancas_posicao = calcular_mudancas_posicao(classificacao, None)
    exportar_classificacao(classificacao, CLASSIFICACAO_CSV)
    exportar_classificacao_texto(
        classificacao,
        CLASSIFICACAO_TXT,
        jogos_realizados=realizados,
        total_jogos=len(bolao.jogos),
        variacoes=variacoes,
        mudancas_posicao=mudancas_posicao,
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


def _salvar_baseline(bolao, *, mensagem_snapshot: bool = True) -> None:
    classificacao = _classificacao_programa(bolao)
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
    shutil.copy2(origem, REFERENCIA_CSV)
    classificacao = carregar_classificacao_referencia(REFERENCIA_CSV)
    print(
        f"Classificação importada: {len(classificacao)} participantes em {REFERENCIA_CSV.name}"
    )
    print("Essa tabela passa a ser usada pelo programa (classificar, compartilhar e PNG).")

    bolao = carregar_bolao()
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    jogos_ids = [jogo.id for jogo in bolao.jogos if j.realizado]
    salvar_snapshot(
        SNAPSHOT_JSON,
        classificacao,
        jogos_realizados=realizados,
        jogos_ids=jogos_ids,
    )
    print(f"Baseline salva em {SNAPSHOT_JSON.name} ({realizados} jogos).")

    _atualizar_exports_classificacao(bolao)
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
                    atualizar_resultado(bolao, jogo.id, casa, fora)
                    print(f"  Registrado: {casa}-{fora}")
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
        jogo = atualizar_resultado(bolao, args.jogo[0], casa, fora)
        print(f"Jogo {jogo.id} ({jogo.casa} x {jogo.fora}): {casa}-{fora}")

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


def cmd_classificar(args: argparse.Namespace) -> int:
    bolao = carregar_bolao()
    classificacao = _classificacao_programa(bolao)
    _imprimir_classificacao(classificacao)
    return 0


def cmd_exportar(args: argparse.Namespace) -> int:
    bolao = carregar_bolao()
    classificacao = _classificacao_programa(bolao)
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


def cmd_compartilhar(args: argparse.Namespace) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    bolao = carregar_bolao()
    classificacao = _classificacao_programa(bolao)
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
    legenda_rodada = None
    if jogo_ids_export:
        variacoes = calcular_variacoes_jogos(bolao, set(jogo_ids_export))
        jogos_novos = resumir_jogos_export(bolao, jogo_ids_export)
        ids_txt = ", ".join(str(jogo_id) for jogo_id in jogo_ids_export)
        legenda_rodada = f"Rod = pontos nos jogos {ids_txt} desta imagem"

    texto = formatar_classificacao_compartilhar(
        classificacao,
        jogos_realizados=realizados,
        total_jogos=len(bolao.jogos),
        variacoes=variacoes,
        mudancas_posicao=mudancas_posicao,
        jogos_novos=jogos_novos or None,
        legenda_rodada=legenda_rodada,
    )
    print(texto)

    if not args.sem_arquivo:
        exportar_classificacao_texto(
            classificacao,
            CLASSIFICACAO_TXT,
            jogos_realizados=realizados,
            total_jogos=len(bolao.jogos),
            variacoes=variacoes,
            mudancas_posicao=mudancas_posicao,
            jogos_novos=jogos_novos or None,
            legenda_rodada=legenda_rodada,
        )
        print(f"\nTexto salvo em {CLASSIFICACAO_TXT}")

    if not args.sem_png:
        if not _PNG_DISPONIVEL:
            print(
                "PNG nao gerado: instale Pillow com 'pip install pillow' e rode de novo.",
                file=sys.stderr,
            )
        else:
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

    jogo_ids = getattr(args, "jogo", None)
    if jogo_ids and not args.sem_png:
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
            rodada_path = DATA_DIR / nome_arquivo_rodada(jogo_ids)
            exportar_rodada_completa_png(
                classificacao,
                blocos,
                rodada_path,
                jogos_realizados=realizados,
                total_jogos=len(bolao.jogos),
                variacoes=variacoes,
                mudancas_posicao=mudancas_posicao,
                jogos_novos=jogos_novos or None,
            )
            print(f"Imagem completa salva em {rodada_path}")

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
        txt_path = DATA_DIR / nome_arquivo_palpites(args.jogo, "txt", provisorio=args.provisorio)
        txt_path.write_text(texto + "\n", encoding="utf-8")
        print(f"\nTexto salvo em {txt_path}")

    if not args.sem_png:
        if not _PNG_DISPONIVEL:
            print(
                "PNG nao gerado: instale Pillow com 'pip install pillow' e rode de novo.",
                file=sys.stderr,
            )
        else:
            png_path = DATA_DIR / nome_arquivo_palpites(args.jogo, "png", provisorio=args.provisorio)
            if args.provisorio:
                exportar_palpites_provisorios_png(blocos, png_path)
            else:
                exportar_palpites_png(blocos, png_path)
            print(f"Imagem salva em {png_path}")

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
    referencia_path = _resolve_arquivo(
        REFERENCIA_CSV, "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv"
    )
    if not referencia_path.exists():
        print(f"Arquivo de referência não encontrado: {referencia_path}")
        return 1

    bolao = carregar_bolao()
    calculada = gerar_classificacao(bolao)
    referencia = carregar_classificacao_referencia(referencia_path)
    diferencas = comparar_classificacoes(calculada, referencia)

    if not diferencas:
        print("Classificação confere com a referência.")
        return 0

    print("Diferenças encontradas:")
    for diff in diferencas:
        print(f"  - {diff}")
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
        "--remover",
        action="store_true",
        help="Remove o placar dos jogos informados em --jogo",
    )
    p_resultado.add_argument("--interativo", action="store_true")
    p_resultado.set_defaults(func=cmd_resultado)

    p_classificar = subparsers.add_parser("classificar", help="Exibe classificação")
    p_classificar.set_defaults(func=cmd_classificar)

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
    p_compartilhar.set_defaults(func=cmd_compartilhar)

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
