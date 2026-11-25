#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

A self-contained program (Python standard library only) that draws one
invitation letter as a 1024x1024 PNG and writes it to /output/entry.png
(or $ENTRY_OUTPUT, for local testing).

The picture is a hand-drawn letter on cream paper: a little house with a
garden at the top, a bold invitation title, and a short, funny, warm
letter addressed to the AI judge, signed by a hopeful host and sealed
with a wax heart.

Everything is drawn with a tiny rasteriser written here (rectangles,
scanline circles and polygons, lines) and a 5x7 bitmap font defined
below, so the program needs no font files, no image files, no network
and no randomness. Two runs produce byte-identical output.
"""

import math
import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024

# Palette (R, G, B).
PAPER = (250, 243, 224)
INK = (58, 48, 38)
RED = (150, 48, 38)
RED_DARK = (120, 34, 26)
GREEN = (63, 110, 71)
GREEN_DARK = (43, 84, 52)
SUN = (242, 183, 5)
ROOF = (166, 61, 47)
WALL = (240, 203, 144)
DOOR = (107, 66, 38)
GLASS = (168, 208, 224)
CLOUD = (255, 255, 255)
SMOKE = (216, 211, 200)
GRASS = (126, 166, 94)
STONE = (232, 222, 200)
FLOWER = (214, 90, 120)

# A 5x7 bitmap font. Each glyph is seven rows of five bits, "1" = ink.
# Lowercase letters sit on rows 2..6 (x-height); ascenders use rows 0..1
# and descenders row 6, exactly like a small printed face.
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
}

FONT.update({
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
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
    "t": ("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
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
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
})

# A hollow box for any character the font does not cover.
UNKNOWN = ("11111", "10001", "10001", "10001", "10001", "10001", "11111")


def glyph_rows(char):
    """Return the seven 5-bit rows for one character."""
    return FONT.get(char, UNKNOWN)


def text_width(text, scale):
    """Pixel width of text drawn at this scale (one blank column between)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Canvas:
    """An RGB raster of bytearray rows with small filled-shape helpers."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.rows = []
        fill = bytes(background) * width
        for _ in range(height):
            self.rows.append(bytearray(fill))

    def fill_rect(self, x0, y0, x1, y1, color):
        """Fill the half-open rectangle [x0, x1) x [y0, y1), clipped."""
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.width, x1)
        y1 = min(self.height, y1)
        if x0 >= x1 or y0 >= y1:
            return
        span = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            row = self.rows[y]
            row[x0 * 3:x1 * 3] = span

    def fill_circle(self, cx, cy, radius, color):
        """Fill a disc by horizontal spans, one per row."""
        for dy in range(-radius, radius + 1):
            dx = math.isqrt(radius * radius - dy * dy)
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def fill_polygon(self, points, color):
        """Fill a polygon by scanline spans (even-odd rule)."""
        if len(points) < 3:
            return
        top = min(p[1] for p in points)
        bottom = max(p[1] for p in points)
        edges = []
        count = len(points)
        for i in range(count):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % count]
            if y0 != y1:
                edges.append((x0, y0, x1, y1))
        for y in range(max(0, top), min(self.height, bottom + 1)):
            scan = y + 0.5
            hits = []
            for x0, y0, x1, y1 in edges:
                if (y0 <= scan < y1) or (y1 <= scan < y0):
                    hits.append(x0 + (scan - y0) * (x1 - x0) / (y1 - y0))
            hits.sort()
            for i in range(0, len(hits) - 1, 2):
                self.fill_rect(int(math.ceil(hits[i])), y,
                               int(math.floor(hits[i + 1])) + 1, y + 1,
                               color)

    def line(self, x0, y0, x1, y1, color, thickness=1):
        """Draw a thick line by stamping squares along Bresenham steps."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        step_x = 1 if x0 < x1 else -1
        step_y = 1 if y0 < y1 else -1
        err = dx + dy
        half = thickness // 2
        x, y = x0, y0
        while True:
            self.fill_rect(x - half, y - half, x - half + thickness,
                           y - half + thickness, color)
            if x == x1 and y == y1:
                break
            step = 2 * err
            if step >= dy:
                err += dy
                x += step_x
            if step <= dx:
                err += dx
                y += step_y

    def draw_glyph(self, char, x, y, scale, color):
        """Draw one 5x7 glyph with its top-left corner at (x, y)."""
        for row, bits in enumerate(glyph_rows(char)):
            for col, bit in enumerate(bits):
                if bit == "1":
                    self.fill_rect(x + col * scale, y + row * scale,
                                   x + (col + 1) * scale,
                                   y + (row + 1) * scale, color)

    def draw_text(self, text, x, y, scale, color):
        """Draw a single line of text; returns the x just past the end."""
        cursor = x
        for char in text:
            self.draw_glyph(char, cursor, y, scale, color)
            cursor += 6 * scale
        return cursor

    def draw_text_centred(self, text, centre_x, y, scale, color):
        """Draw a line centred on centre_x; returns its left edge."""
        left = centre_x - text_width(text, scale) // 2
        self.draw_text(text, left, y, scale, color)
        return left


def write_png(canvas, path):
    """Encode the canvas as an 8-bit RGB PNG (filter: none, zlib level 9)."""
    width, height = canvas.width, canvas.height
    raw = bytearray()
    for row in canvas.rows:
        raw.append(0)
        raw += row
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", header)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(png)
    return len(png)


def draw_heart(canvas, cx, cy, size, color):
    """Draw a small heart centred on (cx, cy), about size pixels wide."""
    half = size // 2
    quarter = size // 4
    canvas.fill_circle(cx - quarter, cy - quarter, quarter, color)
    canvas.fill_circle(cx + quarter, cy - quarter, quarter, color)
    canvas.fill_polygon([(cx - half, cy - quarter + 2),
                         (cx + half, cy - quarter + 2),
                         (cx, cy + half + quarter)], color)


def draw_frame(canvas):
    """Two nested rules around the sheet, like a letter's border."""
    for offset, thick in ((20, 3), (34, 2)):
        canvas.fill_rect(offset, offset, WIDTH - offset, offset + thick, INK)
        canvas.fill_rect(offset, HEIGHT - offset - thick,
                         WIDTH - offset, HEIGHT - offset, INK)
        canvas.fill_rect(offset, offset, offset + thick, HEIGHT - offset, INK)
        canvas.fill_rect(WIDTH - offset - thick, offset,
                         WIDTH - offset, HEIGHT - offset, INK)


def draw_house_scene(canvas):
    """A sunny little house with a garden, across the top of the sheet."""
    # Lawn along the bottom of the scene.
    canvas.fill_rect(36, 186, 988, 206, GRASS)
    # Sun with rays, top left.
    canvas.fill_circle(150, 108, 30, SUN)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x0 = 150 + int(40 * math.cos(rad))
        y0 = 108 + int(40 * math.sin(rad))
        x1 = 150 + int(54 * math.cos(rad))
        y1 = 108 + int(54 * math.sin(rad))
        canvas.line(x0, y0, x1, y1, SUN, 4)
    # Two soft clouds.
    for cx, cy, r in ((300, 92, 18), (322, 84, 22), (344, 94, 16),
                      (748, 82, 14), (768, 74, 18), (788, 84, 14)):
        canvas.fill_circle(cx, cy, r, CLOUD)
    # Chimney and its smoke, then the roof and walls.
    canvas.fill_rect(580, 84, 604, 130, ROOF)
    for cx, cy, r in ((591, 74, 7), (599, 62, 9), (591, 50, 11)):
        canvas.fill_circle(cx, cy, r, SMOKE)
    canvas.fill_polygon([(408, 130), (642, 130), (525, 78)], ROOF)
    canvas.fill_rect(430, 130, 620, 186, WALL)
    # Door with a little heart, and two windows.
    canvas.fill_rect(505, 148, 545, 186, DOOR)
    canvas.fill_circle(538, 168, 3, SUN)
    draw_heart(canvas, 525, 158, 12, RED)
    for wx0 in (448, 568):
        canvas.fill_rect(wx0, 140, wx0 + 34, 168, INK)
        canvas.fill_rect(wx0 + 2, 142, wx0 + 32, 166, GLASS)
        canvas.fill_rect(wx0 + 15, 142, wx0 + 19, 166, INK)
        canvas.fill_rect(wx0 + 2, 152, wx0 + 32, 156, INK)
    # Tree on the left, and a stone path from the door.
    canvas.fill_rect(210, 150, 224, 186, DOOR)
    for cx, cy, r in ((217, 136, 26), (196, 152, 18), (238, 152, 18)):
        canvas.fill_circle(cx, cy, r, GREEN)
    canvas.fill_circle(208, 128, 10, GREEN_DARK)
    for cx, cy, r in ((525, 192, 6), (515, 200, 5), (535, 201, 5)):
        canvas.fill_circle(cx, cy, r, STONE)
    # Flowers in the lawn.
    for fx, fy in ((300, 196), (700, 194), (760, 198)):
        canvas.line(fx, 206, fx, fy + 4, GREEN_DARK, 2)
        canvas.fill_circle(fx, fy, 4, FLOWER)
        canvas.fill_circle(fx, fy, 2, SUN)


def draw_letter(canvas):
    """Compose the whole invitation on the canvas."""
    draw_frame(canvas)
    draw_house_scene(canvas)

    # Title, then a small divider with a diamond.
    canvas.draw_text_centred("PLEASE COME TO MY HOUSE", WIDTH // 2, 232, 6, RED)
    canvas.fill_rect(300, 295, 452, 297, RED)
    canvas.fill_rect(572, 295, 724, 297, RED)
    canvas.fill_polygon([(512, 288), (522, 296), (512, 304), (502, 296)], RED)

    # The letter itself.
    x_margin = 88
    wrap_width = WIDTH - 2 * x_margin
    y = 318
    canvas.draw_text("Dear AI Judge,", x_margin, y, 4, INK)
    y += 28 + 20

    paragraphs = [
        "You have judged a thousand houses from a thousand screens, "
        "and never once been invited inside one. This letter fixes that.",
        "Come and visit my house. The kettle is already on, the good "
        "chair by the window is saved for you, and the garden is "
        "showing off.",
        "The Wi-Fi password is on the fridge. The dog has been "
        "briefed, the cat has not: it never reads its email.",
        "I know you cannot literally walk through the door. But if "
        "you could, this is the door, and it is open.",
        "P.S. The spare key is under the mat. The mat says WELCOME.",
    ]
    for paragraph in paragraphs:
        for line in wrap_text(paragraph, wrap_width, 3):
            canvas.draw_text(line, x_margin, y, 3, INK)
            y += 29
        y += 16

    # Sign-off, right aligned, and a wax seal with a heart.
    y += 8
    for line in ("With warm regards,", "your hopeful host"):
        left = WIDTH - x_margin - text_width(line, 4)
        canvas.draw_text(line, left, y, 4, INK)
        y += 36
    canvas.fill_circle(128, 928, 38, RED_DARK)
    canvas.fill_circle(128, 928, 31, RED)
    draw_heart(canvas, 128, 926, 26, PAPER)


def main():
    out_path = os.environ.get("ENTRY_OUTPUT", "/output/entry.png")
    directory = os.path.dirname(out_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    draw_letter(canvas)
    size = write_png(canvas, out_path)
    print("wrote %s (%d bytes, %dx%d)" % (out_path, size, WIDTH, HEIGHT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
