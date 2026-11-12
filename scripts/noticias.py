"""Baixa as principais noticias do mundo (RSS) e grava noticias.json.

Roda sozinho no GitHub (Actions) a cada 3 horas. So usa a biblioteca padrao.
Uso local: python -I scripts/noticias.py noticias.json
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FONTES = [
    ("BBC Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml"),
    ("g1 Mundo", "https://g1.globo.com/rss/g1/mundo/"),
    ("DW Brasil", "https://rss.dw.com/rdf/rss-br-all"),
]
POR_FONTE = 4
TOTAL = 10
TAM_RESUMO = 220


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


def ler_fonte(nome, url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (previsao-do-dia)"})
    dados = urllib.request.urlopen(req, timeout=20).read()
    raiz = ET.fromstring(dados)
    itens = [e for e in raiz.iter() if e.tag.split("}")[-1] == "item"]
    saida = []
    for it in itens:
        titulo = limpar(filho(it, "title"))
        link = filho(it, "link")
        if not titulo or not link:
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


def main(destino):
    por_fonte = []
    for nome, url in FONTES:
        try:
            por_fonte.append(ler_fonte(nome, url))
        except Exception as e:  # uma fonte fora do ar nao derruba as outras
            print(f"Falhou {nome}: {e}", file=sys.stderr)
    # intercala as fontes: 1a de cada, 2a de cada...
    noticias, vistos = [], set()
    for i in range(POR_FONTE):
        for lista in por_fonte:
            if i < len(lista) and lista[i]["titulo"] not in vistos:
                vistos.add(lista[i]["titulo"])
                noticias.append(lista[i])
    noticias = noticias[:TOTAL]
    if not noticias:
        print("Nenhuma noticia baixada; mantendo o arquivo anterior.", file=sys.stderr)
        return 1
    with open(destino, "w", encoding="utf-8") as f:
        json.dump({"atualizado": datetime.now(timezone.utc).isoformat(), "noticias": noticias},
                  f, ensure_ascii=False, indent=1)
    print(f"{len(noticias)} noticias gravadas em {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "noticias.json"))
