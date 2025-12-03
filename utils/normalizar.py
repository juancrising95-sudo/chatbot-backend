
import unicodedata

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return t
