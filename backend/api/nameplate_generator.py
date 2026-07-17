"""
nameplate_generator.py

Generuje pojedynczy PNG (avatar + nazwa postaci) do nałożenia na timeline
w DaVinci. Generujemy RAZ na postać (cache po character_id) i wielokrotnie
używamy tego samego pliku w FCPXML — więc nawet przy 500 kwestiach w rozdziale
avatar Emilii jest renderowany tylko raz.

Wygląd: kwadratowa miniaturka avatara w prawym górnym rogu + pasek z nazwą
pod spodem — podobnie jak w Twoim przykładowym screenie z "EMILIA".

Wymagane: Pillow (już masz).
"""

import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

CANVAS_W, CANVAS_H = 1920, 1080     # musi być zgodne z rozdzielczością timeline'u
AVATAR_SIZE = 220
MARGIN_RIGHT = 60
MARGIN_TOP = 60
NAME_BOX_HEIGHT = 60
BORDER_COLOR = (70, 140, 255, 255)   # niebieska ramka jak w Twoim przykładzie
BG_COLOR = (20, 20, 20, 180)
TEXT_COLOR = (255, 255, 255, 255)


def _load_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_nameplate(
    character_name: str,
    avatar_path: Optional[str],
    output_path: str,
) -> str:
    """
    Tworzy PNG (1920x1080, transparentne tło poza kartą postaci) z avatarem
    w prawym górnym rogu i nazwą postaci pod spodem.

    character_name: np. "Emilia"
    avatar_path: ścieżka do pliku avatara na dysku (może być None -> placeholder)
    output_path: gdzie zapisać wynikowy PNG

    Zwraca output_path.
    """
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    avatar_x = CANVAS_W - MARGIN_RIGHT - AVATAR_SIZE
    avatar_y = MARGIN_TOP

    # --- Avatar ---
    if avatar_path and os.path.exists(avatar_path):
        avatar_img = Image.open(avatar_path).convert("RGBA")
        avatar_img = avatar_img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
    else:
        avatar_img = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (60, 60, 60, 255))

    canvas.paste(avatar_img, (avatar_x, avatar_y), avatar_img)

    # --- Ramka wokół avatara ---
    draw.rectangle(
        [avatar_x, avatar_y, avatar_x + AVATAR_SIZE, avatar_y + AVATAR_SIZE],
        outline=BORDER_COLOR, width=4
    )

    # --- Pasek z nazwą pod avatarem ---
    name_box_y = avatar_y + AVATAR_SIZE + 10
    draw.rectangle(
        [avatar_x, name_box_y, avatar_x + AVATAR_SIZE, name_box_y + NAME_BOX_HEIGHT],
        outline=BORDER_COLOR, width=3, fill=BG_COLOR
    )

    font = _load_font(32)
    name_text = character_name.upper()
    bbox = draw.textbbox((0, 0), name_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = avatar_x + (AVATAR_SIZE - text_w) // 2
    text_y = name_box_y + (NAME_BOX_HEIGHT - text_h) // 2 - bbox[1]
    draw.text((text_x, text_y), name_text, font=font, fill=TEXT_COLOR)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, "PNG")
    return output_path


def get_or_create_nameplate(
    character_id: int,
    character_name: str,
    avatar_path: Optional[str],
    cache_dir: str,
) -> str:
    """
    Cache po character_id — nie generujemy tego samego PNG-a wielokrotnie
    w obrębie jednego audiobooka.
    """
    output_path = os.path.join(cache_dir, f"nameplate_{character_id}.png")
    if not os.path.exists(output_path):
        generate_nameplate(character_name, avatar_path, output_path)
    return output_path
