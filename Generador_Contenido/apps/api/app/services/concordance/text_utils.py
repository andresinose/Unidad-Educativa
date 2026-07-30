"""Text normalization, tokenization, and similarity utilities according to Spec v1.2.
"""
from __future__ import annotations

import re
import unicodedata

STOPWORDS = {
    "de", "la", "el", "los", "las", "y", "e", "con", "en", "del", "al", "a", "un", "una",
    "por", "para", "su", "sus", "que", "o", "u", "se", "numeros", "numero",
    "resolucion", "problemas", "concepto", "conceptos", "sobre", "entre"
}


def normalizar(texto: str) -> str:
    """Lowercases, removes diacritics/accents, and replaces non-alphanumeric chars with spaces."""
    if not texto:
        return ""
    texto = texto.lower()
    # NFD decomposition + stripping combining characters (accents/tildes)
    nfd = unicodedata.normalize("NFD", texto)
    sem_tildes = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    # replace non-alphanumeric with spaces
    limpio = re.sub(r"[^\w\s]", " ", sem_tildes)
    return re.sub(r"\s+", " ", limpio).strip()


def tokens(texto: str) -> set[str]:
    """Extracts non-stopword tokens, stemmed/truncated to max 6 characters."""
    norm = normalizar(texto)
    if not norm:
        return set()
    res: set[str] = set()
    for word in norm.split():
        if len(word) <= 2 or word in STOPWORDS:
            continue
        stem = word[:6] if len(word) > 6 else word
        res.add(stem)
    return res


def similitud(a: str, b: str) -> float:
    """Calculates token overlap over the smaller set (Section 5.1)."""
    ta = tokens(a)
    tb = tokens(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    return len(inter) / min(len(ta), len(tb))
