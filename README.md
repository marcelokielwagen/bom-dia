# Bom Dia

Página do dia para **Blumenau** e **Balneário Camboriú**:

| Parte | De onde vem |
|---|---|
| Previsão de hoje hora a hora, gráfico da temperatura e a semana | [Open-Meteo](https://open-meteo.com/), buscada ao abrir a página (sempre atual) |
| Frase motivacional e frase de Câncer | `frases.js` — troca sozinha a cada dia |
| Notícias em 3 abas: Mundo, Política, TI e Segurança | Vários sites (lista em `scripts/noticias.py`); o GitHub roda `scripts/noticias.py` a cada 3 horas e grava `noticias.json` |

## Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | A página |
| `frases.js` | Listas de frases (edite à vontade) |
| `noticias.json` | Notícias resumidas (gerado automaticamente) |
| `scripts/noticias.py` | Baixa as notícias. Uso local: `python -I scripts/noticias.py noticias.json` |
| `.github/workflows/noticias.yml` | Agenda do GitHub que atualiza as notícias |

Desenvolvido por Claude Opus 5.5.
