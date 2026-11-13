"""Desenha o icone do Bom Dia (sol nascendo atras dos morros) e grava em icons/.
Precisa do Pillow (pip install pillow). Uso: python -I scripts/gerar_icone.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

S = 1024  # desenha grande e reduz depois, para as bordas ficarem lisas
raiz = Path(__file__).resolve().parent.parent
saida = raiz / "icons"
saida.mkdir(exist_ok=True)

# ceu: degrade do amanhecer (laranja embaixo, roxo em cima)
img = Image.new("RGB", (S, S))
d = ImageDraw.Draw(img)
topo, meio, base = (66, 52, 140), (214, 108, 150), (255, 178, 110)
for y in range(S):
    t = y / (S - 1)
    a, b, k = (topo, meio, t / 0.6) if t < 0.6 else (meio, base, (t - 0.6) / 0.4)
    d.line([(0, y), (S, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3)))

img = img.convert("RGBA")
cx, cy = S // 2, 640

# brilho do sol
brilho = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(brilho).ellipse([cx - 330, cy - 330, cx + 330, cy + 330], fill=(255, 214, 120, 150))
img.alpha_composite(brilho.filter(ImageFilter.GaussianBlur(70)))

# raios
raios = Image.new("RGBA", (S, S), (0, 0, 0, 0))
dr = ImageDraw.Draw(raios)
for i in range(13):
    ang = math.radians(180 + 14 + i * (152 / 12))
    for lado in (-1, 1):
        dr.polygon([(cx, cy), (cx + 900 * math.cos(ang + lado * 0.035), cy + 900 * math.sin(ang + lado * 0.035)),
                    (cx + 900 * math.cos(ang), cy + 900 * math.sin(ang))], fill=(255, 232, 160, 46))
img.alpha_composite(raios)

# sol
d = ImageDraw.Draw(img)
d.ellipse([cx - 175, cy - 175, cx + 175, cy + 175], fill=(255, 224, 118, 255))
d.ellipse([cx - 135, cy - 135, cx + 135, cy + 135], fill=(255, 244, 196, 255))


# morros (dois planos)
def morro(base_y, amp, fase, cor):
    pts = [(x, base_y + amp * math.sin(x / S * 2 * math.pi * 1.4 + fase) + amp * 0.45 * math.sin(x / S * 2 * math.pi * 3.1 + fase * 2))
           for x in range(0, S + 8, 8)]
    ImageDraw.Draw(img).polygon(pts + [(S, S), (0, S)], fill=cor)


morro(742, 44, 0.6, (88, 60, 130, 255))
morro(830, 38, 2.4, (46, 32, 92, 255))

for nome, lado in (("icone-180.png", 180), ("icone-192.png", 192), ("icone-512.png", 512)):
    img.convert("RGB").resize((lado, lado), Image.LANCZOS).save(saida / nome, optimize=True)
print("icones gravados em", saida)
