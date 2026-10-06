# posts-sst

Imagens e ferramentas dos posts de Instagram de @alconsultoriaengsst.

- `tools/render_carousel.py` + `tools/fonts/`: gera carrosséis em PNG (1080x1350) a partir de um JSON.
- `templates/exemplo-post1.json`: exemplo do JSON (tipos de slide: cover, content, compare, cta).
- `AAAA-MM-DD-assunto/`: PNGs de cada post (URLs públicas lidas pelo Metricool).

Uso: `python3 tools/render_carousel.py spec.json pasta_saida`
