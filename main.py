#!/usr/bin/env python3
"""THE WORLD TODAY - newspaper front page, Thursday 26 November 2026.

Pure standard library only: no Pillow, no third-party packages, no
network, no clock, no randomness. The program rasterizes a 1024x1024
RGB canvas by hand, encodes it as PNG by hand (signature, IHDR, IDAT
with zlib-compressed scanlines, IEND, CRC32), and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (fallback /output/entry.png).

Two runs produce byte-identical output.
"""

import binascii
import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# Palette.
PAPER = (245, 240, 225)   # warm newsprint cream
INK = (17, 17, 17)        # near-black
RED = (178, 34, 34)       # brick red for kickers and rules
NAVY = (31, 58, 95)       # dark navy for dateline and ticker
GRAY = (110, 105, 92)     # muted gray for the footer line
WHITE = (255, 255, 255)
GLOBE_BLUE = (205, 220, 235)  # pale fill for the globe
GLOBE_LINE = (31, 58, 95)

# ---------------------------------------------------------------------------
# 5x7 bitmap font, defined from scratch in this file.
# Each glyph is 7 rows of 5 characters; '#' is a set pixel.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}

CHAR_W = 6  # glyph cell width in font units (5 pixels + 1 spacing)
CHAR_H = 7


def text_width(text, scale):
    """Pixel width of text at the given scale."""
    if not text:
        return 0
    return len(text) * CHAR_W * scale - scale


# ---------------------------------------------------------------------------
# Canvas: a flat RGB bytearray, W x H x 3.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set_pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def rect_outline(self, x, y, w, h, color, thick=1):
        self.hline(x, y, w, color, thick)
        self.hline(x, y + h - thick, w, color, thick)
        self.vline(x, y, h, color, thick)
        self.vline(x + w - thick, y, h, color, thick)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, 1 pixel wide."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, thick=1, fill=None):
        """Circle outline (midpoint), optionally filled first."""
        if fill is not None:
            for yy in range(-r, r + 1):
                half = int(math.sqrt(max(0, r * r - yy * yy)))
                self.hline(cx - half, cy + yy, half * 2 + 1, fill)
        for t in range(thick):
            rr = r - t
            x = 0
            y = rr
            d = 1 - rr
            while x <= y:
                for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                               (cx + x, cy - y), (cx - x, cy - y),
                               (cx + y, cy + x), (cx - y, cy + x),
                               (cx + y, cy - x), (cx - y, cy - x)):
                    self.set_pixel(px, py, color)
                if d < 0:
                    d += 2 * x + 3
                else:
                    d += 2 * (x - y) + 5
                    y -= 1
                x += 1

    def ellipse(self, cx, cy, rx, ry, color):
        """Ellipse outline by parametric sampling."""
        steps = max(64, int(2 * math.pi * max(rx, ry)))
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            self.set_pixel(int(round(cx + rx * math.cos(a))),
                           int(round(cy + ry * math.sin(a))), color)

    # -- text ---------------------------------------------------------------
    def draw_char(self, ch, x, y, scale, color, bold=False):
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT["?"]
        thick = max(1, scale // 4) if bold else 0
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit != "1":
                    continue
                bx = x + gx * scale
                by = y + gy * scale
                self.fill_rect(bx, by, scale, scale, color)
                if thick:
                    self.fill_rect(bx + thick, by, scale, scale, color)

    def draw_text(self, text, x, y, scale, color, bold=False):
        cx = x
        for ch in text:
            self.draw_char(ch, cx, y, scale, color, bold)
            cx += CHAR_W * scale
        return cx

    def draw_text_centered(self, text, cx, y, scale, color, bold=False):
        x = cx - text_width(text, scale) // 2
        self.draw_text(text, x, y, scale, color, bold)
        return x

    def wrap_lines(self, text, max_width, scale):
        """Greedy word wrap; returns a list of lines fitting max_width."""
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split(" ")
            cur = ""
            for word in words:
                trial = word if not cur else cur + " " + word
                if text_width(trial, scale) <= max_width:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines


# ---------------------------------------------------------------------------
# PNG encoder, written by hand: signature, IHDR, IDAT, IEND, CRC32.
# ---------------------------------------------------------------------------
def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    raw = bytearray()
    row_len = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter type 0: none
        start = y * row_len
        raw += canvas.buf[start:start + row_len]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------------------
# Page layout: a newspaper front page, 1024x1024.
# ---------------------------------------------------------------------------
def draw_globe(cv, cx, cy, r):
    """Wireframe globe with red bar chart beneath it."""
    cv.circle(cx, cy, r, GLOBE_LINE, thick=3, fill=GLOBE_BLUE)
    # Vertical meridians: ellipses with shrinking horizontal radius.
    for rx in (r * 2 // 3, r // 3):
        cv.ellipse(cx, cy, rx, r - 2, GLOBE_LINE)
    # Horizontal parallels.
    cv.ellipse(cx, cy, r - 2, r // 3, GLOBE_LINE)
    cv.hline(cx - r + 3, cy, (r - 3) * 2, GLOBE_LINE, thick=1)
    # Red bar chart under the globe.
    base_y = cy + r + 12
    bars = (14, 26, 40)
    bw = 22
    gap = 8
    x = cx - (len(bars) * bw + (len(bars) - 1) * gap) // 2
    for hgt in bars:
        cv.fill_rect(x, base_y - hgt, bw, hgt, RED)
        x += bw + gap


def draw_story_box(cv, x, y, w, h, rule_color, kicker, headline_lines,
                   body, head_scale=4):
    cv.rect_outline(x, y, w, h, INK, thick=2)
    cv.fill_rect(x, y, w, 6, rule_color)
    pad = 16
    inner_w = w - 2 * pad
    cy = y + 16
    cv.draw_text(kicker, x + pad, cy, 2, rule_color, bold=True)
    cy += 26
    for line in headline_lines:
        cv.draw_text(line, x + pad, cy, head_scale, INK, bold=True)
        cy += head_scale * CHAR_H + 8
    cy += 4
    for line in cv.wrap_lines(body, inner_w, 2):
        cv.draw_text(line, x + pad, cy, 2, INK)
        cy += 20


def draw_page():
    cv = Canvas(W, H, PAPER)

    # Double outer frame.
    cv.rect_outline(10, 10, W - 20, H - 20, INK, thick=3)
    cv.rect_outline(18, 18, W - 36, H - 36, INK, thick=1)

    # Kicker above the masthead.
    cv.draw_text_centered("THE WORLD IN ONE IMAGE", W // 2, 34, 3, RED,
                          bold=True)

    # Masthead.
    cv.draw_text_centered("THE WORLD TODAY", W // 2, 62, 9, INK, bold=True)

    # Double rule under the masthead.
    cv.hline(36, 140, W - 72, INK, thick=3)
    cv.hline(36, 146, W - 72, INK, thick=1)

    # Dateline and standfirst.
    cv.draw_text_centered("THURSDAY, 26 NOVEMBER 2026", W // 2, 158, 3,
                          NAVY, bold=True)
    cv.draw_text_centered("Five stories that defined the day, on one page",
                          W // 2, 186, 2, GRAY)

    # Red rule above the lead story.
    cv.hline(36, 212, W - 72, RED, thick=5)

    # ---- Lead story -------------------------------------------------------
    lx, ly, lw, lh = 36, 222, W - 72, 226
    cv.rect_outline(lx, ly, lw, lh, INK, thick=2)
    cv.draw_text("TRADE WAR RETURNS", lx + 16, ly + 14, 2, RED, bold=True)
    cv.draw_text("TRUMP'S NEW TARIFFS", lx + 16, ly + 44, 6, INK, bold=True)
    cv.draw_text("HIT 14 PARTNERS", lx + 16, ly + 96, 6, INK, bold=True)
    lead_body = ("Washington unveils Section 301 duties of up to 40% on "
                 "China, Japan, the EU and 11 others; China capped at 20%, "
                 "the EU at 15%. Markets fall.")
    cy = ly + 152
    for line in cv.wrap_lines(lead_body, 690, 2):
        cv.draw_text(line, lx + 16, cy, 2, INK)
        cy += 20
    draw_globe(cv, 862, 316, 62)

    # ---- Second row -------------------------------------------------------
    box_w = (W - 72 - 24) // 2
    row2_y = 460
    box_h = 208
    draw_story_box(
        cv, 36, row2_y, box_w, box_h, RED, "CAIRO DISASTER",
        ["30 KILLED IN CAIRO"],
        "A fuel tanker overturns on Cairo's ring road and bursts into "
        "flames, killing at least 30 people and injuring 25, Egyptian "
        "officials say.")
    draw_story_box(
        cv, 36 + box_w + 24, row2_y, box_w, box_h, NAVY, "WAR IN UKRAINE",
        ["RUSSIA'S WAR DEAD", "NEAR 500,000"],
        "Moscow's own figures show nearly 500,000 people lost in the "
        "Ukraine war, the BBC reports. Kyiv says it hit five Russian jets.")

    # ---- Third row --------------------------------------------------------
    row3_y = 680
    draw_story_box(
        cv, 36, row3_y, box_w, box_h, RED, "BANGLADESH",
        ["GARMENT PAY UP 36%"],
        "Bangladesh raises garment workers' minimum wage to 17,000 taka "
        "a month after weeks of protests that shut factories; workers "
        "had wanted double.")
    draw_story_box(
        cv, 36 + box_w + 24, row3_y, box_w, box_h, NAVY, "COLOMBIA",
        ["10 YEARS OF PEACE"],
        "Colombia marks a decade since its historic peace accord, as the "
        "UN chief praises progress and warns unfinished commitments "
        "remain.")

    # ---- Ticker -----------------------------------------------------------
    tx, ty, tw, th = 36, 900, W - 72, 64
    cv.fill_rect(tx, ty, tw, th, NAVY)
    cv.draw_text("ALSO TODAY: Thanksgiving in the US | Record double "
                 "century at 15", tx + 14, ty + 10, 2, WHITE, bold=True)
    cv.draw_text("N. Korea expels Swiss envoy | Hera's Dimorphos close-ups",
                 tx + 14, ty + 36, 2, WHITE, bold=True)

    # ---- Footer -----------------------------------------------------------
    cv.draw_text_centered(
        "Sources: Reuters, AP, BBC, AFP. Thursday's editions, 26 November "
        "2026.", W // 2, 978, 2, GRAY)

    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    out_path = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(draw_page())
    with open(out_path, "wb") as fh:
        fh.write(png)
    # Best-effort only: never fail the run over permissions, and never
    # touch the permissions of the output directory itself.
    try:
        os.chmod(out_path, 0o644)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
