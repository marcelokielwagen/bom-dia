"""Baixa as noticias por categoria (RSS) e grava noticias.json.

Roda sozinho no GitHub (Actions) a cada 3 horas. So usa a biblioteca padrao.
Uso local: python -I scripts/noticias.py noticias.json

Para trocar ou acrescentar sites, edite a lista CATEGORIAS abaixo.
Cada fonte e (nome, endereco do RSS, filtro). O filtro e opcional: se tiver,
so entram noticias cujo titulo combine com ele; com "!" na frente, entram so
as que NAO combinam.
"""
import gzip
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

PROMO = r"promo|oferta|cupom|desconto|menor pre[cç]o|black friday|baixou|barato|pre[cç]o no ch[aã]o"


def gnews(busca):
    """Endereco do Google Noticias para uma busca (ultimos 3 dias, em portugues)."""
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote(busca + " when:3d") +
            "&hl=pt-BR&gl=BR&ceid=BR:pt-419")


CATEGORIAS = [
    ("mundo", "Mundo", 8, [
        ("BBC Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml", None),
        ("g1 Mundo", "https://g1.globo.com/rss/g1/mundo/", None),
        ("DW Brasil", "https://rss.dw.com/rdf/rss-br-all", None),
    ]),
    ("politica", "Política", 8, [
        ("g1 Política", "https://g1.globo.com/rss/g1/politica/", None),
        ("Poder360", "https://www.poder360.com.br/feed/", None),
    ]),
    ("ti", "TI e Segurança", 10, [
        ("CISO Advisor", "https://www.cisoadvisor.com.br/feed/", None),
        ("TecMundo", "https://rss.tecmundo.com.br/feed", "!" + PROMO),
        ("The Hack", "https://thehack.com.br/feed/", None),
        ("g1 Tecnologia", "https://g1.globo.com/rss/g1/tecnologia/", "!" + PROMO),
    ]),
    ("acoes", "Ações e Mercado", 10, [
        ("Money Times", "https://www.moneytimes.com.br/feed/", None),
        ("Investing.com", "https://br.investing.com/rss/news_25.rss", None),
        ("Seu Dinheiro", "https://www.seudinheiro.com/feed/", None),
        ("E-Investidor", "https://einvestidor.estadao.com.br/feed/", None),
    ]),
    # Noticias da cidade: a pagina mostra so a da cidade escolhida (ids = "blumenau" e "bc")
    ("blumenau", "Blumenau", 8, [
        ("Google Notícias", gnews("Blumenau"), None),
    ]),
    ("bc", "Balneário Camboriú", 10, [
        ("BC Notícias", "https://www.bcnoticias.com.br/feed/", None),
        ("Camboriú News", "https://camboriu.news/feed/", None),
        ("Google Notícias", gnews('"Balneário Camboriú"'), None),
    ]),
]
POR_FONTE = 4
TAM_RESUMO = 220
CABECALHO = {"User-Agent": "Mozilla/5.0 (bom-dia)", "Accept": "application/rss+xml,application/xml,text/xml,*/*"}


def limpar(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    texto = html.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def resumir(texto):
    if len(texto) <= TAM_RESUMO:
        return texto
    corte = texto[:TAM_RESUMO]
    ponto = corte.rfind(". ")
    if ponto > TAM_RESUMO * 0.5:
        return corte[: ponto + 1]
    return corte[: corte.rfind(" ")].rstrip(",;:") + "…"


CREDITO = re.compile(r"REUTERS|AFP|\bAP\b|EFE|Getty|Reprodu[cç][aã]o|Divulga[cç][aã]o|Arquivo|Foto:|/", re.I)


def sem_legenda(texto):
    """O g1 comeca o resumo com a legenda da foto e o credito (ex.: REUTERS/Fulano).
    Se achar uma linha curta de credito no inicio, joga fora tudo ate ela."""
    linhas = [l.strip() for l in re.sub(r"<[^>]+>", "\n", texto or "").splitlines() if l.strip()]
    for i, l in enumerate(linhas[:4]):
        if len(l) < 70 and CREDITO.search(l) and i + 1 < len(linhas):
            return "\n".join(linhas[i + 1:])
    return "\n".join(linhas)


def data_iso(texto):
    if not texto:
        return None
    try:
        d = parsedate_to_datetime(texto)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat()


def filho(el, nome):
    """Acha o primeiro filho pelo nome local (ignora namespaces)."""
    for c in el:
        if c.tag.split("}")[-1] == nome:
            return (c.text or "").strip()
    return ""


_cache = {}


def baixar(url):
    if url not in _cache:
        req = urllib.request.Request(url, headers=CABECALHO)
        dados = urllib.request.urlopen(req, timeout=25).read()
        if dados[:2] == b"\x1f\x8b":  # alguns sites (g1) mandam compactado sem pedir
            dados = gzip.decompress(dados)
        _cache[url] = dados
    return _cache[url]


def ler_google(url, por_veiculo=2, maximo=8):
    """Google Noticias: o titulo vem como 'Titulo - Veiculo'. Separa os dois, mostra as mais
    novas primeiro e limita por veiculo para nao ficar tudo do mesmo site."""
    raiz = ET.fromstring(baixar(url))
    itens = []
    for it in raiz.iter():
        if it.tag.split("}")[-1] != "item":
            continue
        bruto, link = limpar(filho(it, "title")), filho(it, "link")
        if " - " not in bruto or not link:
            continue
        titulo, veiculo = bruto.rsplit(" - ", 1)
        itens.append({"titulo": titulo.strip(), "resumo": "", "link": link, "fonte": veiculo.strip(),
                      "data": data_iso(filho(it, "pubDate"))})
    itens.sort(key=lambda x: x["data"] or "", reverse=True)
    saida, contagem, vistos = [], {}, set()
    for x in itens:
        chave = x["titulo"].lower()[:50]
        if contagem.get(x["fonte"], 0) >= por_veiculo or chave in vistos:
            continue
        contagem[x["fonte"]] = contagem.get(x["fonte"], 0) + 1
        vistos.add(chave)
        saida.append(x)
        if len(saida) >= maximo:
            break
    return saida


def ler_fonte(nome, url, filtro):
    if "news.google.com" in url:
        return ler_google(url)
    raiz = ET.fromstring(baixar(url))
    itens = [e for e in raiz.iter() if e.tag.split("}")[-1] == "item"]
    saida = []
    for it in itens:
        titulo = limpar(filho(it, "title"))
        link = filho(it, "link")
        if not titulo or not link:
            continue
        if filtro:  # "!" na frente = excluir o que combina
            achou = re.search(filtro.lstrip("!"), titulo, re.I)
            if bool(achou) == filtro.startswith("!"):
                continue
        resumo = resumir(limpar(sem_legenda(filho(it, "description"))))
        if resumo.lower().startswith(titulo.lower()[:40]):
            resumo = ""
        saida.append({
            "titulo": titulo,
            "resumo": resumo,
            "link": link,
            "fonte": nome,
            "data": data_iso(filho(it, "pubDate") or filho(it, "date")),
        })
        if len(saida) >= POR_FONTE:
            break
    return saida


def montar_categoria(fontes, total, ja_usados):
    por_fonte = []
    for nome, url, filtro in fontes:
        try:
            por_fonte.append(ler_fonte(nome, url, filtro))
        except Exception as e:  # uma fonte fora do ar nao derruba as outras
            print(f"Falhou {nome}: {e}", file=sys.stderr)
    # intercala as fontes: 1a de cada, 2a de cada...
    lista = []
    for i in range(max([len(x) for x in por_fonte] or [0])):
        for itens in por_fonte:
            if i < len(itens) and itens[i]["link"] not in ja_usados:
                ja_usados.add(itens[i]["link"])
                lista.append(itens[i])
    return lista[:total]


def ibovespa():
    """Pontos e variacao do Ibovespa no dia (Yahoo Finance). Se falhar, devolve None."""
    try:
        req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/%5EBVSP?range=1d&interval=1d",
                                     headers={"User-Agent": "Mozilla/5.0"})
        meta = json.loads(urllib.request.urlopen(req, timeout=20).read())["chart"]["result"][0]["meta"]
        atual, anterior = meta["regularMarketPrice"], meta["chartPreviousClose"]
        return {"pontos": round(atual), "variacao": round((atual / anterior - 1) * 100, 2),
                "hora": datetime.fromtimestamp(meta["regularMarketTime"], timezone.utc).isoformat()}
    except Exception as e:
        print(f"Falhou Ibovespa: {e}", file=sys.stderr)
        return None


# Bolsas e acoes que aparecem na pagina: (id, nome, grupo, simbolo no Yahoo Finance).
# Para trocar um banco ou acrescentar uma acao, e so mexer nesta lista.
BOLSAS = [
    ("sp500", "S&P 500", "indices", "^GSPC"),
    ("nasdaq", "Nasdaq", "indices", "^IXIC"),
    ("dow", "Dow Jones", "indices", "^DJI"),
    ("nikkei", "Nikkei 225", "indices", "^N225"),
    ("dax", "DAX (Alemanha)", "indices", "^GDAXI"),
    ("itub", "Itaú", "bancos", "ITUB4.SA"),
    ("bbdc", "Bradesco", "bancos", "BBDC4.SA"),
    ("bbas", "Banco do Brasil", "bancos", "BBAS3.SA"),
    ("petr", "Petrobras", "famosas", "PETR4.SA"),
    ("vale", "Vale", "famosas", "VALE3.SA"),
]


def bolsas():
    """Preco e variacao do dia de cada item de BOLSAS. O que falhar fica de fora."""
    saida = []
    for cid, nome, grupo, simbolo in BOLSAS:
        try:
            req = urllib.request.Request(
                "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(simbolo) + "?range=1d&interval=1d",
                headers={"User-Agent": "Mozilla/5.0"})
            meta = json.loads(urllib.request.urlopen(req, timeout=20).read())["chart"]["result"][0]["meta"]
            atual, anterior = meta["regularMarketPrice"], meta["chartPreviousClose"]
            saida.append({"id": cid, "nome": nome, "grupo": grupo, "preco": round(atual, 2),
                          "variacao": round((atual / anterior - 1) * 100, 2)})
        except Exception as e:
            print(f"Falhou {nome}: {e}", file=sys.stderr)
    return saida


NOVELA = "Quem Ama Cuida"
GRADE_GLOBO = "https://redeglobo.globo.com/sc/nsctv/programacao/"  # NSC TV, a Globo de Santa Catarina


def novela():
    """Horarios dos proximos dias da novela na grade da Globo em SC. A pagina da grade traz os
    dados dentro do proprio HTML. Se falhar, devolve None (e o programa mantem o valor antigo)."""
    try:
        pagina = html.unescape(baixar(GRADE_GLOBO).decode("utf-8", "replace"))
        achados = re.findall(r'"contentType":"[^"]*","duration":"(\d+):(\d+):\d+"[^{}]*?"name":"' + re.escape(NOVELA) +
                             r'".*?"scheduledDate":"(\d{4}-\d\d-\d\d)T(\d\d:\d\d)', pagina)
        exibicoes = sorted({(d, ini, int(h) * 60 + int(m)) for h, m, d, ini in achados})
        if not exibicoes:
            return None
        return {"nome": NOVELA, "canal": "TV Globo",
                "exibicoes": [{"data": d, "inicio": ini, "duracao": dur} for d, ini, dur in exibicoes]}
    except Exception as e:
        print(f"Falhou novela: {e}", file=sys.stderr)
        return None


def main(destino):
    usados, categorias = set(), []
    for cid, nome, total, fontes in CATEGORIAS:
        noticias = montar_categoria(fontes, total, usados)
        print(f"{nome}: {len(noticias)} noticias")
        categorias.append({"id": cid, "nome": nome, "noticias": noticias})
    if not any(c["noticias"] for c in categorias):
        print("Nenhuma noticia baixada; mantendo o arquivo anterior.", file=sys.stderr)
        return 1
    antigo = {}  # se alguma fonte cair, mantem o que ja estava no arquivo
    try:
        with open(destino, encoding="utf-8") as f:
            antigo = json.load(f)
    except (OSError, ValueError):
        pass
    nov = novela() or antigo.get("novela")
    bol = bolsas() or antigo.get("bolsas")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump({"atualizado": datetime.now(timezone.utc).isoformat(), "ibovespa": ibovespa(), "novela": nov,
                   "bolsas": bol, "categorias": categorias}, f, ensure_ascii=False, indent=1)
    print(f"Gravado em {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "noticias.json"))
