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
| `resultados.csv` | Placares registrados via CLI (fonte oficial após o `reset`) |
| `flags/` | Bandeiras reais em PNG (baixadas automaticamente ou via `bandeiras`) |
| `classificacao_grupo.txt` | Tabela em texto para o grupo |
| `classificacao_grupo.png` | Imagem da classificação (requer Pillow) |
| `classificacao_snapshot.json` | Última classificação publicada (cálculo da variação) |

## Pontuação

- **Placar exato:** 5 pontos (3 placar + 2 vencedor)
- **Vencedor certo** (sem placar): 2 pontos
- **Gols casa/fora** (sem placar exato): 1 ponto cada
- Vencedor e gols parciais podem somar (máx. 4 sem placar exato)
- **Desempate:** soma → placar → vencedor → gols casa → gols fora

## Comandos

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

# Modo interativo para jogos pendentes (Enter pula, 'sair' ou Ctrl+C encerra)
python -m src.cli resultado --interativo

# Ver classificação no terminal
python -m src.cli classificar

# Tabela em texto e imagem PNG para colar no WhatsApp
python -m src.cli compartilhar

# Instalar suporte a PNG (uma vez)
pip install pillow

# Ver próximos jogos e seus IDs
python -m src.cli proximos --limite 6

# Palpites de jogos específicos (texto + PNG)
python -m src.cli palpites --jogo 51 52

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
2. Rode `python -m src.cli validar`
3. Após cada rodada de jogos, use `resultado --interativo`
4. Rode `classificar` ou `exportar` para obter a tabela atualizada
