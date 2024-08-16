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
    "rmac",
    "LevinsohnClauseID",
    "OGNTa"
]

# Test the generation fields, to make sure that it really is a subset of all OpenGNT fields.
for _field in GENERATION_FIELDS:
    if _field not in OPENGNT_FIELDS:
        raise ValueError('GENERATION_FIELDS not a subset of OPENGNT_FIELDS.')


def convert_line(row: list[str], idx: int) -> dict:
    """Converts the line to a dictionary."""
    result = {}
    for field in GENERATION_FIELDS:
        result[field] = helpers.get_row_val(field, row)

    # Add the word index
    result['word_index'] = idx

    return result


def process_file(file):
    """Processes the OpenGNT file."""
    # Do the conversion.
    reader = csv.reader(file, delimiter='\t')
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
