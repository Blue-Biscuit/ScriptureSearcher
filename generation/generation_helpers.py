"""Helper functions for the generation part of the project."""

def split_sub_columns(sub_col: str):
    """The OpenGNT data set specifies "sub-columns" with these unicode bar characters. split them into something
    Python can handle."""
    # Open GNT uses this unicode bar to split columns.
    result = sub_col.split('｜')

    # Get rid of parens on the first and last element
    if len(result) > 0:
        result[0] = result[0][1:]
        result[-1] = result[-1][:-1]

    return result


def get_row_val(field: str, row: list[str]) -> str:
    """Gets the value of the given field in a row."""
    # Define the data structure which will be used to map on the result.
    row_indexing = {
        "OGNTsort": 0,
        "TANTsort": 1,
        "FEATURESsort1": 2,
        "LevinsohnClauseID": 3,
        "OTquotation": 4,
        "BGBSortI": (5, 0),
        "LTsortI": (5, 1),
        "STsortI": (5, 2),
        "Book": (6, 0),
        "Chapter": (6, 1),
        "Verse": (6, 2),
        "OGNTk": (7, 0),
        "OGNTu": (7, 1),
        "OGNTa": (7, 2),
        "lexeme": (7, 3),
        "rmac": (7, 4),
        "sn": (7, 5),
        "BDAGentry": (8, 0),
        "EDNTentry": (8, 1),
        "MounceEntry": (8, 2),
        "GoodrickKohlenbergerNumbers": (8, 3),
        "LN-LouwNidaNumbers": (8, 4),
        "transSBLcap": (9, 0),
        "transSBL": (9, 1),
        "modernGreek": (9, 2),
        "Fonetica_Transliteracion": (9, 3),
        "TBESG": (10, 0),
        "IT": (10, 1),
        "LT": (10, 2),
        "ST": (10, 3),
        "Espanol": (10, 4),
        "PMpWord": (11, 0),
        "PMfWord": (11, 1),
        "Note": (12, 0),
        "Mvar": (12, 1),
        "Mlexeme": (12, 2),
        "Mrmac": (12, 3),
        "Msn": (12, 4),
        "MTBESG": (12, 5)
    }

    # If the field provided isn't in the structure, error out.
    if field not in row_indexing:
        raise ValueError(f'Not a OpenGNT field: {field}')

    mapped = row_indexing[field]

    # If the mapped value is an index, just return that.
    if isinstance(mapped, int):
        result = row[mapped]

    # Otherwise, return the specified sub-column value.
    else:
        sub_cols = split_sub_columns(row[mapped[0]])
        result = sub_cols[mapped[1]]

    return result
