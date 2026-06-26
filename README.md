# Bolão THDFM — Copa do Mundo 2026

Sistema em Python para **calcular a classificação**, **lançar resultados** e **gerar imagens** do bolão THDFM (fase de grupos). O programa replica as regras da planilha Excel: quesito (Placar / Gols casa / Gols fora / Nada), pontuação por coluna e critérios de desempate.

Destinado aos administradores que atualizam o bolão no dia a dia e compartilham a tabela no grupo (WhatsApp).

---

## Requisitos

| Item | Detalhe |
|------|---------|
| Python | 3.11 ou superior |
| Dependências | Biblioteca padrão (CSV, JSON, argparse) |
| Imagens PNG | `pip install pillow` (classificação, palpites, rodada completa) |
| Git | Recomendado para sincronizar placares entre computadores |

### Instalação rápida

```bash
git clone https://github.com/mazeta1910/THDFM-Bolao-Copa-do-Mundo.git
cd THDFM-Bolao-Copa-do-Mundo
pip install pillow
python scripts/setup_data.py
python scripts/download_bandeiras.py
```

O `setup_data.py` copia da pasta **Downloads** para `data/` (se ainda não existirem):

- `BOLÃO THDFM WC26 - Fase de grupos.csv` → `data/bolao.csv`
- `BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv` → `data/classificacao_referencia.csv`

---

## Como iniciar

```bash
python -m src.cli
```

Sem argumentos, abre o **menu interativo** (recomendado). Também funciona:

```bash
python -m src.cli menu
python -m src.cli compartilhar
python -m src.cli resultado --jogo 61 --placar 2-1
```

---

## Arquivos em `data/`

| Arquivo | Quem atualiza | Função |
|---------|---------------|--------|
| `bolao.csv` | Admin (export do Excel) | Palpites de todos + estrutura dos 72 jogos. Fonte dos nomes e placares da aba *Fase de grupos*. |
| `resultados.csv` | **Programa** (opções 3–5 do menu) | Placares lançados pela CLI. **Versionado no Git** para sincronizar entre PCs. |
| `classificacao_snapshot.json` | Programa (opção 2 ou 10) | Baseline da coluna **Rod**: pontos e jogos já “fechados” na última rodada confirmada. **Versionado no Git**. |
| `classificacao_referencia.csv` | Excel (opcional) | Classificação exportada do Excel para **conferência** (`conferir`). |
| `classificacao.csv` | Programa (`exportar` / compartilhar) | CSV completo com Placar, Vencedor, Gols casa, Gols fora e Soma. |
| `classificacao_grupo.txt` | Programa | Texto curto (Pos, Pts, Rod) para colar no grupo. |
| `classificacao_grupo.png` | Programa | Imagem da classificação com **todas as colunas de pontuação** + Pts + Rod. |
| `rodada_jXX_YY.png` | Programa | Classificação + palpites provisórios dos jogos informados. |
| `palpites_jXX.png` | Programa | Só palpites de um ou mais jogos. |
| `flags/` | `python -m src.cli bandeiras` | Bandeiras usadas nos PNGs de palpites. |

### Sincronizar entre administradores (Git)

Depois de lançar jogos ou confirmar rodada em um PC:

```bash
git add data/resultados.csv data/classificacao_snapshot.json
git commit -m "Atualiza placares apos jogos XX-YY"
git push
```

No outro PC:

```bash
git pull
python -m src.cli compartilhar
```

**Importante:** sempre faça `git pull` antes de lançar placares, para não sobrescrever o trabalho de outro admin.

---

## Regras de pontuação

Igual à planilha Excel:

| Acerto | Pontos | Coluna na tabela |
|--------|--------|------------------|
| Placar exato | **5** (3 + 2 vencedor) | Placar + Vencedor |
| Só o vencedor (ou empate) | **2** | Vencedor |
| Gols da casa corretos (sem placar exato) | **1** | Gols casa |
| Gols de fora corretos (sem placar exato) | **1** | Gols fora |

- Vencedor e gols parciais **somam** no mesmo jogo (máximo 4 pts sem placar exato).
- **Desempate:** soma → placar → vencedor → gols casa → gols fora (maior vence).

O programa classifica cada palpite nas categorias **Placar**, **Gols Casa**, **Gols fora** ou **Nada**, e verifica se acertou o vencedor — igual às colunas F e G do Excel.

---

## Menu interativo (opções)

```
Dia a dia
  1. Compartilhar classificacao (+ provisorio opcional)
  2. Confirmar rodada (fim dos jogos oficiais)
  3. Lancar placar de um jogo
  4. Lancar placares (modo interativo)
  5. Remover placar de jogo(s)
  6. Ver proximos jogos

Palpites
  7. Palpites de jogos (imagem simples)
  8. Palpites provisorios (quesito + vencedor)

Outros
  9. Classificacao no terminal
 10. Salvar baseline pre-rodada
 11. Validar bolao
 12. Conferir com referencia do Excel
 13. Importar classificacao do Excel
```

### Opção 1 — Compartilhar

Gera `classificacao_grupo.txt`, `classificacao_grupo.png` e mostra a tabela no terminal.

- O **PNG** traz: Pos, Participante, **Placar, Venc., G.casa, G.fora**, **Pts** e **Rod**.
- O **texto** traz versão resumida (Pos, Pts, Rod) para WhatsApp.
- Se informar IDs de jogos (ex.: `57 58`), gera também `rodada_j57_58.png`: classificação ao lado dos palpites provisórios desses jogos.
- A coluna **Rod** mostra quantos pontos cada um ganhou **desde a última baseline** (snapshot). Setas ↑↓ na posição indicam subida ou queda no ranking.

### Opção 2 — Confirmar rodada

Use **ao final do dia**, quando todos os placares oficiais estiverem corretos. Atualiza `classificacao_snapshot.json` e zera a **Rod** na próxima divulgação (todos começam com Rod = 0 até novos jogos).

### Opções 3 e 4 — Lançar placar

- **3:** um jogo por vez (informa ID e placar, ex.: `2-1`).
- **4:** modo interativo nos jogos pendentes; Enter pula, `sair` encerra.

O placar é salvo em `resultados.csv`. Formatos aceitos: `2-1`, `2x1`, `2 1`.

### Opção 5 — Remover placar

Remove resultado de um ou mais jogos (útil para corrigir antes de confirmar a rodada).

### Opção 10 — Baseline pré-rodada

Salva o estado atual **antes** de uma rodada começar, para a coluna Rod contar só os jogos novos do dia. Equivalente a preparar o “ponto de partida” da Rod.

### Opções 12 e 13 — Conferência com Excel

- **12 (`conferir`):** compara o cálculo do programa com `classificacao_referencia.csv`.
- **13:** importa um CSV de classificação exportado do Excel (atualiza referência e exports).

Use para validar se o programa e a planilha estão alinhados.

---

## Fluxo recomendado para administradores

### Início da temporada / planilha nova

```bash
python -m src.cli reset --arquivo "caminho/para/Fase de grupos.csv"
# ou, mantendo placares já preenchidos no Excel:
python -m src.cli reset --com-resultados
```

### Antes de uma rodada de jogos

1. `git pull`
2. Menu **10** (baseline pré-rodada) **ou** aguardar a opção **2** do dia anterior
3. Conferir próximos jogos: menu **6**

### Durante os jogos (placar provisório)

1. Menu **3** ou **4** — lançar placar assim que souber o resultado
2. Menu **1** — compartilhar (informe os IDs dos jogos da rodada para gerar imagem completa)
3. A **Rod** soma pontos só nos jogos novos desde o snapshot

**Atenção:** não lance placar no programa se o jogo ainda não tiver resultado real na planilha oficial. Placares “só por colocar” (ex.: 0×0 provisório) geram divergência com o Excel.

### Fim da rodada (placares oficiais)

1. Ajustar/corrigir placares (opções **3**, **4** ou **5**)
2. Menu **2** — confirmar rodada
3. `git add data/resultados.csv data/classificacao_snapshot.json && git commit && git push`
4. Menu **1** — compartilhar classificação final do dia

---

## Comandos CLI (referência)

```bash
# Menu
python -m src.cli

# Validar palpites e estrutura
python -m src.cli validar

# Ver classificação completa no terminal (4 colunas + soma)
python -m src.cli classificar

# Compartilhar (texto + PNG)
python -m src.cli compartilhar
python -m src.cli compartilhar --jogo 57 58          # + imagem rodada_j57_58.png
python -m src.cli compartilhar --confirmar-rodada    # fim da rodada

# Lançar / remover resultado
python -m src.cli resultado --jogo 61 --placar 2-1
python -m src.cli resultado --remover --jogo 61
python -m src.cli resultado --interativo

# Próximos jogos (com ID)
python -m src.cli proximos --limite 8

# Palpites em imagem
python -m src.cli palpites --jogo 57 58
python -m src.cli palpites --jogo 57 --provisorio     # com quesito e vencedor

# Exportar CSV da classificação (formato Excel)
python -m src.cli exportar

# Conferir com Excel
python -m src.cli importar-referencia --arquivo "data/classificacao_referencia.csv"
python -m src.cli conferir

# Importar placares das linhas PLACAR do bolao.csv
python -m src.cli importar-resultados

# Reiniciar bolão com planilha nova
python -m src.cli reset
python -m src.cli reset --com-resultados

# Bandeiras para PNGs
python -m src.cli bandeiras
python -m src.cli bandeiras --forcar
```

---

## Saídas geradas (imagens)

| Arquivo | Conteúdo |
|---------|----------|
| `classificacao_grupo.png` | Tabela preta/branca: posição, nome, **Placar, Venc., G.casa, G.fora**, total (**Pts**), pontos na rodada (**Rod**). |
| `rodada_j57_58.png` | Classificação + palpites provisórios dos jogos 57 e 58 (quesito + Acertou/Errou vencedor). |
| `palpites_j57.png` | Só palpites do jogo 57 (com bandeiras). |

Requer Pillow instalado. Sem Pillow, texto e CSV continuam funcionando.

---

## Problemas comuns

### Classificação diferente do Excel

1. Verifique se `resultados.csv` tem jogos que **ainda não** estão na planilha (placar provisório).
2. Rode `python -m src.cli conferir` com `classificacao_referencia.csv` atualizado.
3. Confira se o jogo tem linha **PLACAR** preenchida no Excel antes de contar pontos lá.

### Coluna Rod estranha

- **Rod** depende de `classificacao_snapshot.json`. Confirme a rodada (opção **2**) após os jogos oficiais.
- Use opção **10** no início do dia se quiser resetar o que conta como “rodada atual”.

### Conflito no `git pull`

Se outro admin já atualizou `resultados.csv`:

```bash
git stash
git pull
git stash pop
# Resolva conflitos manualmente se houver, depois commit
```

### Atualizar palpites da planilha

Exporte de novo a aba *Fase de grupos* do Excel para `data/bolao.csv` (ou use `reset` com o arquivo novo). Os **resultados** em `resultados.csv` são mantidos separadamente.

---

## Testes

```bash
python -m unittest discover -s tests -v
```

Cobrem pontuação, ranking, parser da planilha THDFM, snapshot e export de imagens.

---

## Estrutura do projeto

```
THDFM-Bolao-Copa-do-Mundo/
├── data/                  # CSVs, snapshot, PNGs gerados
├── scripts/               # setup_data, download_bandeiras, reset_bolao
├── src/
│   ├── cli.py             # Comandos e menu
│   ├── menu.py            # Menu interativo
│   ├── ranking.py         # Classificação e exports
│   ├── scoring.py         # Regras de pontos
│   ├── thdfm_parser.py    # Leitura do CSV do Excel
│   ├── palpites_view.py   # Palpites e modo provisório
│   ├── image_export.py    # PNGs (classificação e palpites)
│   └── snapshot.py        # Baseline da coluna Rod
└── tests/
```

---

## Contato e repositório

[github.com/mazeta1910/THDFM-Bolao-Copa-do-Mundo](https://github.com/mazeta1910/THDFM-Bolao-Copa-do-Mundo)

Dúvidas sobre regras de pontuação: conferir sempre com a planilha oficial do bolão THDFM.
