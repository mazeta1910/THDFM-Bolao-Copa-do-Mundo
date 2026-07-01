from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from src.exports_manager import ultimo_dir
from src.ranking import FASES_BOLAO, sugerir_jogos_provisorios
from src.scoring import fase_jogo
from src.share_options import (
    SelecaoCompartilhar,
    ajustar_selecao_disponivel,
    caminho_menu_export,
    descrever_exports,
    disponibilidade_compartilhar,
    selecao_completa,
    selecao_geral_parcial,
    selecao_geral_parcial_palpites,
    selecao_geral_premio_a,
    selecao_rodada_whatsapp,
    selecao_so_geral,
    selecao_so_parcial,
)

_FASES_MENU = (
    ("grupos", "Fase de grupos (J1-J72)"),
    ("32avos", "32 avos (J73-J88)"),
    ("grupos_mais_32avos", "Grupos + 32 avos"),
    ("oitavas", "Oitavas"),
    ("quartas", "Quartas"),
    ("semis", "Semifinais"),
    ("finais", "Finais"),
)

_LABEL_FASE = {
    "grupos": "Fase de grupos",
    "16avos": "32 avos",
    "oitavas": "Oitavas",
    "quartas": "Quartas",
    "semis": "Semifinais",
    "finais": "Finais",
}


def _configurar_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")


def _pausar(*, curto: bool = False) -> None:
    if curto:
        return
    try:
        input("\nEnter para voltar ao menu...")
    except (EOFError, KeyboardInterrupt):
        print()


def _ler_linha(mensagem: str) -> str | None:
    try:
        return input(mensagem).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


_CANCELAMENTO_EXPLICITO = frozenset({"sair", "cancelar", "q", "quit"})


def _entrada_abortada(texto: str | None) -> bool:
    """Enter vazio nao aborta; use em menus numericos e IDs."""
    if texto is None:
        return True
    return texto.lower() in _CANCELAMENTO_EXPLICITO


def _entrada_cancelada(texto: str | None) -> bool:
    """Enter vazio ou '0' cancela; use quando cancelar e a intencao do Enter."""
    if texto is None:
        return True
    return texto.lower() in {"", "0", *_CANCELAMENTO_EXPLICITO}


def _confirmar(mensagem: str, *, padrao: bool = True) -> bool | None:
    """True=sim, False=nao, None=abortou (Ctrl+C / sair)."""
    sufixo = "[S/n]" if padrao else "[s/N]"
    texto = _ler_linha(f"{mensagem} {sufixo}: ")
    if texto is None:
        return None
    normalizado = texto.lower()
    if normalizado in _CANCELAMENTO_EXPLICITO:
        return None
    if not normalizado:
        return padrao
    if normalizado in {"n", "nao", "no"}:
        return False
    if normalizado in {"s", "sim", "y", "yes"}:
        return True
    print("  Responda s (sim) ou n (nao).")
    return _confirmar(mensagem, padrao=padrao)


def _ler_opcao_numerica(
    mensagem: str,
    *,
    padrao: str = "1",
    cancelar: str = "0",
) -> str | None:
    texto = _ler_linha(mensagem)
    if texto is None:
        return None
    if not texto:
        return padrao
    if texto == cancelar:
        return None
    return texto


def _namespace(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _carregar_bolao():
    from src.cli import carregar_bolao

    return carregar_bolao()


def _data_dir() -> Path:
    from src.cli import DATA_DIR

    return DATA_DIR


def _buscar_jogo(bolao, jogo_id: int):
    return next((jogo for jogo in bolao.jogos if jogo.id == jogo_id), None)


def _formatar_jogo(jogo) -> str:
    return f"Jogo {jogo.id}: {jogo.casa} x {jogo.fora}  ({jogo.data})"


def _ler_jogo_para_placar() -> tuple[int, object] | None:
    bolao = _carregar_bolao()
    while True:
        jogo_texto = _ler_linha("ID do jogo (sair cancela): ")
        if _entrada_abortada(jogo_texto):
            return None
        try:
            jogo_id = int(jogo_texto)
        except ValueError:
            print("Use o numero do jogo, ex: 50")
            continue

        jogo = _buscar_jogo(bolao, jogo_id)
        if jogo is None:
            print(f"Jogo {jogo_id} nao encontrado.")
            continue
        return jogo_id, jogo


def _ler_placar_jogo(jogo) -> str | None:
    from src.scoring import FASE_GRUPOS_MAX

    if jogo.realizado:
        placar = f"{jogo.gols_casa}x{jogo.gols_fora}"
        if jogo.vencedor_penaltis:
            placar += f" (penaltis: {jogo.vencedor_penaltis})"
        print(f"  Placar atual: {placar} (sera substituido se informar outro)")
    dica = ""
    if jogo.id > FASE_GRUPOS_MAX:
        dica = " [empate: Enter=parcial | time=penaltis]"
    return _ler_linha(
        f"Placar Jogo {jogo.id} ({jogo.casa} x {jogo.fora}){dica} "
        f"[Enter/sair cancela]: "
    )


def _ler_jogos(
    mensagem: str = "IDs dos jogos (ex: 73 74): ",
    *,
    opcional: bool = False,
    padrao: list[int] | None = None,
) -> list[int] | None:
    texto = _ler_linha(mensagem)
    if texto is None:
        return None
    if not texto:
        if padrao is not None:
            if padrao:
                print(f"  -> jogos {', '.join(str(jogo_id) for jogo_id in padrao)}")
            return list(padrao)
        if opcional:
            return []
        print("Nenhum jogo informado.")
        return None
    if texto.lower() in {"-", "0", "nenhum", "nao", "n"}:
        return []
    try:
        return [int(parte) for parte in texto.split()]
    except ValueError:
        print("Use numeros separados por espaco, ex: 73 74")
        return None


def _imprimir_ultimos_com_placar(bolao, *, limite: int = 2, titulo: str | None = None) -> None:
    com_placar_lista = [jogo for jogo in bolao.jogos if jogo.realizado]
    if not com_placar_lista:
        print("Com placar: nenhum jogo lancado ainda.")
        return

    if titulo is None:
        titulo = (
            f"Ultimos com placar ({min(limite, len(com_placar_lista))} de {len(com_placar_lista)})"
        )
    print(titulo + ":")
    for jogo in com_placar_lista[-limite:]:
        placar = f"{jogo.gols_casa}x{jogo.gols_fora}"
        if jogo.vencedor_penaltis:
            placar += f" (pen. {jogo.vencedor_penaltis})"
        print(
            f"  Jogo {jogo.id}: {jogo.casa} x {jogo.fora}  "
            f"-> {placar}  ({jogo.data})"
        )


def _imprimir_contexto_jogos(
    *,
    pendentes: bool = False,
    com_placar: bool = False,
    limite_pendentes: int = 8,
    limite_com_placar: int = 6,
    mostrar_ultimos_com_placar: bool = True,
) -> None:
    bolao = _carregar_bolao()
    realizados_total = sum(1 for jogo in bolao.jogos if jogo.realizado)
    print(f"\nResultados registrados: {realizados_total}/{len(bolao.jogos)} jogos")

    if pendentes:
        pendentes_lista = [jogo for jogo in bolao.jogos if not jogo.realizado]
        if pendentes_lista:
            print(f"Sem placar ({len(pendentes_lista)} no total):")
            for jogo in pendentes_lista[:limite_pendentes]:
                print(f"  {_formatar_jogo(jogo)}")
            if len(pendentes_lista) > limite_pendentes:
                print(f"  ... e mais {len(pendentes_lista) - limite_pendentes} jogos")
        else:
            print("Sem placar: nenhum jogo pendente.")

        if mostrar_ultimos_com_placar and not com_placar:
            print()
            _imprimir_ultimos_com_placar(
                bolao,
                limite=limite_com_placar,
                titulo="Ultimos com placar (para alterar)",
            )

    if com_placar:
        if pendentes:
            print()
        _imprimir_ultimos_com_placar(
            bolao,
            limite=limite_com_placar,
            titulo=f"Com placar ({realizados_total} no total)",
        )

    print()


def _fase_atual_bolao(bolao) -> str:
    pendentes = [jogo for jogo in bolao.jogos if not jogo.realizado]
    referencia = pendentes[0].id if pendentes else bolao.jogos[-1].id
    return _LABEL_FASE.get(fase_jogo(referencia), fase_jogo(referencia))


def _ultimo_export_resumo() -> str:
    pasta = ultimo_dir(_data_dir())
    manifest = pasta / "manifest.txt"
    if not manifest.exists():
        return "nenhum export ainda"

    arquivos = [path for path in pasta.iterdir() if path.is_file() and path.name != "manifest.txt"]
    if not arquivos:
        return "pasta vazia"

    recente = max(arquivos, key=lambda path: path.stat().st_mtime)
    quando = datetime.fromtimestamp(recente.stat().st_mtime).strftime("%d/%m %H:%M")
    return f"{recente.name} ({quando})"


def _imprimir_status() -> None:
    from src.cli import _classificacao_jogos, _classificacao_premio_a

    bolao = _carregar_bolao()
    classificacao = _classificacao_jogos(bolao)
    premio_a, _ = _classificacao_premio_a(bolao)
    realizados = sum(1 for jogo in bolao.jogos if jogo.realizado)
    lider_b = classificacao[0] if classificacao else None
    lider_a = premio_a[0] if premio_a else None

    print()
    print("-" * 52)
    linha_status = (
        f"  {realizados}/{len(bolao.jogos)} jogos  |  "
        f"Fase: {_fase_atual_bolao(bolao)}"
    )
    if lider_b:
        linha_status += f"  |  Lider B: {lider_b.participante.strip()} ({lider_b.soma})"
    print(linha_status)
    if lider_a:
        print(f"  Lider A: {lider_a.participante.strip()} ({lider_a.soma} pts)")
    print(f"  Ultimo export: {_ultimo_export_resumo()}")
    print(f"  Pasta: {ultimo_dir(_data_dir())}")
    print("-" * 52)


def _imprimir_cabecalho() -> None:
    print()
    print("=" * 52)
    print("  BOLAO THDFM - COPA DO MUNDO 2026")
    print("=" * 52)
    _imprimir_status()
    print()
    print(" 1. Rodada de hoje (placares + compartilhar)")
    print(" 2. Compartilhar (escolher tabelas)")
    print(" 3. Placares")
    print(" 4. Palpites")
    print(" 5. Tabelas e rankings")
    print(" 6. Ferramentas")
    print()
    print("Atalhos: r=rodada  c=compartilhar  s=status  u=pasta ultimo")
    print("  0. Sair")


def _normalizar_escolha(escolha: str) -> str:
    escolha = escolha.strip().lower()
    atalhos = {
        "r": "1",
        "rodada": "1",
        "c": "2",
        "compartilhar": "2",
        "s": "status",
        "status": "status",
        "u": "ultimo",
        "ultimo": "ultimo",
        "p": "3",
        "placares": "3",
        "t": "5",
        "tabelas": "5",
        "f": "6",
        "ferramentas": "6",
    }
    return atalhos.get(escolha, escolha)


def _disponibilidade_atual():
    from src.cli import _classificacao_premio_a, _tabelas_mata_mata

    bolao = _carregar_bolao()
    premio_a, _ = _classificacao_premio_a(bolao)
    c32, cg32 = _tabelas_mata_mata(bolao)
    return disponibilidade_compartilhar(
        tem_premio_a=bool(premio_a),
        classificacao_32avos=c32,
        classificacao_grupos_32avos=cg32,
    )


def _selecao_personalizada(disponivel) -> SelecaoCompartilhar:
    print("\nPersonalizado (s/n, Enter = sim onde aplicavel):")

    def _sn(mensagem: str, *, padrao: bool = True) -> bool:
        return _confirmar(mensagem, padrao=padrao)

    selecao = SelecaoCompartilhar(
        texto=_sn("Texto WhatsApp (classificacao.txt)?"),
        classificacao_png=_sn("PNG tabela geral (premio B)?"),
        premio_a_png=(
            _sn("PNG premio A?", padrao=True) if disponivel.tem_premio_a else False
        ),
        fase_32avos_png=(
            _sn("PNG pontuacao 32 avos?", padrao=True)
            if disponivel.tem_fase_32avos
            else False
        ),
        fase_grupos_32avos_png=(
            _sn("PNG grupos + 32 avos?", padrao=True)
            if disponivel.tem_fase_grupos_32avos
            else False
        ),
        rodada_png=_sn("PNG rodada com palpites provisorios?", padrao=False),
    )
    return ajustar_selecao_disponivel(selecao, disponivel)


def _breadcrumb(*partes: str) -> None:
    print("\n" + " > ".join(["Menu", *partes]))


def _nome_arquivo_export(item: str) -> str:
    return item.split(" — ", 1)[0].strip()


def _imprimir_dica_palpites_somente() -> None:
    print("\nQuer SOMENTE a tabela de palpites (sem ranking)?")
    print("  Menu > Palpites > 2. Exportar palpites provisorios")
    print("  (gera palpites_provisorios.png em data/ultimo/png/)")


def _imprimir_preview_exports(
    selecao: SelecaoCompartilhar,
    *,
    jogos_rodada: list[int] | None,
    disponivel,
    breadcrumb: tuple[str, ...] | None = None,
) -> None:
    itens = descrever_exports(
        selecao,
        jogos_rodada=jogos_rodada,
        disponivel=disponivel,
        legivel=True,
    )
    if breadcrumb:
        _breadcrumb(*breadcrumb)
    print("\nArquivos que serao gerados em data/ultimo/ (png/, txt/, csv/):")
    for item in itens:
        print(f"  • {item}")
    if itens:
        print("\nComo gerar cada um depois (pelo menu):")
        for item in itens:
            nome = _nome_arquivo_export(item)
            print(f"  • {nome}: {caminho_menu_export(nome)}")
    if selecao.rodada_png:
        print("\nrodada.png = ranking (esquerda) + palpites provisorios (direita) na mesma imagem.")
        _imprimir_dica_palpites_somente()


def _escolher_preset_compartilhar(
    disponivel,
    *,
    modo_rodada: bool = False,
) -> SelecaoCompartilhar | None:
    if modo_rodada:
        return None  # fluxo da rodada trata fora

    print("\nO que gerar?")
    _breadcrumb("Compartilhar")
    print(" 1. Tudo (ranking + grupos/cravadura + 32 avos, se houver)")
    print(" 2. Rodada ao vivo (ranking + 32 avos + imagem com palpites)")
    print(" 3. So ranking geral")
    print(" 4. Escolher arquivo por arquivo...")
    print(" 0. Cancelar")

    op = _ler_opcao_numerica("Escolha [1]: ", padrao="1")
    if op is None:
        return None

    mapa = {
        "1": selecao_completa(),
        "2": selecao_geral_parcial_palpites(),
        "3": selecao_so_geral(),
    }
    if op == "4":
        return _escolher_preset_compartilhar_completo(disponivel)
    if op not in mapa:
        print("Opcao invalida.")
        return None
    return ajustar_selecao_disponivel(mapa[op], disponivel)


def _escolher_preset_compartilhar_completo(disponivel) -> SelecaoCompartilhar | None:
    print("\nEscolha arquivo por arquivo:")
    print(" 1. Tudo")
    print(" 2. Ranking + 32 avos + palpites na imagem rodada")
    print(" 3. Ranking + 32 avos (sem imagem de palpites)")
    print(" 4. Ranking + tabela dos grupos")
    print(" 5. So ranking geral")
    print(" 6. So pontuacao dos 32 avos")
    print(" 7. Personalizado (marca um a um)")
    print(" 0. Voltar / cancelar")

    op = _ler_opcao_numerica("Escolha [1]: ", padrao="1")
    if op is None:
        return None

    presets = {
        "1": selecao_completa(),
        "2": selecao_geral_parcial_palpites(),
        "3": selecao_geral_parcial(),
        "4": selecao_geral_premio_a(),
        "5": selecao_so_geral(),
        "6": selecao_so_parcial(),
    }
    if op == "7":
        return _selecao_personalizada(disponivel)
    if op not in presets:
        print("Opcao invalida.")
        return None
    return ajustar_selecao_disponivel(presets[op], disponivel)


def _configurar_exports_rodada(disponivel) -> tuple[SelecaoCompartilhar | None, list[int] | None]:
    """Fluxo enxuto do passo 2 da rodada de hoje."""
    from src.cli import _carregar_baseline_variacao

    bolao = _carregar_bolao()
    _, baseline_ids, _ = _carregar_baseline_variacao()
    sugeridos = sugerir_jogos_provisorios(bolao, baseline_ids, limite=2)
    jogos: list[int] | None = list(sugeridos) if sugeridos else None

    _breadcrumb("Rodada de hoje", "Passo 2/2 — Divulgar no grupo")
    print("\nO que mandar no WhatsApp?")
    print(" 1. Ranking + palpites do jogo (recomendado)")
    print(" 2. So ranking geral")
    print(" 3. Mais arquivos (32 avos, premio A, etc.)")
    print(" 0. Cancelar")

    op = _ler_opcao_numerica("Escolha [1]: ", padrao="1")
    if op is None or op == "0":
        return None, None

    if op == "1":
        selecao = ajustar_selecao_disponivel(selecao_rodada_whatsapp(), disponivel)
        if sugeridos:
            sugestao = " ".join(str(jogo_id) for jogo_id in sugeridos)
            mensagem = (
                "\nQual jogo entra na imagem rodada.png? "
                f"[Enter = {sugestao} | - = sem palpites na imagem]: "
            )
        else:
            mensagem = "\nQual jogo entra na imagem rodada.png? (- = sem palpites): "
        escolhidos = _ler_jogos(mensagem, opcional=True, padrao=sugeridos or None)
        if escolhidos is None:
            return None, None
        if not escolhidos:
            selecao = replace(selecao, rodada_png=False)
            jogos = None
        else:
            jogos = escolhidos
    elif op == "2":
        selecao = ajustar_selecao_disponivel(selecao_so_geral(), disponivel)
        jogos = None
    elif op == "3":
        selecao = _escolher_preset_compartilhar_completo(disponivel)
        if selecao is None:
            return None, None
        if selecao.rodada_png and not jogos:
            if sugeridos:
                sugestao = " ".join(str(jogo_id) for jogo_id in sugeridos)
                mensagem = (
                    "\nQual jogo entra na imagem rodada.png? "
                    f"[Enter = {sugestao} | - = sem palpites]: "
                )
            else:
                mensagem = "\nQual jogo entra na imagem rodada.png? (- = sem palpites): "
            escolhidos = _ler_jogos(mensagem, opcional=True, padrao=sugeridos or None)
            if escolhidos is None:
                return None, None
            if not escolhidos:
                selecao = replace(selecao, rodada_png=False)
                jogos = None
            else:
                jogos = escolhidos
    else:
        print("Opcao invalida.")
        return None, None

    _imprimir_preview_exports(
        selecao,
        jogos_rodada=jogos,
        disponivel=disponivel,
        breadcrumb=("Rodada de hoje", "Passo 2/2 — Divulgar no grupo"),
    )
    return selecao, jogos


def _wizard_compartilhar(
    *,
    jogos_preset: list[int] | None = None,
    modo_rodada: bool = False,
) -> bool:
    from src.cli import _carregar_baseline_variacao, cmd_compartilhar

    disponivel = _disponibilidade_atual()
    jogos = list(jogos_preset) if jogos_preset else None

    if modo_rodada and jogos_preset is None:
        selecao, jogos = _configurar_exports_rodada(disponivel)
        if selecao is None:
            return False
    else:
        selecao = _escolher_preset_compartilhar(disponivel, modo_rodada=False)
        if selecao is None:
            return False

        if selecao.rodada_png and not jogos:
            bolao = _carregar_bolao()
            _, baseline_ids, _ = _carregar_baseline_variacao()
            sugeridos = sugerir_jogos_provisorios(bolao, baseline_ids, limite=2)
            if sugeridos:
                sugestao = " ".join(str(jogo_id) for jogo_id in sugeridos)
                mensagem = (
                    "\nJogo(s) na imagem com palpites "
                    f"[Enter = {sugestao} | - = sem imagem]: "
                )
            else:
                mensagem = "\nJogo(s) na imagem com palpites (- = sem imagem): "
            jogos = _ler_jogos(mensagem, opcional=True, padrao=sugeridos or None)
            if jogos is None:
                return False
            if not jogos:
                selecao = replace(selecao, rodada_png=False)

        _imprimir_preview_exports(
            selecao,
            jogos_rodada=jogos,
            disponivel=disponivel,
            breadcrumb=("Compartilhar",),
        )

    itens = descrever_exports(selecao, jogos_rodada=jogos, disponivel=disponivel)
    if not itens:
        print("Nenhum arquivo selecionado.")
        return False

    confirmacao = _confirmar("\nGerar agora?", padrao=True)
    if confirmacao is None:
        return False
    if not confirmacao:
        print("Exportacao nao realizada.")
        return False

    cmd_compartilhar(
        _namespace(
            sem_arquivo=False,
            sem_png=False,
            sem_snapshot=False,
            confirmar_rodada=False,
            zerar_variacao=False,
            jogo=jogos,
            selecao=selecao,
        )
    )
    return True


def _fluxo_rodada_hoje() -> None:
    from src.cli import cmd_confirmar_rodada, cmd_resultado

    _breadcrumb("Rodada de hoje")
    print("\nFluxo: placares (opcional) -> compartilhar -> confirmar rodada (opcional)")
    print("(Baseline pre-rodada: Menu > Ferramentas > 1)\n")
    _imprimir_contexto_jogos(pendentes=True, limite_pendentes=5)

    _breadcrumb("Rodada de hoje", "Passo 1/2 — Placares")
    print(" 1. Lancar placares agora (interativo)")
    print(" 2. Pular")
    passo = _ler_opcao_numerica("Escolha [2]: ", padrao="2")
    if passo is None:
        print("Fluxo encerrado.")
        return
    if passo == "1":
        print("Enter pula o jogo; 'sair' encerra sem perder o que ja foi lancado.\n")
        cmd_resultado(
            _namespace(
                jogo=None,
                placar=None,
                remover=False,
                interativo=True,
                penaltis=None,
                perguntar_penaltis=False,
                provisorio=False,
            )
        )

    _wizard_compartilhar(modo_rodada=True)

    print("\n--- Apos os jogos oficiais ---")
    confirmacao = _confirmar(
        "Confirmar rodada agora (zerar Rod na proxima divulgacao)?",
        padrao=False,
    )
    if confirmacao is None:
        return
    if confirmacao:
        cmd_confirmar_rodada(_namespace())


def _submenu_placares() -> None:
    from src.cli import cmd_proximos, cmd_resultado

    while True:
        print("\n--- Placares ---")
        print(" 1. Lancar placar de um jogo")
        print(" 2. Lancar placares (interativo)")
        print(" 3. Remover placar de jogo(s)")
        print(" 4. Ver proximos jogos")
        print(" 0. Voltar")

        escolha = _ler_linha("Opcao: ")
        if escolha is None or escolha == "0":
            return

        if escolha == "1":
            _imprimir_contexto_jogos(pendentes=True, limite_com_placar=6)
            entrada = _ler_jogo_para_placar()
            if entrada is None:
                print("Cancelado.")
                continue
            jogo_id, jogo = entrada
            print(f"  {_formatar_jogo(jogo)}")
            placar = _ler_placar_jogo(jogo)
            if placar is None or _entrada_abortada(placar):
                print("Cancelado.")
                continue
            cmd_resultado(
                _namespace(
                    jogo=[jogo_id],
                    placar=placar,
                    remover=False,
                    interativo=False,
                    penaltis=None,
                    perguntar_penaltis=True,
                    provisorio=False,
                )
            )
        elif escolha == "2":
            _imprimir_contexto_jogos(pendentes=True, limite_com_placar=6)
            print("Enter pula o jogo; 'sair' encerra.\n")
            cmd_resultado(
                _namespace(
                    jogo=None,
                    placar=None,
                    remover=False,
                    interativo=True,
                    penaltis=None,
                    perguntar_penaltis=False,
                    provisorio=False,
                )
            )
        elif escolha == "3":
            _imprimir_contexto_jogos(com_placar=True)
            jogos = _ler_jogos("IDs dos jogos para remover: ")
            if not jogos:
                continue
            cmd_resultado(
                _namespace(
                    jogo=jogos,
                    placar=None,
                    remover=True,
                    interativo=False,
                    penaltis=None,
                    perguntar_penaltis=False,
                    provisorio=False,
                )
            )
        elif escolha == "4":
            cmd_proximos(_namespace(limite=None))
        else:
            print("Opcao invalida.")
            continue

        _pausar()


def _submenu_palpites() -> None:
    from src.cli import cmd_palpites

    while True:
        _breadcrumb("Palpites")
        print("\n 1. Exportar palpites (imagem simples → palpites.png)")
        print(" 2. Exportar palpites provisorios (quesito + vencedor → palpites_provisorios.png)")
        print(" 0. Voltar")

        escolha = _ler_linha("Opcao: ")
        if escolha is None or escolha == "0":
            return

        if escolha not in {"1", "2"}:
            print("Opcao invalida.")
            continue

        _imprimir_contexto_jogos(
            pendentes=True,
            com_placar=True,
            mostrar_ultimos_com_placar=False,
        )
        jogos = _ler_jogos()
        if not jogos:
            continue

        cmd_palpites(
            _namespace(
                jogo=jogos,
                sem_arquivo=False,
                sem_png=False,
                provisorio=escolha == "2",
            )
        )
        _pausar()


def _ler_fase_menu() -> str | None:
    print("\nFase:")
    for indice, (fase_id, rotulo) in enumerate(_FASES_MENU, start=1):
        if fase_id not in FASES_BOLAO:
            continue
        print(f" {indice}. {rotulo}")
    print(" 0. Cancelar")

    escolha = _ler_linha("Opcao [2]: ")
    if _entrada_abortada(escolha):
        return None
    if not escolha:
        return "32avos"

    try:
        indice = int(escolha)
    except ValueError:
        if escolha in FASES_BOLAO:
            return escolha
        print("Opcao invalida.")
        return None

    if indice == 0:
        return None
    opcoes = [fase_id for fase_id, _ in _FASES_MENU if fase_id in FASES_BOLAO]
    if indice < 1 or indice > len(opcoes):
        print("Opcao invalida.")
        return None
    return opcoes[indice - 1]


def _submenu_tabelas() -> None:
    from src.cli import cmd_classificar, cmd_fase, cmd_ranking_grupos

    while True:
        print("\n--- Tabelas e rankings ---")
        print(" 1. Classificacao geral no terminal (premio B)")
        print(" 2. Pontuacao parcial por fase (detalhada)")
        print(" 3. Ranking parcial dos grupos (premio A)")
        print(" 4. Ver indice de exports (manifest.txt)")
        print(" 5. Abrir pasta data/ultimo/ (png, txt, csv)")
        print(" 0. Voltar")

        escolha = _ler_linha("Opcao: ")
        if escolha is None or escolha == "0":
            return

        if escolha == "1":
            cmd_classificar(_namespace())
        elif escolha == "2":
            fase = _ler_fase_menu()
            if fase:
                cmd_fase(_namespace(fase=fase, sem_arquivo=False, sem_png=False))
        elif escolha == "3":
            cmd_ranking_grupos(
                _namespace(reais=None, palpites=None, detalhe=False, sem_arquivo=False)
            )
        elif escolha == "4":
            _mostrar_manifest()
        elif escolha == "5":
            _abrir_pasta_ultimo()
        else:
            print("Opcao invalida.")
            continue

        _pausar()


def _mostrar_manifest() -> None:
    manifest = ultimo_dir(_data_dir()) / "manifest.txt"
    if not manifest.exists():
        print(f"Nenhum manifest em {manifest.parent}")
        return
    print()
    print(manifest.read_text(encoding="utf-8"))


def _abrir_pasta_ultimo() -> None:
    pasta = ultimo_dir(_data_dir())
    print(f"Abrindo {pasta}...")
    if sys.platform == "win32":
        os.startfile(pasta)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        os.system(f'open "{pasta}"')
    else:
        os.system(f'xdg-open "{pasta}"')


def _submenu_ferramentas() -> None:
    from src.cli import (
        cmd_baseline,
        cmd_conferir,
        cmd_importar_referencia,
        cmd_importar_resultados,
        cmd_reset,
        cmd_validar,
    )

    while True:
        print("\n--- Ferramentas ---")
        print(" 1. Salvar baseline pre-rodada")
        print(" 2. Confirmar rodada (zerar Rod)")
        print(" 3. Validar bolao")
        print(" 4. Conferir com referencia do Excel")
        print(" 5. Importar classificacao do Excel")
        print(" 6. Importar placares do bolao.csv")
        print(" 7. Atualizar palpites dos 32 avos")
        print(" 8. Reiniciar bolao (reset)")
        print(" 9. Baixar bandeiras")
        print(" 0. Voltar")

        escolha = _ler_linha("Opcao: ")
        if escolha is None or escolha == "0":
            return

        try:
            if escolha == "1":
                cmd_baseline(_namespace())
            elif escolha == "2":
                from src.cli import cmd_confirmar_rodada

                cmd_confirmar_rodada(_namespace())
            elif escolha == "3":
                cmd_validar(_namespace())
            elif escolha == "4":
                cmd_conferir(_namespace())
            elif escolha == "5":
                caminho = _ler_linha(
                    "Caminho do CSV (Enter = CLASSIFICACAO PROVISORIA (1).csv): "
                )
                if caminho is not None and _entrada_abortada(caminho):
                    print("Cancelado.")
                    continue
                if not caminho:
                    caminho = "data/fontes/BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv"
                cmd_importar_referencia(_namespace(arquivo=caminho))
            elif escolha == "6":
                cmd_importar_resultados(_namespace(arquivo=None, sem_baseline=False, conferir=False))
            elif escolha == "7":
                _importar_32_avos()
            elif escolha == "8":
                if _confirmar("Reiniciar bolao? Isso altera arquivos em data/.", padrao=False) is not True:
                    print("Cancelado.")
                    continue
                cmd_reset(_namespace(arquivo=None, com_resultados=False))
            elif escolha == "9":
                from src.cli import cmd_bandeiras

                cmd_bandeiras(_namespace(forcar=False))
            else:
                print("Opcao invalida.")
                continue
        except ValueError as exc:
            print(f"Erro: {exc}")
        except FileNotFoundError as exc:
            print(exc)

        _pausar()


def _importar_32_avos() -> None:
    from scripts.import_32avos import atualizar_palpites_32_avos

    print("Atualizando palpites J73-J88 a partir das respostas...")
    atualizar_palpites_32_avos()
    print("Concluido.")


def executar_menu() -> int:
    _configurar_stdio()

    while True:
        _imprimir_cabecalho()
        escolha = _ler_linha("Opcao: ")
        if escolha is None:
            return 0

        escolha = _normalizar_escolha(escolha)
        if escolha in {"0", "sair", "q"}:
            return 0

        try:
            if escolha == "status":
                _imprimir_status()
                _pausar(curto=True)
                continue
            if escolha == "ultimo":
                _mostrar_manifest()
                _pausar()
                continue
            if escolha == "1":
                _fluxo_rodada_hoje()
            elif escolha == "2":
                _wizard_compartilhar()
            elif escolha == "3":
                _submenu_placares()
                continue
            elif escolha == "4":
                _submenu_palpites()
                continue
            elif escolha == "5":
                _submenu_tabelas()
                continue
            elif escolha == "6":
                _submenu_ferramentas()
                continue
            else:
                print("Opcao invalida.")
                _pausar(curto=True)
                continue
        except ValueError as exc:
            print(f"Erro: {exc}")
        except FileNotFoundError as exc:
            print(exc)

        _pausar()
