"""
nameplate_generator.py

Generuje pojedynczy PNG (avatar + nazwa postaci) do nałożenia na timeline
w DaVinci. Generujemy RAZ na postać (cache po character_id) i wielokrotnie
używamy tego samego pliku w FCPXML — więc nawet przy 500 kwestiach w rozdziale
avatar Emilii jest renderowany tylko raz.

Wygląd: avatar po lewej stronie kadru, wyśrodkowany w pionie, z nazwą postaci
pod spodem. BEZ tła, ramek czy jakichkolwiek ozdobników — to celowe, bo
background i obramowania dokładasz sam w DaVinci. Obraz NIE zawiera treści
czytanej kwestii (to idzie osobno przez plik .srt) — tylko avatar i nazwa.

Wymagane: Pillow (już masz).
"""

import os
import re
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

CANVAS_W, CANVAS_H = 1920, 1080     # musi być zgodne z rozdzielczością timeline'u

AVATAR_SIZE = 450       # rozmiar kwadratu avatara w pikselach
MARGIN_LEFT = 140       # odstęp avatara od lewej krawędzi kadru
NAME_GAP = 45           # odstęp między avatarem a nazwą pod spodem (odrobinę niżej niż wcześniej)
NAME_FONT_SIZE = 44

TEXT_COLOR = (255, 255, 255, 255)


def _crop_to_square_top(image: Image.Image, size: int) -> Image.Image:
    """
    Skaluje obraz proporcjonalnie tak, żeby pokrył kwadrat size x size
    (bez zniekształcenia), a potem przycina go do kwadratu: w poziomie
    na środek, w pionie OD GÓRY (żeby twarz/góra postaci na avatarze
    nigdy nie została ucięta, niezależnie od oryginalnych proporcji zdjęcia).
    """
    src_w, src_h = image.size
    scale = size / min(src_w, src_h)
    new_w, new_h = max(round(src_w * scale), size), max(round(src_h * scale), size)
    resized = image.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - size) // 2
    top = 0  # zawsze od góry, nie ze środka - nie tniemy twarzy
    return resized.crop((left, top, left + size, top + size))


def _load_font(size: int):
    candidates = [
        # Dorzuć tu plik czcionki Sitka Heading (patrz komentarz niżej)
        "/app/api/fonts/SitkaHeadingBold.ttf",
        "/app/api/fonts/sitka.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue  # np. .ttc bez odpowiedniego face index - próbuj dalej
    return ImageFont.load_default()


def generate_nameplate(
    character_name: str,
    avatar_path: Optional[str],
    output_path: str,
) -> str:
    """
    Tworzy PNG (1920x1080, w pełni transparentne tło) z samym avatarem
    i nazwą postaci pod nim — bez ramek, bez tła, bez ozdobników.

    Layout: avatar wyśrodkowany w pionie, przy lewej krawędzi kadru (żeby
    zostawić miejsce po prawej na Twoje napisy z pliku .srt). Nazwa postaci
    wycentrowana pod avatarem.

    character_name: np. "Emilia"
    avatar_path: ścieżka do pliku avatara na dysku (może być None -> szary placeholder)
    output_path: gdzie zapisać wynikowy PNG

    Zwraca output_path.
    """
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    font = _load_font(NAME_FONT_SIZE)
    name_text = character_name.upper()
    bbox = draw.textbbox((0, 0), name_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Cały blok (avatar + odstęp + nazwa) wyśrodkowany w pionie na kadrze
    total_block_height = AVATAR_SIZE + NAME_GAP + text_h
    avatar_y = (CANVAS_H - total_block_height) // 2
    avatar_x = MARGIN_LEFT

    # --- Avatar (bez ramki) ---
    if avatar_path and os.path.exists(avatar_path):
        avatar_img = Image.open(avatar_path).convert("RGBA")
        avatar_img = _crop_to_square_top(avatar_img, AVATAR_SIZE)
    else:
        if avatar_path:
            print(f"[nameplate_generator] UWAGA: nie znaleziono pliku avatara pod ścieżką: {avatar_path} - używam szarego placeholdera")
        avatar_img = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (60, 60, 60, 255))

    canvas.paste(avatar_img, (avatar_x, avatar_y), avatar_img)

    # --- Nazwa postaci pod avatarem, wycentrowana pod nim (bez tła/ramki) ---
    text_x = avatar_x + (AVATAR_SIZE - text_w) // 2 - bbox[0]
    text_y = avatar_y + AVATAR_SIZE + NAME_GAP - bbox[1]
    draw.text((text_x, text_y), name_text, font=font, fill=TEXT_COLOR)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, "PNG")
    return output_path


def _slugify(name: str) -> str:
    """Zamienia nazwę postaci na bezpieczny fragment nazwy pliku (a-z, 0-9, _)."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "character"


def get_or_create_nameplate(
    character_id: int,
    character_name: str,
    avatar_path: Optional[str],
    cache_dir: str,
) -> str:
    """
    Cache po character_id — nie generujemy tego samego PNG-a wielokrotnie
    w obrębie jednego audiobooka.

    WAŻNE: nazwa pliku zawiera slug z nazwy postaci (nie tylko goły numer
    ID). Pliki typu "nameplate_13.png", "nameplate_14.png" w tym samym
    folderze (ten sam prefiks + rosnący numer) DaVinci Resolve automatycznie
    wykrywa jako "sekwencję obrazów" (jak klatki animacji) i SKLEJA w jeden
    klip - co objawia się przeskakiwaniem z avatara jednej postaci na avatar
    drugiej w połowie karty. Różne prefiksy per postać (nameplate_subaru_14.png
    vs nameplate_beatrice_13.png) łamią ten wzorzec.
    """
    slug = _slugify(character_name)
    output_path = os.path.join(cache_dir, f"nameplate_{slug}_{character_id}.png")
    if not os.path.exists(output_path):
        generate_nameplate(character_name, avatar_path, output_path)
    return output_path