"""
Maps arbitrary color words (e.g. "chartreuse", "cornflowerblue") onto the
strict H&M color taxonomy using actual color-space distance, not text
similarity. Color naming is fundamentally a perceptual/RGB problem, not a
lexical one — "chartreuse" isn't semantically "close" to "yellow" in the way
a text embedding model understands meaning, it's close in RGB space. A
general-purpose sentence-embedding model was tested for this and performed
badly (see conversation/commit history); this is the principled replacement.

Only covers the CSS3 standard 147 named colors (via `webcolors`) — a precise,
unambiguous reference, not a guess. Words outside that set fall through to
the existing synonym/fuzzy-match layers in local_taxonomy_mapper.py.
"""
import webcolors

# Representative RGB for each *unambiguous* H&M color. Deliberately excludes
# vague buckets ("Other Red", "Unknown", "Transparent", etc.) — there's no
# single RGB point that means "Other Purple", so guessing one would make
# nearest-distance matching actively wrong rather than merely incomplete.
HM_COLOR_RGB = {
    "Black": (0, 0, 0),
    "White": (255, 255, 255),
    "Off White": (250, 240, 230),
    "Grey": (128, 128, 128),
    "Light Blue": (173, 216, 230),
    "Dark Blue": (0, 0, 139),
    "Dark Red": (139, 0, 0),
    "Dark Grey": (64, 64, 64),
    "Light Grey": (211, 211, 211),
    "Blue": (0, 0, 255),
    "Light Pink": (255, 182, 193),
    "Dark Green": (0, 100, 0),
    "Red": (255, 0, 0),
    "Greenish Khaki": (189, 183, 107),
    "Dark Pink": (231, 84, 128),
    "Light Orange": (255, 200, 124),
    "Turquoise": (64, 224, 208),
    "Yellow": (255, 255, 0),
    "Orange": (255, 165, 0),
    "Dark Purple": (75, 0, 130),
    "Pink": (255, 192, 203),
    "Beige": (245, 245, 220),
    "Light Beige": (240, 230, 210),
    "Dark Orange": (255, 140, 0),
    "Light Turquoise": (175, 238, 238),
    "Purple": (128, 0, 128),
    "Dark Beige": (196, 164, 132),
    "Light Green": (144, 238, 144),
    "Green": (0, 128, 0),
    "Light Yellow": (255, 255, 224),
    "Dark Yellow": (184, 134, 11),
    "Yellowish Brown": (153, 101, 21),
    "Silver": (192, 192, 192),
    "Light Red": (255, 102, 102),
    "Dark Turquoise": (0, 139, 139),
    "Light Purple": (216, 191, 216),
    "Greyish Beige": (200, 192, 174),
    "Gold": (255, 215, 0),
    "Bronze/Copper": (184, 115, 51),
}


def _word_to_rgb(word: str):
    """Look up a color word's RGB via the CSS3 standard name set. Returns
    None if the word isn't a recognized standard color name — never guesses."""
    normalized = word.strip().lower().replace(" ", "").replace("-", "")
    try:
        return webcolors.name_to_rgb(normalized, spec="css3")
    except ValueError:
        return None


def match_color_by_distance(word: str, max_distance: float = 120.0):
    """
    Returns the closest H&M color to `word` by RGB Euclidean distance, or
    None if `word` isn't a recognized CSS3 color name, or if even the
    closest H&M color is too far away to be a meaningful match.
    """
    rgb = _word_to_rgb(word)
    if rgb is None:
        return None

    best_name, best_dist = None, float("inf")
    for name, (r, g, b) in HM_COLOR_RGB.items():
        dist = ((rgb[0] - r) ** 2 + (rgb[1] - g) ** 2 + (rgb[2] - b) ** 2) ** 0.5
        if dist < best_dist:
            best_name, best_dist = name, dist

    return best_name if best_dist <= max_distance else None
