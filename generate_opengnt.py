#!/bin/python3
"""Takes the OpenGNT database and transforms it to an easily searchable JSON model."""

import helpers
import csv
import json

INPUT_FILE_NAME = 'OpenGNT_version3_3.csv'
OUTPUT_FILE_NAME = 'opengnt.json'

OPENGNT_FIELDS = [
        "OGNTsort",
        "TANTsort",
        "FEATURESsort1",
        "LevinsohnClauseID",
        "OTquotation",
        "BGBSortI",
        "LTsortI",
        "STsortI",
        "Book",
        "Chapter",
        "Verse",
        "OGNTk",
        "OGNTu",
        "OGNTa",
        "lexeme",
        "rmac",
        "sn",
        "BDAGentry",
        "EDNTentry",
        "MounceEntry",
        "GoodrickKohlenbergerNumbers",
        "LN-LouwNidaNumbers",
        "transSBLcap",
        "transSBL",
        "modernGreek",
        "Fonetica_Transliteracion",
        "TBESG",
        "IT",
        "LT",
        "ST",
        "Espanol",
        "PMpWord",
        "PMfWord",
        "Note",
        "Mvar",
        "Mlexeme",
        "Mrmac",
        "Msn",
        "MTBESG"
]

GENERATION_FIELDS = [
    "Book",
    "Chapter",
    "Verse",
    "lexeme",
    ("rmac", "morph_code"),
    "LevinsohnClauseID",
    ("OGNTa", "word")
]

# Test the generation fields, to make sure that it really is a subset of all OpenGNT fields.
for _field in GENERATION_FIELDS:
    if isinstance(_field, tuple):
        if _field[0] not in OPENGNT_FIELDS:
            raise ValueError(f'{_field[0]} not a field in the OpenGNT dataset.')
    elif _field not in OPENGNT_FIELDS:
        raise ValueError(f'{_field[0]} not a field in the OpenGNT dataset.')


def interpret_book_code(code: int):
    book_list = [
        'Matthew',
        'Mark',
        'Luke',
        'John',
        'Acts',
        'Romans',
        '1 Corinthians',
        '2 Corinthians',
        'Galatians',
        'Ephesians',
        'Philippians',
        'Colossians',
        '1 Thessalonians',
        '2 Thessalonians',
        '1 Timothy',
        '2 Timothy',
        'Titus',
        'Philemon',
        'Hebrews',
        'James',
        '1 Peter',
        '2 Peter',
        '1 John',
        '2 John',
        '3 John',
        'Jude',
        'Revelation'
    ]

    book_index = code - 40
    return book_list[book_index]


def convert_line(row: list[str], idx: int) -> dict:
    """Converts the line to a dictionary."""
    result = {}
    for field in GENERATION_FIELDS:
        if isinstance(field, tuple):
            result[field[1]] = helpers.get_row_val(field[0], row)
        elif field == 'Book':
            # Transform the book into a string first.
            book_number = int(helpers.get_row_val(field, row))
            result[field] = interpret_book_code(book_number)
        else:
            result[field] = helpers.get_row_val(field, row)

    # Add the word index
    result['word_index'] = idx

    return result


def process_file(file):
    """Processes the OpenGNT file."""
    # Do the conversion.
    reader = csv.reader(file, delimiter='\t')
    next(reader)  # Skip the first line (the table header)
    gnt_data_json = [convert_line(x, idx) for idx, x in enumerate(reader)]

    # Output to a file.
    with open(OUTPUT_FILE_NAME, 'w') as out_f:
        json.dump(gnt_data_json, out_f)


def main():
    """The main routine."""
    with open(INPUT_FILE_NAME, 'r') as f:
        process_file(f)


if __name__ == '__main__':
    main()
