# Bolão Copa

Sistema de classificação automática para o bolão THDFM Copa do Mundo 2026.

## Requisitos

- Python 3.11+
- Biblioteca padrão (texto/CSV). Para imagem PNG: `pip install pillow`

## Arquivos de dados

Coloque na pasta `data/` (ou deixe os CSVs em `Downloads`):

```bash
python scripts/setup_data.py
python scripts/download_bandeiras.py
```

| Arquivo | Descrição |
|---------|-----------|
| `bolao.csv` | Exportação ativa da aba "Fase de grupos" (criada pelo `reset`) |
| `classificacao_referencia.csv` | Classificação provisória (opcional, para validação) |
| `resultados.csv` | Placares registrados via CLI (versionado no Git para sincronizar entre PCs) |
| `flags/` | Bandeiras reais em PNG (baixadas automaticamente ou via `bandeiras`) |
| `classificacao_grupo.txt` | Tabela em texto para o grupo |
| `classificacao_grupo.png` | Imagem da classificação (requer Pillow) |
| `classificacao_snapshot.json` | Baseline da coluna Rod (versionado no Git para sincronizar entre PCs) |

## Pontuação

- **Placar exato:** 5 pontos (3 placar + 2 vencedor)
- **Vencedor certo** (sem placar): 2 pontos
- **Gols casa/fora** (sem placar exato): 1 ponto cada
- Vencedor e gols parciais podem somar (máx. 4 sem placar exato)
- **Desempate:** soma → placar → vencedor → gols casa → gols fora

## Comandos

```bash
# Menu interativo (recomendado)
python -m src.cli
python -m src.cli menu
```

### Linha de comando

```bash
# Resumo da importação
python -m src.cli importar --arquivo data/bolao.csv

# Validar integridade
python -m src.cli validar

# Reiniciar com planilha nova (zera resultados, snapshot e exports antigos)
python -m src.cli reset

# Reiniciar mantendo os placares ja preenchidos na planilha (linhas PLACAR)
python -m src.cli reset --com-resultados

# Importar placares da planilha ativa sem refazer o reset
python -m src.cli importar-resultados

# Importar classificacao provisoria do Excel para conferencia
python -m src.cli importar-referencia --arquivo "caminho/CLASSIFICACAO.csv"
python -m src.cli conferir

# Registrar resultado de um jogo
python -m src.cli resultado --jogo 72 --placar 1-1

# Remover placar de um ou mais jogos (volta ao estado anterior)
python -m src.cli resultado --remover --jogo 51 52

# Modo interativo para jogos pendentes (Enter pula, 'sair' ou Ctrl+C encerra)
python -m src.cli resultado --interativo

# Ver classificação no terminal
python -m src.cli classificar

# Tabela em texto e imagem PNG para colar no WhatsApp
python -m src.cli compartilhar

# Ao final da rodada (placares oficiais), confirma a baseline fixa
python -m src.cli compartilhar --confirmar-rodada

# Durante os jogos pode compartilhar com placar provisorio: Rodada conta so jogos novos
# Corrigir placar nao gera variacao negativa. Baseline so muda com --confirmar-rodada

# Definir baseline manualmente (ex.: inicio do dia de jogos)
python -m src.cli baseline

# Instalar suporte a PNG (uma vez)
pip install pillow

# Ver próximos jogos e seus IDs
python -m src.cli proximos --limite 6

# Palpites de jogos específicos (texto + PNG)
python -m src.cli palpites --jogo 51 52

# Palpites com status provisório (quesito + vencedor, estilo planilha)
python -m src.cli palpites --jogo 51 --provisorio

# Baixar bandeiras reais para os PNGs de palpites (cache em data/flags/)
python -m src.cli bandeiras

# Exportar CSV da classificação
python -m src.cli exportar

# Conferir com classificacao_referencia.csv
python -m src.cli conferir
```

## Testes

```bash
python -m unittest discover -s tests -v
```

## Fluxo típico

1. Exporte a planilha do Excel como CSV e salve em `data/bolao.csv`
2. Rode `python -m src.cli` e use o menu (ou `validar` na linha de comando)
3. Antes de uma rodada de jogos: opção **10** no menu (baseline)
4. Durante os jogos: opções **3/4** (placar) e **1** (compartilhar)
5. Ao final: opção **2** (confirmar rodada)
