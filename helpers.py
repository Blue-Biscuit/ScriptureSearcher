"""Helper functions for the project."""

import unicodedata


def strip_accents(s: str):
    """Strips the accents off of the given Greek word."""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
