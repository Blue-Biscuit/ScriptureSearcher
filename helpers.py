"""Helper functions for the project."""

import unicodedata



def strip_accents(s: str):
    """Strips the accents off of the given Greek word."""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def assert_non_null(val, val_name: str):
    """Raises a value error if the value is None."""
    if val is None:
        raise ValueError(f'{val_name} was None')