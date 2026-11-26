#!/usr/bin/env python3
"""make.fun bounty news-image-20261126.

Sum up 26 November 2026 world news in one image.

Draws a newspaper front page (1024x1024 PNG) with PIL. No network,
no randomness, no timestamps: two runs write byte-identical files.
Writes to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""
import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MARGIN = 36
CONTENT_W = W - 2 * MARGIN

PAPER = (247, 243, 232)
INK = (17, 17, 17)
RED = (185, 28, 28)
NAVY = (30, 58, 95)
GREY = (90, 86, 76)
LIGHT_GREY = (210, 204, 188)
CARD = (255, 252, 244)
GOLD = (176, 141, 58)

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap, returns list of lines that fit max_w."""
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for word in words[1:]:
            trial = cur + " " + word
            if draw.textlength(trial, font=fnt) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def draw_wrapped(draw, text, fnt, x, y, max_w, fill, spacing=4):
    lines = wrap(draw, text, fnt, max_w)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + spacing
    return y


def centered(draw, text, fnt, cx, y, fill):
    w = draw.textlength(text, font=fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)
    return y + fnt.size


def draw_globe(draw, cx, cy, r, line_col, fill_col):
    """Simple line-art globe: circle, meridians, parallels."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill_col,
                 outline=line_col, width=4)
    draw.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r],
                 outline=line_col, width=3)
    draw.line([cx - r, cy, cx + r, cy], fill=line_col, width=3)
    draw.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 0, 180,
             fill=line_col, width=3)
    draw.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 180, 360,
             fill=line_col, width=3)


def draw_bars(draw, x, y, w, h, fill):
    """Three rising bars, a tiny trade chart."""
    bw = w // 4
    heights = [h // 3, (2 * h) // 3, h]
    for i, bh in enumerate(heights):
        bx = x + i * (bw + 6)
        draw.rectangle([bx, y + h - bh, bx + bw, y + h], fill=fill)


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # --- outer frame ---
    d.rectangle([14, 14, W - 15, H - 15], outline=INK, width=3)
    d.rectangle([22, 22, W - 23, H - 23], outline=GOLD, width=1)

    # --- masthead (explicit y positions so nothing runs off the page) ---
    f_kicker = font(SANS_BOLD, 20)
    centered(d, "THE WORLD IN ONE IMAGE", f_kicker, W // 2, 38, RED)
    f_title = font(SERIF_BOLD, 74)
    centered(d, "THE WORLD TODAY", f_title, W // 2, 66, INK)
    d.line([MARGIN, 150, W - MARGIN, 150], fill=INK, width=3)
    d.line([MARGIN, 158, W - MARGIN, 158], fill=INK, width=1)
    f_date = font(SANS_BOLD, 24)
    centered(d, "THURSDAY, 26 NOVEMBER 2026", f_date, W // 2, 170, NAVY)
    f_sub = font(SANS, 18)
    centered(d, "Five stories that defined the day, on one page",
             f_sub, W // 2, 200, GREY)
    y = 222

    # --- lead story ---
    lead_top = y
    lead_h = 248
    lead_bot = lead_top + lead_h
    d.rectangle([MARGIN, lead_top, W - MARGIN, lead_bot],
                fill=CARD, outline=INK, width=2)
    d.rectangle([MARGIN, lead_top, W - MARGIN, lead_top + 8],
                fill=RED)
    lx = MARGIN + 24
    ly = lead_top + 22
    f_lead_kick = font(SANS_BOLD, 21)
    d.text((lx, ly), "TRADE WAR RETURNS", font=f_lead_kick, fill=RED)
    ly += 32
    f_lead_head = font(SERIF_BOLD, 46)
    d.text((lx, ly), "TRUMP'S NEW TARIFFS", font=f_lead_head, fill=INK)
    ly += 52
    d.text((lx, ly), "HIT 14 PARTNERS", font=f_lead_head, fill=INK)
    ly += 54
    f_lead_deck = font(SANS, 20)
    draw_wrapped(d, "Washington unveils Section 301 duties of up to "
                 "40% on China, Japan, the EU and 11 others; China "
                 "capped at 20%, the EU at 15%. Markets fall.",
                 f_lead_deck, lx, ly, 600, INK, spacing=4)
    # globe + bars art on the right of the lead box
    gx, gy = 830, lead_top + 112
    draw_globe(d, gx, gy, 66, NAVY, (226, 234, 244))
    draw_bars(d, gx - 52, gy + 72, 104, 44, RED)

    # --- 2x2 grid of supporting stories ---
    stories = [
        ("CAIRO DISASTER", "30 KILLED IN CAIRO",
         "A fuel tanker overturns on Cairo's ring road and bursts "
         "into flames, killing at least 30 people and injuring 25, "
         "Egyptian officials say.", RED),
        ("WAR IN UKRAINE", "RUSSIA'S WAR DEAD\nNEAR 500,000",
         "Moscow's own figures show nearly 500,000 people lost in "
         "the Ukraine war, the BBC reports. Kyiv says it hit five "
         "Russian jets.", NAVY),
        ("BANGLADESH", "GARMENT PAY UP 36%",
         "Bangladesh raises garment workers' minimum wage to 17,000 "
         "taka a month after weeks of protests that shut factories; "
         "workers had wanted double.", RED),
        ("COLOMBIA", "10 YEARS OF PEACE",
         "Colombia marks a decade since its historic peace accord, "
         "as the UN chief praises progress and warns unfinished "
         "commitments remain.", NAVY),
    ]
    grid_top = lead_bot + 16
    cell_w = (CONTENT_W - 16) // 2
    cell_h = 200
    f_kick = font(SANS_BOLD, 18)
    f_head = font(SERIF_BOLD, 30)
    f_body = font(SANS, 19)
    for i, (kick, head, body, accent) in enumerate(stories):
        col = i % 2
        row = i // 2
        x0 = MARGIN + col * (cell_w + 16)
        y0 = grid_top + row * (cell_h + 16)
        d.rectangle([x0, y0, x0 + cell_w, y0 + cell_h],
                    fill=CARD, outline=INK, width=2)
        d.rectangle([x0, y0, x0 + cell_w, y0 + 7], fill=accent)
        tx = x0 + 18
        ty = y0 + 18
        d.text((tx, ty), kick, font=f_kick, fill=accent)
        ty += 28
        head_lines = wrap(d, head, f_head, cell_w - 36)[:2]
        for line in head_lines:
            d.text((tx, ty), line, font=f_head, fill=INK)
            ty += 36
        ty += 6
        draw_wrapped(d, body, f_body, tx, ty, cell_w - 36, INK,
                     spacing=4)

    # --- bottom ticker ---
    tick_top = grid_top + 2 * cell_h + 16 + 14
    tick_h = 46
    d.rectangle([MARGIN, tick_top, W - MARGIN, tick_top + tick_h],
                fill=NAVY)
    ticker = ("ALSO TODAY: Thanksgiving in the US | Record double "
              "century at 15 | N. Korea expels Swiss envoy | Hera's "
              "Dimorphos close-ups")
    tick_size = 20
    while tick_size > 12:
        f_tick = font(SANS_BOLD, tick_size)
        if d.textlength(ticker, font=f_tick) <= CONTENT_W - 24:
            break
        tick_size -= 1
    tw = d.textlength(ticker, font=f_tick)
    d.text(((W - tw) / 2, tick_top + (tick_h - tick_size) / 2 - 2),
           ticker, font=f_tick, fill=(255, 255, 255))

    # --- footer ---
    f_foot = font(SANS, 15)
    centered(d, "Sources: Reuters, AP, BBC, AFP. All stories in "
             "Thursday's editions, 26 November 2026.", f_foot, W // 2,
             tick_top + tick_h + 10, GREY)

    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    img = build()
    img.save(out_path, format="PNG")
    try:
        os.chmod(out_path, 0o644)
    except OSError:
        pass
    print("wrote", out_path)


if __name__ == "__main__":
    main()
