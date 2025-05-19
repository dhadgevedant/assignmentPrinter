from PIL import Image, ImageDraw, ImageFont
import random
import os
import colorsys
import math

# ---------------------------
# Page and Text Layout Settings
# ---------------------------
A4_WIDTH, A4_HEIGHT = 2480, 3508  # A4 page at 300 dpi
START_X = 297.637795  # Horizontal margin (can be a decimal)
START_Y = 383.858267   # Vertical position of the first line (can be a decimal)
LINE_HEIGHT = 96.26 # Spacing between lines (can be a decimal)
RIGHT_MARGIN = 600  # Right margin (for wrapping)
RIGHT_PADDING = 200  # Additional padding on the right side

# ---------------------------
# Randomization Parameters
# ---------------------------
LETTER_VERTICAL_JITTER_MIN = -1.2
LETTER_VERTICAL_JITTER_MAX = 1.2
LETTER_HORIZONTAL_JITTER_MIN = -0
LETTER_HORIZONTAL_JITTER_MAX = 0

LETTER_TILT_MIN = 0    # Minimal tilt
LETTER_TILT_MAX = 10 # Maximum tilt (negative means tilt in one direction)

LETTER_SPACING_VARIATION_MIN = 4
LETTER_SPACING_VARIATION_MAX = 15

# Additional padding (in pixels) to avoid clipping when rotating
LETTER_PADDING = 10

# Pressure variation (scaling factor)
PRESSURE_MIN = 0.95
PRESSURE_MAX = 1.05

# Size variation (font size scaling factor)
SIZE_VARIATION_MIN = 0.95
SIZE_VARIATION_MAX = 1.5

# Correction probability (chance to simulate a correction on a line)
CORRECTION_PROBABILITY = 0

# ---------------------------
# Text Appearance Settings
# ---------------------------
TEXT_COLOR = (55, 45, 146)  # Base ink color
BRIGHTNESS_VARIATION = 0.01 # ±1% lightness variation

# Option to show or hide the background:
SHOW_BACKGROUND = False

# Base font size
BASE_FONT_SIZE = 60

# ---------------------------
# Ink Brightness Variation
# ---------------------------
def randomize_ink_brightness(base_color, variation=BRIGHTNESS_VARIATION):
    r, g, b = [c/255.0 for c in base_color]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    delta = random.uniform(-variation, variation)
    new_l = min(max(l + delta, 0), 1)
    nr, ng, nb = colorsys.hls_to_rgb(h, new_l, s)
    return (int(nr*255), int(ng*255), int(nb*255))

# ---------------------------
# Helper Functions
# ---------------------------

def measure_text_width(text, font):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def wrap_text(text, font, max_width):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        words = para.split(" ")
        line = words[0]
        for w in words[1:]:
            test = f"{line} {w}"
            if measure_text_width(test, font) <= max_width:
                line = test
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines

# ---------------------------
# Generation Function
# ---------------------------
def generate_handwritten_letter(text, output_dir, font_path, bg_path, show_background=True):
    # Verify font file exists
    if not os.path.isfile(font_path):
        raise FileNotFoundError(f"Font not found at: {font_path}")

    # Prepare base font for wrapping
    base_font = ImageFont.truetype(font_path, BASE_FONT_SIZE)
    available_width = int(A4_WIDTH - START_X - RIGHT_MARGIN - RIGHT_PADDING)
    wrapped = wrap_text(text, base_font, available_width)

    max_lines = int((A4_HEIGHT - START_Y) // LINE_HEIGHT)
    pages = [wrapped[i:i+max_lines] for i in range(0, len(wrapped), max_lines)]

    for idx, page in enumerate(pages, start=1):
        # Load or create background
        if show_background and os.path.isfile(bg_path):
            img = Image.open(bg_path).resize((A4_WIDTH, A4_HEIGHT))
        else:
            img = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
        img = img.convert('RGBA')
        draw = ImageDraw.Draw(img)

        # Draw lines
        for li, line in enumerate(page):
            y = START_Y + li * LINE_HEIGHT
            x = START_X
            for ch in line:
                # Size variation
                sf = random.uniform(SIZE_VARIATION_MIN, SIZE_VARIATION_MAX)
                fs = max(1, int(BASE_FONT_SIZE * sf))
                base_font = max(1, int(BASE_FONT_SIZE * sf))
                fnt = ImageFont.truetype(font_path, fs)

                # Measure char
                L, T, R, B = fnt.getbbox(ch)
                cw, chh = R-L, B-T

                # Render onto char canvas
                cw_canvas = cw + 2*LETTER_PADDING
                ch_canvas = chh + 2*LETTER_PADDING
                char_im = Image.new('RGBA', (cw_canvas, ch_canvas), (0,0,0,0))
                cd = ImageDraw.Draw(char_im)
                color = randomize_ink_brightness(TEXT_COLOR)
                cd.text((LETTER_PADDING - L, LETTER_PADDING - T), ch, font=fnt, fill=color)

                # Pressure scale
                pf = random.uniform(PRESSURE_MIN, PRESSURE_MAX)
                nw = int(char_im.width * pf)
                nh = int(char_im.height * pf)
                char_im = char_im.resize((nw, nh), Image.BICUBIC)

                # Tilt
                ang = random.uniform(LETTER_TILT_MIN, LETTER_TILT_MAX)
                char_im = char_im.rotate(ang, Image.BICUBIC, expand=True)

                # Jitter and paste
                jx = random.randint(LETTER_HORIZONTAL_JITTER_MIN, LETTER_HORIZONTAL_JITTER_MAX)
                img.paste(char_im, (int(round(x + jx)), int(round(y))), char_im)

                # Advance x
                var = random.randint(LETTER_SPACING_VARIATION_MIN, LETTER_SPACING_VARIATION_MAX)
                x += int(cw * pf) + var

        # Save
        name = "handwritten_letter.png" if len(pages)==1 else f"handwritten_page_{idx}.png"
        outf = os.path.join(output_dir, name)
        os.makedirs(output_dir, exist_ok=True)
        img.save(outf)
        print(f"Saved: {outf}")

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    # Compute project root (two levels up from this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))

    letter_txt = os.path.join(script_dir, "letter.txt")
    font_ttf = os.path.join(script_dir, "..", "fonts", "font3.ttf")
    font_ttf = os.path.abspath(font_ttf)

    bg_img = os.path.join(project_root, "assets", "lined_a4.png")
    out_dir = os.path.join(project_root, "output")

    # Read input
    with open(letter_txt, "r", encoding="utf-8") as f:
        txt = f.read()

    generate_handwritten_letter(txt, out_dir, font_ttf, bg_img, show_background=SHOW_BACKGROUND)
