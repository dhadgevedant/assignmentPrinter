from PIL import Image, ImageDraw, ImageFont
import random
import os
import colorsys
import math

# ---------------------------
# Page and Text Layout Settings
# ---------------------------
A4_WIDTH, A4_HEIGHT = 2480, 3508  # A4 page at 300 dpi
START_X = 400.0    # Horizontal margin (can be a decimal)
START_Y = 426    # Vertical position of the first line (can be a decimal)
LINE_HEIGHT = 90 # Spacing between lines (can be a decimal)
RIGHT_MARGIN = 600  # Right margin (for wrapping)
RIGHT_PADDING = 200  # Additional padding on the right side

# ---------------------------
# Randomization Parameters (Tweak these as needed)
# ---------------------------
LETTER_VERTICAL_JITTER_MIN = 0
LETTER_VERTICAL_JITTER_MAX = 0
LETTER_HORIZONTAL_JITTER_MIN = -1
LETTER_HORIZONTAL_JITTER_MAX = 3

LETTER_TILT_MIN = 0    # Minimal tilt
LETTER_TILT_MAX = -20  # Maximum tilt (negative means tilt in one direction)

LETTER_SPACING_VARIATION_MIN = 4
LETTER_SPACING_VARIATION_MAX = 15

# Additional padding (in pixels) to avoid clipping when rotating
LETTER_PADDING = 10

# New parameter for pressure variation (scaling factor)
PRESSURE_MIN = 0.95
PRESSURE_MAX = 1.05

# Correction probability (chance to simulate a correction on a line)
CORRECTION_PROBABILITY = 0

# ---------------------------
# Text Appearance Settings
# ---------------------------
TEXT_COLOR = (55, 45, 146)  # Base blue color
BRIGHTNESS_VARIATION = 0.01   # ±10% lightness variation

# Option to show or hide the background:
SHOW_BACKGROUND = True   # Set to False to generate output without the background

# ---------------------------
# Ink Brightness Variation Function
# ---------------------------
def randomize_ink_brightness(base_color, variation=BRIGHTNESS_VARIATION):
    """
    Adjusts the brightness (lightness) of the base_color by a random amount 
    within ±variation while preserving the hue.
    """
    r, g, b = base_color
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    delta = random.uniform(-variation, variation)
    new_l = min(max(l + delta, 0), 1)
    new_r, new_g, new_b = colorsys.hls_to_rgb(h, new_l, s)
    return (int(new_r * 255), int(new_g * 255), int(new_b * 255))

# ---------------------------
# Helper Functions for Text Wrapping
# ---------------------------
def measure_text_width(text, font):
    """Return the pixel width of text using the given font."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]

def wrap_text(text, font, max_width):
    """
    Wrap text so that each line's width does not exceed max_width.
    Returns a list of lines.
    """
    wrapped_lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            wrapped_lines.append("")  # Preserve blank lines
            continue
        words = paragraph.split(" ")
        current_line = words[0]
        for word in words[1:]:
            test_line = current_line + " " + word
            if measure_text_width(test_line, font) <= max_width:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                current_line = word
        wrapped_lines.append(current_line)
    return wrapped_lines

# ---------------------------
# Multi-Page Generation Function
# ---------------------------
def generate_handwritten_letter(text, output_dir, font_path, bg_path, show_background=True):
    # Load the font
    font = ImageFont.truetype(font_path, 48)
    
    # Calculate available width for text (accounting for right margin and additional padding)
    available_width = int(A4_WIDTH - START_X - RIGHT_MARGIN - RIGHT_PADDING)
    # Wrap the input text based on available width
    wrapped_lines = wrap_text(text, font, available_width)
    
    # Calculate maximum lines per page (convert float division result to int)
    max_lines_per_page = int((A4_HEIGHT - START_Y) // LINE_HEIGHT)
    # Split wrapped lines into pages
    pages = [wrapped_lines[i:i + max_lines_per_page] for i in range(0, len(wrapped_lines), max_lines_per_page)]
    
    for page_idx, page in enumerate(pages, start=1):
        # Create a new page: either load the background or create a blank white page.
        if show_background:
            image = Image.open(bg_path)
            image = image.resize((A4_WIDTH, A4_HEIGHT))
        else:
            image = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), "white")
        # Ensure image is in RGBA mode for transparency
        image = image.convert("RGBA")
        
        # Draw each line on this page
        draw = ImageDraw.Draw(image)
        for line_idx, line in enumerate(page):
            y = START_Y + line_idx * LINE_HEIGHT
            current_x = START_X
            for char in line:
                # Get bounding box for the character
                left, top, right, bottom = font.getbbox(char)
                char_width = right - left
                char_height = bottom - top

                # Create a canvas larger than the character to avoid clipping after rotation.
                canvas_width = char_width + 2 * LETTER_PADDING
                canvas_height = char_height + 2 * LETTER_PADDING
                char_image = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 0))
                char_draw = ImageDraw.Draw(char_image)
                
                # Get a randomized ink brightness while preserving hue
                ink_color = randomize_ink_brightness(TEXT_COLOR)
                
                # Draw the character with padding adjustment
                char_draw.text((LETTER_PADDING - left, LETTER_PADDING - top), char, font=font, fill=ink_color)
                
                # --- Pressure Variation ---
                pressure_factor = random.uniform(PRESSURE_MIN, PRESSURE_MAX)
                # Scale the character image by the pressure factor
                scaled_width = int(char_image.width * pressure_factor)
                scaled_height = int(char_image.height * pressure_factor)
                char_image = char_image.resize((scaled_width, scaled_height), resample=Image.BICUBIC)
                
                # --- End Pressure Variation ---
                
                # Apply random tilt
                angle = random.uniform(LETTER_TILT_MIN, LETTER_TILT_MAX)
                char_image = char_image.rotate(angle, resample=Image.BICUBIC, expand=True)
                
                # Apply horizontal jitter (vertical jitter is disabled)
                jitter_x = random.randint(LETTER_HORIZONTAL_JITTER_MIN, LETTER_HORIZONTAL_JITTER_MAX)
                jitter_y = 0
                paste_x = int(round(current_x + jitter_x))
                paste_y = int(round(y + jitter_y))
                image.paste(char_image, (paste_x, paste_y), char_image)
                
                # Update current x position using the original character width scaled by pressure factor
                spacing_variation = random.randint(LETTER_SPACING_VARIATION_MIN, LETTER_SPACING_VARIATION_MAX)
                current_x += int(char_width * pressure_factor) + spacing_variation
            
            # --- Simulated Correction ---
            # With a probability, add a strike-through correction on the line
            # if random.random() < CORRECTION_PROBABILITY and current_x > START_X + 100:
            #     corr_start = random.randint(int(START_X), int(current_x) - 50)
            #     corr_length = random.randint(30, 100)
            #     corr_y = int(round(START_Y - 10 + line_idx * LINE_HEIGHT + LINE_HEIGHT / 2))
            #     # Draw a correction line in a semi-transparent dark red
            #     draw.line([(corr_start, corr_y), (corr_start + corr_length, corr_y)], fill=(55, 45, 146), width=3)
            # --- End Simulated Correction ---
        
        # Determine output filename based on number of pages
        if len(pages) == 1:
            output_file = os.path.join(output_dir, "handwritten_letter.png")
        else:
            output_file = os.path.join(output_dir, f"handwritten_letter_page_{page_idx}.png")
        image.save(output_file)
        print(f"Page {page_idx} generated and saved to {output_file}")

# ---------------------------
# Main Function
# ---------------------------
def main():
    letter_file = os.path.join(os.path.dirname(__file__), "letter.txt")
    with open(letter_file, "r", encoding="utf-8") as f:
        letter_text = f.read()
    
    font_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "font1.ttf")
    bg_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "lined_a4.png")
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    generate_handwritten_letter(letter_text, output_dir, font_file, bg_file, show_background=SHOW_BACKGROUND)

if __name__ == "__main__":
    main()
