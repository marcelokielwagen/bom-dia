# Bom Dia

Página do dia para **Blumenau** e **Balneário Camboriú**:

| Parte | De onde vem |
|---|---|
| Previsão de hoje hora a hora, gráfico da temperatura e a semana | [Open-Meteo](https://open-meteo.com/), buscada ao abrir a página (sempre atual) |
| Rio Itajaí-Açu em Blumenau, avisos do INMET e notícias de segurança em português | AlertaBlu, INMET e sites brasileiros, pelo robô |
| Gráficos (dia, semana, mês, ano) ao tocar nos índices, bancos, dólar, euro e Bitcoin | Yahoo Finance, gravado pelo robô em `graficos.json` |
| Ranking diário dos 10 países mais atacados (computador, navegação, e-mail, rede, ransomware) | Kaspersky Cyberthreat Map, lido pelo robô |
| Fechamento e vencimento das faturas dos cartões | Calculado na página (lista `CARTOES` em `index.html`) |
| Cotações (dólar, euro, bitcoin) ao vivo; Ibovespa pelo robô | AwesomeAPI e Yahoo Finance |
| Horário da novela Quem Ama Cuida | Grade da Globo (NSC TV), pelo robô |
| Música do dia (50 na lista, uma por dia) com botão do Spotify | `frases.js` |
| Frase motivacional, frase e cor do dia de Câncer | `frases.js` — troca sozinha a cada dia |
| Notícias em 4 abas: Mundo, Política, TI e Segurança, Ações e Mercado | Vários sites (lista em `scripts/noticias.py`); o GitHub roda `scripts/noticias.py` a cada 3 horas e grava `noticias.json` |

## Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | A página |
| `frases.js` | Listas de frases (edite à vontade) |
| `noticias.json` | Notícias resumidas (gerado automaticamente) |
| `scripts/noticias.py` | Baixa as notícias. Uso local: `python -I scripts/noticias.py noticias.json` |
| `.github/workflows/noticias.yml` | Agenda do GitHub que atualiza as notícias |

Desenvolvido por Claude Opus 5.5.
