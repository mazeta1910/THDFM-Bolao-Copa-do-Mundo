# Fotos dos participantes

Miniaturas para a classificação PNG (issue #4).

## Como adicionar

1. Veja o **nome base** do arquivo em `manifest.json` (ex.: `Mazeta`, `Haron`, `Hotel`).
2. Salve a foto nesta pasta com esse nome + a extensão que você tiver.
3. Imagem **quadrada** (rosto centralizado), ideal **256×256 px** (mínimo 128×128).

### Formatos aceitos

**PNG, JPG, JPEG e WEBP** — pode mandar direto do celular, **sem converter**.

| Participante no bolão | Nome base | Exemplos válidos |
|-----------------------|-----------|------------------|
| Mazeta | `Mazeta` | `Mazeta.jpg`, `Mazeta.jpeg`, `Mazeta.png` |
| Haron Bonamigo | `Haron` | `Haron.jpg` |
| Hotel Plus Antonio Menezes | `Hotel` | `Hotel.jpeg` |
| Rodrigo (DDD 95) | `Rodrigo` | `Rodrigo.webp` |

Lista completa: `manifest.json`.

## Quem falta foto

Participantes sem arquivo usam **iniciais** em um círculo colorido (fallback).

## Versionamento

Fotos redimensionadas podem ir para o Git. Se preferir não versionar, ignore localmente: `data/participantes/*.{png,jpg,jpeg,webp}`.
