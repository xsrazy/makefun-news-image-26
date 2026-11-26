#!/usr/bin/env python3
"""THE WORLD TODAY - front page for Thursday 26 November 2026.

Draws a newspaper front page summarising the day's world news as a
single 1024x1024 PNG. Everything is painted from scratch with Pillow:
no downloaded assets, no network calls, no randomness and no clock
reads, so two runs produce byte-identical output.

Run:  python3 main.py
Out:  $MAKEFUN_OUTPUT_DIR/entry.png  (or /output/entry.png)
"""

import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)   # warm newsprint
INK = (16, 16, 16)        # near-black headline ink
FLAG_RED = (185, 28, 28)  # kicker red / lead accent bar
NAVY = (30, 58, 95)       # dateline, navy accent bars, ticker fill
GREY = (96, 94, 88)       # standfirst and footer grey
SKY = (214, 228, 240)     # globe fill
BODY_INK = (28, 28, 28)   # body copy

# ---------------------------------------------------------------- typefaces
FONT_DIR = "/usr/share/fonts/truetype"
FACES = {
    "serif_b": os.path.join(FONT_DIR, "dejavu", "DejaVuSerif-Bold.ttf"),
    "serif_i": os.path.join(FONT_DIR, "noto", "NotoSerif-Italic.ttf"),
    "sans": os.path.join(FONT_DIR, "dejavu", "DejaVuSans.ttf"),
    "sans_b": os.path.join(FONT_DIR, "dejavu", "DejaVuSans-Bold.ttf"),
}

PAGE = 1024
GUTTER = 36          # content inset from the page edge
RIGHT = PAGE - GUTTER


def load_face(kind, size):
    """Return a truetype face, falling back to Pillow's built-in font."""
    try:
        return ImageFont.truetype(FACES[kind], size)
    except (OSError, KeyError):
        return ImageFont.load_default()


def shrink_to_fit(text, kind, start, max_width):
    """Largest face size at or below `start` whose text fits `max_width`."""
    size = start
    while size > 8:
        face = load_face(kind, size)
        if face.getlength(text) <= max_width:
            return face
        size -= 1
    return load_face(kind, 8)


def wrap_lines(text, face, max_width):
    """Greedy word wrap; returns a list of lines that fit `max_width`."""
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if face.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class FrontPage:
    """Owns the canvas and paints every element of the front page."""

    def __init__(self):
        self.sheet = Image.new("RGB", (PAGE, PAGE), PAPER)
        self.pen = ImageDraw.Draw(self.sheet)

    # ------------------------------------------------------------ helpers
    def centred(self, text, y, kind, size, colour):
        face = load_face(kind, size)
        self.pen.text((PAGE // 2, y), text, font=face, fill=colour,
                      anchor="ma")

    def left(self, text, x, y, kind, size, colour):
        face = load_face(kind, size)
        self.pen.text((x, y), text, font=face, fill=colour, anchor="la")

    def paragraph(self, text, x, y, width, kind, size, leading, colour):
        """Wrapped body copy; returns the y just below the last line."""
        face = load_face(kind, size)
        cursor = y
        for line in wrap_lines(text, face, width):
            self.pen.text((x, cursor), line, font=face, fill=colour,
                          anchor="la")
            cursor += leading
        return cursor

    def frame(self):
        """Double black border framing the whole page."""
        self.pen.rectangle((10, 10, PAGE - 11, PAGE - 11), outline=INK,
                           width=2)
        self.pen.rectangle((20, 20, PAGE - 21, PAGE - 21), outline=INK,
                           width=1)

    # ------------------------------------------------------------ masthead
    def nameplate(self):
        self.centred("THE WORLD IN ONE IMAGE", 42, "sans_b", 21, FLAG_RED)
        face = shrink_to_fit("THE WORLD TODAY", "serif_b", 92,
                             RIGHT - GUTTER)
        self.pen.text((PAGE // 2, 64), "THE WORLD TODAY", font=face,
                      fill=INK, anchor="ma")
        self.pen.line((GUTTER, 160, RIGHT, 160), fill=INK, width=3)
        self.pen.line((GUTTER, 167, RIGHT, 167), fill=INK, width=1)
        self.centred("THURSDAY, 26 NOVEMBER 2026", 178, "sans_b", 27, NAVY)
        self.centred("Five stories that defined the day, on one page",
                     208, "serif_i", 20, GREY)

    # ------------------------------------------------------------ artwork
    def globe_and_bars(self, cx, cy, radius):
        """Wireframe globe with a small rising bar chart beneath it."""
        self.pen.ellipse((cx - radius, cy - radius, cx + radius,
                          cy + radius), fill=SKY, outline=NAVY, width=3)
        self.pen.ellipse((cx - 22, cy - radius, cx + 22, cy + radius),
                         outline=NAVY, width=2)
        self.pen.ellipse((cx - radius, cy - 18, cx + radius, cy + 18),
                         outline=NAVY, width=2)
        self.pen.line((cx - radius, cy, cx + radius, cy), fill=NAVY,
                      width=2)
        base = cy + radius + 26
        widths = (26, 26, 26)
        heights = (16, 30, 44)
        start_x = cx - (sum(widths) + 16) // 2
        x = start_x
        for w, h in zip(widths, heights):
            self.pen.rectangle((x, base - h, x + w, base), fill=FLAG_RED)
            x += w + 8

    # ------------------------------------------------------------ stories
    def lead_story(self, story):
        x0, y0, x1, y1 = GUTTER, 232, RIGHT, 470
        self.pen.rectangle((x0, y0, x1, y1), outline=INK, width=2)
        self.pen.rectangle((x0, y0, x1, y0 + 9), fill=FLAG_RED)
        self.left(story["tag"], x0 + 16, y0 + 20, "sans_b", 20, FLAG_RED)
        cursor = y0 + 44
        for line in story["headline"]:
            self.left(line, x0 + 16, cursor, "serif_b", 50, INK)
            cursor += 50
        self.paragraph(story["body"], x0 + 16, cursor + 10, 640,
                       "sans", 21, 27, BODY_INK)
        self.globe_and_bars(848, 330, 60)

    def story_card(self, box, story):
        """One of the four smaller stories in the two-by-two grid."""
        x0, y0, x1, y1 = box
        self.pen.rectangle((x0, y0, x1, y1), outline=INK, width=2)
        self.pen.rectangle((x0, y0, x1, y0 + 7), fill=story["accent"])
        self.left(story["tag"], x0 + 16, y0 + 14, "sans_b", 19,
                  story["accent"])
        cursor = y0 + 40
        for line in story["headline"]:
            self.left(line, x0 + 16, cursor, "serif_b", 34, INK)
            cursor += 42
        self.paragraph(story["body"], x0 + 16, cursor + 8, x1 - x0 - 32,
                       "sans", 19, 25, BODY_INK)

    # ------------------------------------------------------------ footer
    def ticker_and_sources(self):
        self.pen.rectangle((GUTTER, 922, RIGHT, 964), fill=NAVY)
        ticker = ("ALSO TODAY: Thanksgiving in the US | Record double "
                  "century at 15 | N. Korea expels Swiss envoy | "
                  "Hera's Dimorphos close-ups")
        face = shrink_to_fit(ticker, "sans_b", 19, RIGHT - GUTTER - 16)
        self.pen.text((PAGE // 2, 943), ticker, font=face,
                      fill=(255, 255, 255), anchor="mm")
        self.centred("Sources: Reuters, AP, BBC, AFP. All stories in "
                     "Thursday's editions, 26 November 2026.",
                     974, "sans", 15, GREY)

    # ------------------------------------------------------------ assembly
    def build(self):
        self.frame()
        self.nameplate()
        self.lead_story(LEAD)
        grid = [
            ((GUTTER, 484, 502, 692), GRID[0]),
            ((522, 484, RIGHT, 692), GRID[1]),
            ((GUTTER, 706, 502, 908), GRID[2]),
            ((522, 706, RIGHT, 908), GRID[3]),
        ]
        for box, story in grid:
            self.story_card(box, story)
        self.ticker_and_sources()
        return self.sheet


# ------------------------------------------------------------------- copy
LEAD = {
    "tag": "TRADE WAR RETURNS",
    "headline": ["TRUMP'S NEW TARIFFS", "HIT 14 PARTNERS"],
    "body": ("Washington unveils Section 301 duties of up to 40% on "
             "China, Japan, the EU and 11 others; China capped at 20%, "
             "the EU at 15%. Markets fall."),
}

GRID = [
    {
        "tag": "CAIRO DISASTER",
        "accent": FLAG_RED,
        "headline": ["30 KILLED IN CAIRO"],
        "body": ("A fuel tanker overturns on Cairo's ring road and "
                 "bursts into flames, killing at least 30 people and "
                 "injuring 25, Egyptian officials say."),
    },
    {
        "tag": "WAR IN UKRAINE",
        "accent": NAVY,
        "headline": ["RUSSIA'S WAR DEAD", "NEAR 500,000"],
        "body": ("Moscow's own figures show nearly 500,000 people lost "
                 "in the Ukraine war, the BBC reports. Kyiv says it hit "
                 "five Russian jets."),
    },
    {
        "tag": "BANGLADESH",
        "accent": FLAG_RED,
        "headline": ["GARMENT PAY UP 36%"],
        "body": ("Bangladesh raises garment workers' minimum wage to "
                 "17,000 taka a month after weeks of protests that shut "
                 "factories; workers had wanted double."),
    },
    {
        "tag": "COLOMBIA",
        "accent": NAVY,
        "headline": ["10 YEARS OF PEACE"],
        "body": ("Colombia marks a decade since its historic peace "
                 "accord, as the UN chief praises progress and warns "
                 "unfinished commitments remain."),
    },
]


def destination():
    """Output folder: $MAKEFUN_OUTPUT_DIR, else /output."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def main():
    page = FrontPage().build()
    folder = destination()
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, "entry.png")
    page.save(target, format="PNG")
    try:
        os.chmod(target, 0o644)
    except OSError:
        pass


if __name__ == "__main__":
    main()
