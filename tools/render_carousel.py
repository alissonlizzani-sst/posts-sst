#!/usr/bin/env python3
"""Renderiza um carrossel de Instagram (1080x1350) a partir de um JSON.

Uso: python3 render_carousel.py spec.json pasta_de_saida
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, PAD = 1080, 1350, 88
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
CB, CX = "BarlowCondensed-Bold.ttf", "BarlowCondensed-ExtraBold.ttf"
BR, BM, BS = "Barlow-Regular.ttf", "Barlow-Medium.ttf", "Barlow-SemiBold.ttf"

NAVY = (14, 36, 51)
CREAM = (244, 241, 234)
MUTED = (185, 199, 209)
PANEL = (26, 58, 82)
INK = (29, 58, 78)
SLATE = (60, 85, 104)
SOFT = (217, 226, 232)
SOFT2 = (228, 235, 240)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def F(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)


def tracked(d, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track


def tracked_w(d, text, font, track):
    return sum(d.textlength(c, font=font) + track for c in text) - track


def wrap(d, words, font, maxw):
    lines, cur, curw = [], [], 0
    space = d.textlength(" ", font=font)
    for w, c in words:
        ww = d.textlength(w, font=font)
        add = ww if not cur else ww + space
        if cur and curw + add > maxw:
            lines.append(cur)
            cur, curw = [(w, c)], ww
        else:
            cur.append((w, c))
            curw += add
    if cur:
        lines.append(cur)
    return lines


def fit(d, words, fontfile, start, minsz, maxw, maxh, lh):
    for sz in range(start, minsz - 1, -2):
        f = F(fontfile, sz)
        if any(d.textlength(w, font=f) > maxw for w, _ in words):
            continue
        lines = wrap(d, words, f, maxw)
        h = int(len(lines) * sz * lh)
        if h <= maxh:
            return f, lines, sz, h
    f = F(fontfile, minsz)
    lines = wrap(d, words, f, maxw)
    return f, lines, minsz, int(len(lines) * minsz * lh)


def draw_lines(d, x, y, lines, font, sz, lh):
    for ln in lines:
        cx = x
        for w, c in ln:
            d.text((cx, y), w, font=font, fill=c)
            cx += d.textlength(w + " ", font=font)
        y += sz * lh
    return y


def words_of(segments, accent, base):
    out = []
    for text, kind in segments:
        col = accent if kind == "a" else base
        out += [(w, col) for w in text.split()]
    return out


def plain(text, color):
    return [(w, color) for w in text.split()]


def arrow(d, x, y, color, w=44):
    d.line([(x, y), (x + w - 4, y)], fill=color, width=3)
    d.line([(x + w - 14, y - 9), (x + w - 4, y), (x + w - 14, y + 9)], fill=color, width=3, joint="curve")


def footer(d, spec, color_left, color_right, label="Próximo", arrow_color=None):
    f = F(BR, 28)
    y = H - PAD - 34
    d.text((PAD, y), spec["handle"], font=f, fill=color_left)
    if label:
        f2 = F(BS, 28)
        lw = d.textlength(label, font=f2)
        ax = W - PAD - 44
        d.text((ax - 14 - lw, y), label, font=f2, fill=color_right)
        arrow(d, ax, y + 17, arrow_color or color_right)


def header(d, spec, idx, total, color_role, color_num):
    f = F(CB, 28)
    tracked(d, (PAD, PAD), spec["role"].upper(), f, color_role, 2)
    if idx is not None:
        t = f"{idx:02d} / {total:02d}"
        f2 = F(CX, 30)
        tw = tracked_w(d, t, f2, 3)
        tracked(d, (W - PAD - tw, PAD), t, f2, color_num, 3)


def bar(d, y, accent):
    d.rectangle([PAD, y, PAD + 140, y + 12], fill=accent)
    return y + 12


def slide_cover(s, spec, accent):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    # cabeçalho
    f = F(CB, 28)
    tracked(d, (PAD, PAD + 8), spec["role"].upper(), f, MUTED, 2)
    ft = F(CX, 30)
    tag = s["tag"].upper()
    tw = tracked_w(d, tag, ft, 3)
    bx0, by0 = W - PAD - tw - 52, PAD - 8
    d.rectangle([bx0, by0, W - PAD, by0 + 30 + 28 + 8], fill=accent)
    tracked(d, (bx0 + 26, by0 + 10), tag, ft, NAVY, 3)

    maxw = W - 2 * PAD
    words = words_of(s["headline"], accent, CREAM)
    words = [(w.upper(), c) for w, c in words]
    hf, hl, hs, hh = fit(d, words, CX, 168, 90, maxw, 560, 0.98)
    sub_f = F(BR, 36)
    sub_lines = wrap(d, plain(s["sub"], SOFT), sub_f, 820)
    sub_h = int(len(sub_lines) * 36 * 1.4)
    total = 12 + 40 + hh + 64 + sub_h
    top, bottom = PAD + 90, H - PAD - 70
    y = top + (bottom - top - total) // 2
    y = bar(d, y, accent) + 40
    y = draw_lines(d, PAD, y, hl, hf, hs, 0.98) + 64
    draw_lines(d, PAD, y, sub_lines, sub_f, 36, 1.4)
    footer(d, spec, MUTED, CREAM, "Deslize", accent)
    return im


def slide_content(s, spec, accent, idx, total):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    header(d, spec, idx, total, SLATE, NAVY)
    maxw = W - 2 * PAD
    title = [(w.upper(), NAVY) for w in s["title"].split()]
    tf, tl, ts, th = fit(d, title, CX, 124, 70, maxw, 420, 0.98)
    body_f = F(BR, 40)
    bl = wrap(d, plain(s["body"], INK), body_f, maxw)
    bh = int(len(bl) * 40 * 1.45)
    total_h = 96 + 44 + th + 44 + 12 + 44 + bh
    top, bottom = PAD + 90, H - PAD - 70
    y = top + (bottom - top - total_h) // 2
    d.rectangle([PAD, y, PAD + 96, y + 96], fill=NAVY)
    d.text((PAD + 48, y + 50), f"{idx:02d}", font=F(CX, 64), fill=accent, anchor="mm")
    lf = F(CB, 36)
    tracked(d, (PAD + 96 + 24, y + 30), s["label"].upper(), lf, SLATE, 3)
    y += 96 + 44
    y = draw_lines(d, PAD, y, tl, tf, ts, 0.98) + 44
    y = bar(d, y, accent) + 44
    draw_lines(d, PAD, y, bl, body_f, 40, 1.45)
    footer(d, spec, SLATE, NAVY, "Próximo")
    return im


def slide_compare(s, spec, accent, idx, total):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    header(d, spec, idx, total, MUTED, MUTED)
    maxw = W - 2 * PAD
    words = words_of(s["title"], accent, CREAM)
    words = [(w.upper(), c) for w, c in words]
    tf, tl, ts, th = fit(d, words, CX, 112, 70, maxw, 360, 0.98)
    panels = []
    pw = maxw - 88
    bf = F(BR, 34)
    bfm = F(BM, 34)
    for i, p in enumerate(s["panels"]):
        fnt = bf if i == 0 else bfm
        col = SOFT2 if i == 0 else NAVY
        ln = wrap(d, plain(p["body"], col), fnt, pw)
        ph = 40 + int(34 * 1.2) + 14 + int(len(ln) * 34 * 1.4) + 40
        panels.append((p, ln, fnt, ph))
    total_h = th + 64 + sum(p[3] for p in panels) + 28 * (len(panels) - 1)
    top, bottom = PAD + 90, H - PAD - 70
    y = top + (bottom - top - total_h) // 2
    y = draw_lines(d, PAD, y, tl, tf, ts, 0.98) + 64
    for i, (p, ln, fnt, ph) in enumerate(panels):
        bg = PANEL if i == 0 else accent
        lc = CREAM if i == 0 else NAVY
        d.rectangle([PAD, y, W - PAD, y + ph], fill=bg)
        tracked(d, (PAD + 44, y + 40), p["label"].upper(), F(CX, 34), lc, 3)
        draw_lines(d, PAD + 44, y + 40 + int(34 * 1.2) + 14, ln, fnt, 34, 1.4)
        y += ph + 28
    footer(d, spec, MUTED, CREAM, "Próximo", accent)
    return im


def slide_cta(s, spec, accent, idx, total):
    im = Image.new("RGB", (W, H), accent)
    d = ImageDraw.Draw(im)
    header(d, spec, idx, total, NAVY, NAVY)
    maxw = W - 2 * PAD
    title = [(w.upper(), NAVY) for w in s["title"].split()]
    tf, tl, ts, th = fit(d, title, CX, 150, 80, maxw, 420, 0.95)
    body_f = F(BM, 40)
    bl = wrap(d, plain(s["body"], NAVY), body_f, 860)
    bh = int(len(bl) * 40 * 1.45)
    btn_f = F(CX, 54)
    btxt = s["button"].upper()
    bw = tracked_w(d, btxt, btn_f, 2)
    btn_w, btn_h = int(bw) + 44 + 48 + 24 + 44, 120
    total_h = th + 68 + bh + 52 + btn_h
    top, bottom = PAD + 90, H - PAD - 130
    y = top + (bottom - top - total_h) // 2
    y = draw_lines(d, PAD, y, tl, tf, ts, 0.95) + 68
    y = draw_lines(d, PAD, y, bl, body_f, 40, 1.45) + 52
    d.rectangle([PAD, y, PAD + btn_w, y + btn_h], fill=NAVY)
    ix, iy = PAD + 44, y + 36
    d.rounded_rectangle([ix, iy, ix + 48, iy + 38], radius=10, outline=accent, width=3)
    d.polygon([(ix + 10, iy + 37), (ix + 10, iy + 52), (ix + 24, iy + 38)], fill=accent)
    tracked(d, (ix + 48 + 24, y + 28), btxt, btn_f, CREAM, 2)
    # rodapé
    ff = F(BR, 26)
    yy = H - PAD - 34 - 40
    d.text((PAD, yy), spec["handle"], font=F(BS, 28), fill=NAVY)
    note = wrap(d, plain(s["note"], NAVY), ff, maxw)
    draw_lines(d, PAD, yy + 40, note, ff, 26, 1.35)
    return im


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    accent = hexrgb(spec.get("accent", "#F5B301"))
    slides = spec["slides"]
    n = len(slides)
    for i, s in enumerate(slides, 1):
        t = s["type"]
        if t == "cover":
            im = slide_cover(s, spec, accent)
        elif t == "content":
            im = slide_content(s, spec, accent, i, n)
        elif t == "compare":
            im = slide_compare(s, spec, accent, i, n)
        elif t == "cta":
            im = slide_cta(s, spec, accent, i, n)
        else:
            raise SystemExit(f"tipo de slide desconhecido: {t}")
        path = os.path.join(out, f"{spec.get('slug', 'post')}-{i:02d}.png")
        im.save(path, "PNG", optimize=True)
        print(path)


if __name__ == "__main__":
    main()
