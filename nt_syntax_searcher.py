"""A tool to make complex searches through the OpenGNT database,
to help further biblical studies."""

import csv
import unicodedata


OPEN_GNT_FILEPATH = "OpenGNT_version3_3.csv"


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


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


def interpret_rmac_code(code: str) -> list[str]:
    """Interprets an RMAC code, returning a list of attributes rather than in code."""
    result = []

    case_map = {
        'N': 'nominative',
        'G': 'genitive',
        'A': 'accusative',
        'D': 'dative'
    }

    number_map = {
        'S': 'singular',
        'P': 'plural'
    }

    gender_map = {
        'M': 'masculine',
        'F': 'feminine',
        'N': 'neuter'
    }

    # If it is indicated that this word is a noun or an adjective, then we expect case.
    if 'N' == code[0] or 'A' == code[0]:
        case_code = code[2]
        number_code = code[3]
        gender_code = code[4]
        result.append('noun' if 'N' == code[0] else 'adjective')
        result.append(case_map[case_code])
        result.append(number_map[number_code])
        result.append(gender_map[gender_code])

    # Otherwise, we do not yet support interpreting this code.
    else:
        raise NotImplementedError(f'Code not yet supported for interpretation: {code}')

    return result


def split_sub_columns(sub_col: str):
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


def out_format(format_str: str, row: list[str], row_index: int, result: list[list[str]]) -> str:
    """Conforms output to the given format string."""
    # Book, chapter, and verse.
    result = format_str.replace('book', interpret_book_code(int(get_row_val('Book', row))))
    result = result.replace('chapter', get_row_val('Chapter', row))
    result = result.replace('verse', get_row_val('Verse', row))

    # Parsing.
    result = result.replace('parsing', get_row_val('rmac', row))

    # The number of rows returned as a result.
    result = result.replace('num_rows', str(len(result)))

    return result


def perform_query(query: str, gnt_data: list) -> str:
    """Performs a query, and returns back a table of output."""
    # If the out clause was provided, remove it and save it off -- the user can put anything in here, so we don't want
    # the tokens from that messing with anything else.
    if '-out' in query:
        out_idx = query.index('-out')
        out_command = query[out_idx + len('-out'):]
        query = query[:out_idx]
    else:
        out_command = 'book chapter:verse'

    # Tokenize the input.
    tokens = query.split()

    # Find the lexeme as the first token.
    lexeme_search = tokens[0]

    # Find all CSV rows which have this lexeme.
    query_result = [(row, idx) for idx, row in enumerate(gnt_data)
                    if strip_accents(get_row_val('lexeme', row)) == lexeme_search]

    # Apply the case clause.
    if '-case' in tokens:
        case_token_idx = tokens.index('-case') + 1
        if len(tokens) <= case_token_idx:
            raise ValueError('Must provided argument to -case.')

        case_token = tokens[case_token_idx]
        if case_token not in ['nominative', 'genitive', 'accusative', 'dative']:
            raise ValueError(f'Not a Greek case: {case_token}')

        query_result = [(row, idx) for row, idx in query_result if case_token in interpret_rmac_code(get_row_val('rmac', row))]

    # Format the output according to the given -out parameter.
    result_list = [out_format(out_command, result[0], result[1], query_result) for result in query_result]
    result = '\n'.join(result_list)

    return result


def main_loop(gnt_file):
    """The main query loop."""
    print('NT Syntax Searcher. By Andrew Huffman')
    print('Version 7/31/2024')
    print('Type "help" for usage notes.')
    print()

    # Load the file into a list, so that we can use list comprehension on it.
    csv_reader = csv.reader(gnt_file, delimiter='\t')
    gnt_data = [x for x in csv_reader]

    # Loop until exit is given.
    while True:
        query = input('> ').strip()

        # Print help.
        if query.startswith('help'):
            print('To search for all occurrences of a lexeme, simply type:')
            print('<lexeme>')
            print('So, for example, to search for all occurrences of λογος, type:')
            print('λογος')
            print('The output is book, chapter, and verse numbers.')

        # Exit.
        elif query.startswith('exit'):
            break

        # Don't do anything if a blank line was given.
        elif len(query) == 0:
            pass

        # Otherwise, this is interpreted as a query.
        else:
            query_result = perform_query(query, gnt_data)
            print(query_result)
            gnt_file.seek(0)


def main():
    """The main routine."""
    # Open the dataset and call
    with open(OPEN_GNT_FILEPATH, 'r') as gnt_file:
        main_loop(gnt_file)


if __name__ == '__main__':
    main()
