from __future__ import annotations

import argparse
import sys


def _configurar_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")


def _pausar() -> None:
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


def _ler_jogos(
    mensagem: str = "IDs dos jogos (ex: 51 52): ",
    *,
    opcional: bool = False,
) -> list[int] | None:
    texto = _ler_linha(mensagem)
    if texto is None:
        return None
    if not texto:
        if opcional:
            return []
        print("Nenhum jogo informado.")
        return None
    try:
        return [int(parte) for parte in texto.split()]
    except ValueError:
        print("Use numeros separados por espaco, ex: 51 52")
        return None


def _namespace(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _carregar_bolao():
    from src.cli import carregar_bolao

    return carregar_bolao()


def _formatar_jogo(jogo) -> str:
    return f"Jogo {jogo.id}: {jogo.casa} x {jogo.fora}  ({jogo.data})"


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
        print(
            f"  Jogo {jogo.id}: {jogo.casa} x {jogo.fora}  "
            f"-> {jogo.gols_casa}x{jogo.gols_fora}  ({jogo.data})"
        )


def _imprimir_contexto_jogos(
    *,
    pendentes: bool = False,
    com_placar: bool = False,
    limite_pendentes: int = 8,
    limite_com_placar: int = 2,
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


def _imprimir_cabecalho() -> None:
    print()
    print("=" * 44)
    print("  BOLAO THDFM - COPA DO MUNDO 2026")
    print("=" * 44)
    print()
    print("Dia a dia")
    print("  1. Compartilhar classificacao (+ provisorio opcional)")
    print("  2. Confirmar rodada (fim dos jogos oficiais)")
    print("  3. Lancar placar de um jogo")
    print("  4. Lancar placares (modo interativo)")
    print("  5. Remover placar de jogo(s)")
    print("  6. Ver proximos jogos")
    print()
    print("Palpites")
    print("  7. Palpites de jogos (imagem simples)")
    print("  8. Palpites provisorios (quesito + vencedor)")
    print()
    print("Outros")
    print("  9. Classificacao no terminal")
    print(" 10. Salvar baseline pre-rodada")
    print(" 11. Validar bolao")
    print(" 12. Conferir com referencia do Excel")
    print()
    print("  0. Sair")


def executar_menu() -> int:
    from src.cli import (
        cmd_baseline,
        cmd_classificar,
        cmd_compartilhar,
        cmd_conferir,
        cmd_palpites,
        cmd_proximos,
        cmd_resultado,
        cmd_validar,
    )

    _configurar_stdio()

    while True:
        _imprimir_cabecalho()
        escolha = _ler_linha("Opcao: ")
        if escolha is None:
            return 0

        escolha = escolha.lower()
        if escolha in {"0", "s", "sair", "q"}:
            return 0

        try:
            if escolha == "1":
                _imprimir_contexto_jogos(com_placar=True, limite_com_placar=4)
                jogos = _ler_jogos(
                    "Jogos provisorios na imagem completa (Enter = so classificacao): ",
                    opcional=True,
                )
                if jogos is None:
                    _pausar()
                    continue
                cmd_compartilhar(
                    _namespace(
                        sem_arquivo=False,
                        sem_png=False,
                        sem_snapshot=False,
                        confirmar_rodada=False,
                        zerar_variacao=False,
                        jogo=jogos,
                    )
                )
            elif escolha == "2":
                cmd_compartilhar(
                    _namespace(
                        sem_arquivo=False,
                        sem_png=False,
                        sem_snapshot=False,
                        confirmar_rodada=True,
                        zerar_variacao=False,
                    )
                )
            elif escolha == "3":
                _imprimir_contexto_jogos(pendentes=True)
                jogo_texto = _ler_linha("ID do jogo: ")
                if not jogo_texto:
                    continue
                placar = _ler_linha("Placar (ex: 2-1): ")
                if not placar:
                    continue
                cmd_resultado(
                    _namespace(
                        jogo=[int(jogo_texto)],
                        placar=placar,
                        remover=False,
                        interativo=False,
                    )
                )
            elif escolha == "4":
                _imprimir_contexto_jogos(pendentes=True)
                cmd_resultado(
                    _namespace(jogo=None, placar=None, remover=False, interativo=True)
                )
            elif escolha == "5":
                _imprimir_contexto_jogos(com_placar=True)
                jogos = _ler_jogos("IDs dos jogos para remover (ex: 51 52): ")
                if not jogos:
                    _pausar()
                    continue
                cmd_resultado(_namespace(jogo=jogos, placar=None, remover=True, interativo=False))
            elif escolha == "6":
                cmd_proximos(_namespace(limite=None))
            elif escolha == "7":
                _imprimir_contexto_jogos(
                    pendentes=True,
                    com_placar=True,
                    mostrar_ultimos_com_placar=False,
                )
                jogos = _ler_jogos()
                if not jogos:
                    _pausar()
                    continue
                cmd_palpites(
                    _namespace(
                        jogo=jogos,
                        sem_arquivo=False,
                        sem_png=False,
                        provisorio=False,
                    )
                )
            elif escolha == "8":
                _imprimir_contexto_jogos(com_placar=True)
                jogos = _ler_jogos()
                if not jogos:
                    _pausar()
                    continue
                cmd_palpites(
                    _namespace(
                        jogo=jogos,
                        sem_arquivo=False,
                        sem_png=False,
                        provisorio=True,
                    )
                )
            elif escolha == "9":
                cmd_classificar(_namespace())
            elif escolha == "10":
                cmd_baseline(_namespace())
            elif escolha == "11":
                cmd_validar(_namespace())
            elif escolha == "12":
                cmd_conferir(_namespace())
            else:
                print("Opcao invalida.")
        except ValueError as exc:
            print(f"Erro: {exc}")
        except FileNotFoundError as exc:
            print(exc)

        _pausar()
