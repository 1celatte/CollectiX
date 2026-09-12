import unicodedata


def normalize_text(text):
    text = text or ""
    text = text.strip()

    normalized = unicodedata.normalize("NFKD", text)

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).casefold()