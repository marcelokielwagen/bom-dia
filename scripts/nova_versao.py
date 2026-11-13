"""Marca uma versao nova do site (rode antes de publicar uma mudanca na pagina).

Quem abre o site depois disso (inclusive pelo atalho do celular) recebe a pagina nova
na hora, em vez da copia antiga guardada no aparelho.
Uso: python -I scripts/nova_versao.py
"""
import json
import re
import time
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
build = time.strftime("%Y%m%d%H%M%S")

pagina = raiz / "index.html"
html = pagina.read_text(encoding="utf-8")
html, n1 = re.subn(r'var B="[^"]*"', f'var B="{build}"', html, count=1)
html, n2 = re.subn(r'frases\.js\?v=[^"]*', f"frases.js?v={build}", html, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit("Nao achei os marcadores de versao no index.html")
pagina.write_text(html, encoding="utf-8", newline="\n")
(raiz / "versao.json").write_text(json.dumps({"build": build}) + "\n", encoding="utf-8", newline="\n")
print("versao", build)
