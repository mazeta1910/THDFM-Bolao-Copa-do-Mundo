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

### Dados operacionais (versionados no Git)

| Arquivo | Quem atualiza | Função |
|---------|---------------|--------|
| `bolao.csv` | Admin (export do Excel) | Palpites de todos + estrutura dos jogos (grupos e mata-mata). |
| `resultados.csv` | **Programa** (opções 3–5 do menu) | Placares lançados pela CLI. **Versionado no Git** para sincronizar entre PCs. |
| `classificacao_snapshot.json` | Programa (opção 2 ou 10) | Baseline da coluna **Rod**: pontos e jogos já “fechados” na última rodada confirmada. **Versionado no Git**. |
| `classificacao_referencia.csv` | Excel (opcional) | Classificação exportada do Excel para **conferência** (`conferir`). |
| `palpites_penaltis.csv` | Programa / import | Palpites de vencedor nos pênaltis (mata-mata empatado). |
| `BOLÃO THDFM WC26 - CRAVADURA.csv` | Excel | Cravadura congelada até 19/jul (coluna REAL OFICIAL). |
| `BOLÃO THDFM WC26 - RESPOSTAS 32 AVOS.csv` | Participantes | Palpites dos 32 avos (import via script). |
| `flags/` | `python -m src.cli bandeiras` | Bandeiras usadas nos PNGs de palpites. |

### Exports gerados — pasta `data/ultimo/`

**Sempre consulte `data/ultimo/`** para achar o último arquivo gerado. Os nomes são fixos (sem sufixo de jogo ou data); cada novo export **substitui** o anterior.

| Arquivo | Conteúdo |
|---------|----------|
| `manifest.txt` | Índice do que existe na pasta e descrição de cada arquivo. |
| `classificacao.png` / `.txt` / `.csv` | Classificação geral — prêmio B (todos os jogos realizados). |
| `premio_a.png` / `.csv` | Prêmio A: palpitadura dos grupos + cravadura. |
| `fase_32avos.png` | Pontuação parcial dos 32 avos (Placar, Vencedor, Gols casa, Gols fora, Soma). |
| `fase_grupos_mais_32avos.png` | Grupos + 32 avos combinados (detalhada). |
| `rodada.png` | Classificação + palpites provisórios da rodada informada. |
| `palpites.png` / `palpites_provisorios.png` | Palpites exportados. |
| `ranking_grupos.txt` | Ranking parcial da classificação dos grupos. |

Ao compartilhar, exportar palpites ou gerar fase, o programa **remove automaticamente** exports antigos que ficavam soltos em `data/` (ex.: `rodada_j73.png`, `classificacao_32avos.png`).

A pasta `data/ultimo/` está no `.gitignore` — não versione PNGs/TXTs gerados; versione só `resultados.csv` e `classificacao_snapshot.json`.

### Sincronizar entre administradores (Git)

**Fluxo combinado do time:** issue por rodada → branch → PR → revisão → merge. Evita push direto na `main` e deixa histórico claro.

#### 1. Abrir issue (GitHub)

Título sugerido: `Rodada jogos 81–82`

Corpo mínimo:
- Jogos da rodada: 81, 82
- Admin responsável: @usuario
- [ ] Placares lançados
- [ ] Rodada confirmada (snapshot)
- [ ] Imagens compartilhadas no grupo

No repositório: **Issues → New issue** → escolher template **Rodada**.

#### 2. Branch e trabalho local

```bash
git pull
git checkout -b rodada/j81-j82
python -m src.cli          # lançar placares, compartilhar, confirmar rodada
```

#### 3. Commit e Pull Request

```bash
git add data/base/resultados.csv data/base/classificacao_snapshot.json
git commit -m "chore: confirma placares j81-82 e atualiza baseline"
git push -u origin rodada/j81-j82
```

No GitHub: **Compare & pull request** → preencher o template → solicitar revisão do outro admin (se estiver disponível) → **Merge**.

No corpo do PR ou no commit, referencie a issue: `Closes #N` (fecha automaticamente ao mergear).

#### 4. No outro PC (após o merge)

```bash
git pull
python -m src.cli compartilhar
```

**Importante:**
- Sempre `git pull` antes de lançar placares.
- Não commitar direto na `main` (exceto emergência; depois abrir PR retroativo se possível).
- Arquivos versionados da rodada: `data/base/resultados.csv` e `data/base/classificacao_snapshot.json`.
- Exports em `data/ultimo/` **não** vão para o Git (cada PC gera localmente).

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

Ao rodar `python -m src.cli`, o cabeçalho mostra **status ao vivo**: jogos realizados, fase atual, líderes A/B e último export em `data/ultimo/`.

```
 1. Rodada de hoje (fluxo guiado)
 2. Compartilhar (escolher tabelas)
 3. Placares        → lançar, remover, próximos
 4. Palpites        → imagem simples ou provisório
 5. Tabelas         → terminal, fase, grupos, manifest, abrir pasta
 6. Ferramentas     → baseline, confirmar rodada, validar, imports, reset
 0. Sair
```

**Atalhos:** `r` rodada · `c` compartilhar · `s` status · `u` manifest/pasta ultimo

### Opção 1 — Rodada de hoje

Fluxo contínuo: baseline opcional → placares interativos → **wizard de compartilhar** → confirmar rodada opcional.

### Opção 2 — Compartilhar (escolher tabelas)

Antes de gerar arquivos, escolha o **pacote de exports**:

| Preset | Conteúdo |
|--------|----------|
| 1. Completo | Geral + prêmio A + parciais (32 avos / grupos+32 avos) |
| 2. Geral + parcial + palpites | Como acima, sem A, **com rodada.png** |
| 3. Geral + parcial | Sem prêmio A |
| 4. Geral + prêmio A | Sem parciais de mata-mata |
| 5. Só geral | Apenas prêmio B |
| 6. Só parcial | Apenas fases disponíveis |
| 7. Personalizado | Marca item a item (txt, PNGs, rodada) |

O menu mostra **pré-visualização** do que será salvo em `data/ultimo/` antes de confirmar. Se incluir **rodada.png**, informe os IDs dos jogos com placar provisório (sugestão automática quando possível).

Via CLI:

```bash
python -m src.cli compartilhar --export geral fase_32avos rodada --jogo 73 74
python -m src.cli confirmar-rodada   # só baseline, sem exports
```

### Confirmar rodada (separado do compartilhar)

Em **Ferramentas → 2** ou `python -m src.cli confirmar-rodada`: salva o snapshot e zera a coluna **Rod** na próxima divulgação, **sem** gerar PNGs.

### Submenu Placares

- Lançar um jogo ou em lote (interativo)
- Remover placar
- Ver próximos jogos
- Empate no mata-mata: informe vencedor nos pênaltis (ou placar provisório com Enter)

### Submenu Tabelas

- Classificação geral no terminal
- Pontuação parcial por fase (menu numerado: grupos, 32 avos, oitavas…)
- Ranking parcial dos grupos
- Ver `manifest.txt` ou abrir pasta `data/ultimo/`

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
3. Abrir PR com `data/base/resultados.csv` e `data/base/classificacao_snapshot.json` (ver seção Git)
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

# Compartilhar (escolher exports em data/ultimo/)
python -m src.cli compartilhar
python -m src.cli compartilhar --export geral fase_32avos rodada --jogo 73 74
python -m src.cli compartilhar --confirmar-rodada    # legado: compartilha + confirma

# Confirmar rodada (so baseline, sem exports)
python -m src.cli confirmar-rodada

# Pontuação parcial por fase (detalhada)
python -m src.cli fase --fase 32avos
python -m src.cli fase --fase grupos_mais_32avos

# Lançar / remover resultado
python -m src.cli resultado --jogo 76 --placar 0-0 --provisorio
python -m src.cli resultado --jogo 73 --placar 1-1 --penaltis BRA
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

# Importar palpites dos 32 avos (RESPOSTAS → bolao.csv)
python scripts/import_32avos.py --atualizar
python scripts/import_oitavas.py
python scripts/import_oitavas.py --atualizar

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

Todos os PNGs vão para **`data/ultimo/`**. Consulte **`manifest.txt`** para ver o que foi gerado por último.

| Arquivo | Conteúdo |
|---------|----------|
| `classificacao.png` | Prêmio B: posição, nome, Placar, Vencedor, Gols casa, Gols fora, Pts, Rod. |
| `premio_a.png` | Prêmio A: grupos + cravadura. |
| `fase_32avos.png` | 32 avos: detalhamento Placar / Vencedor / Gols casa / Gols fora / Soma. |
| `rodada.png` | Classificação + palpites provisórios dos jogos informados. |
| `palpites.png` | Palpites de um ou mais jogos (com bandeiras). |

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
├── data/                  # CSVs operacionais + flags/
│   └── ultimo/            # Exports gerados (gitignored; veja manifest.txt)
├── scripts/               # setup_data, download_bandeiras, import_32avos, import_oitavas
├── src/
│   ├── cli.py             # Comandos e menu
│   ├── menu.py            # Menu interativo
│   ├── ranking.py         # Classificação e exports
│   ├── scoring.py         # Regras de pontos (grupos + mata-mata)
│   ├── exports_manager.py # Pasta data/ultimo/ e limpeza de legados
│   ├── share_options.py   # Presets de export do compartilhar
│   ├── penaltis.py        # Palpites e resultado nos pênaltis
│   ├── cravadura.py       # Cravadura congelada
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
