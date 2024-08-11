#!/bin/python3
"""A tool to make complex searches through the OpenGNT database,
to help further biblical studies."""
import json
import unicodedata
import text_query
import argparse
import sys
import query_string_parsing


OPEN_GNT_FILEPATH = "opengnt.json"
APP_NAME = 'SyntaxSearcher'
APP_VERSION = 'alpha'
EXECUTABLE_NAME = 'nt_syntax_searcher.py'


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


def get_rows_in_clause(start_idx: int, gnt_data: list[dict[str, str]]) -> list[dict[str, str]]:
    """Gets all rows which are in the same clause. This isn't done with list comprehension because this is much
    more efficient."""
    clause_this = gnt_data[start_idx]['LevinsohnClauseID']

    # Get all the part of the clause above.
    last_idx_of_clause = -1
    for i in range(start_idx + 1, len(gnt_data)):
        if gnt_data[i]['LevinsohnClauseID'] != clause_this:
            last_idx_of_clause = i - 1
            break

    # Get all the part of the clause below.
    first_idx_of_clause = -1
    for i in range(start_idx - 1, 0, -1):
        if gnt_data[i]['LevinsohnClauseID'] != clause_this:
            first_idx_of_clause = i + 1
            break

    # Join the two.
    if -1 == first_idx_of_clause or -1 == last_idx_of_clause:
        raise ValueError('Something went wrong.')
    else:
        return gnt_data[first_idx_of_clause:last_idx_of_clause+1]


def out_format(format_str: str, row: dict[str, str], row_index: int, num_rows: int, gnt_data: list[list[str]]) -> str:
    """Conforms output to the given format string."""
    # Book, chapter, and verse.
    result = format_str.replace('book', interpret_book_code(int(row['Book'])))
    result = result.replace('chapter', row['Chapter'])
    result = result.replace('verse', row['Verse'])

    # Parsing.
    result = result.replace('parsing', row['rmac'])

    # The number of rows returned as a result.
    result = result.replace('num_rows', str(num_rows))

    # The containing clause string.
    while 'clause' in result:
        clause = get_rows_in_clause(row_index, gnt_data)
        clause_str = ' '.join(
            [row['OGNTa'] for row in clause]
        )
        result = result.replace('clause', clause_str)

    return result


def print_help(help_arg: str):
    """Prints help. Takes in argv """
    # If no argument was provided, just print general help.
    if '' == help_arg:
        print(f'USAGE: {EXECUTABLE_NAME} [ARGS] SEARCH [--out OUT]')
        print("\tPerforms complex searches through the Greek New Testament's text.")
        print()
        print('ARGS:')
        print('\t-h | --help H\t\t\tPrints this help and exits. Prints help about a specific part of the program')
        print('\t\t\t\t\tgiven an argument. "-h help" prints possible arguments.')
    elif 'help' == help_arg:
        print(f'USAGE: {EXECUTABLE_NAME} -h H')
        print('\tPrints help about a specific aspect of the program.')
        print()
        print('H:')
        print('\t(empty)\t\t\tPrints help for the general program.')
        print('\thelp\t\t\tPrints help for the help command.')
        print('\tsearch\t\t\tPrints help for searching.')
        print('\tout\t\t\tPrints help for output.')
    elif 'search' == help_arg:
        print(f'USAGE: {EXECUTABLE_NAME} SEARCH_TERM [ARGS]')
        print('\tSpecifies the specific search on the New Testament text.')
        print()
        print('\tThe simplest search would be a simple search for all occurrences of a lexeme, as so:')
        print('\t\tλογος')
        print()
        print('\tThis will search through the entire text of the New Testament for the word "λογος," and return the')
        print('\tlist of passages, with the specific clause in which the term appears. If you wanted, you could also')
        print('\tspecify that you only want to see occurrences of λογος in the genitive case: ')
        print('\t\tλογος --case genitive')
        print()
        print('\tSearches can be strung together with "and"s and "or"s; so if I wanted occurrences of λογος in the')
        print('\tdative singular or the genitive plural, I could do this:')
        print('\t\tλογος --case dative and λογος --number singular or λογος --case genitive and λογος --number plural')
        print()
        print('\tThe order of operations, normally, is "and"s first and then "or"s. To override, this precedence, use')
        print('\tbraces for the things you want to be done first; this finds all occurrences of λογος in the')
        print('\tgenitive singular or the dative singular:')
        print('\t\t[λογος --case genitive or λογος --case dative] and λογος --number singular')
        print()
        print('\tThese arguments are positional, so the lexeme should always come first.')
        print()
        print('ARGS:')
        print('\t--case C\t\t\tThe case of the lexeme to search.')
        print('\t--number N\t\t\tThe number of the lexeme to search.')
        print('\t--gender G\t\t\tThe gender of the lexeme to search.')
    elif 'out' == help_arg:
        print(f'USAGE: {EXECUTABLE_NAME} SEARCH --out OUT')
        print('\tSpecifies the format in which the output of the search is to be printed.')
        print()
        print('\tThe input to this command is simply a string which will be printed for each element in the returned')
        print('\tset. Within that string, there are certain special words (listed below, under "OUT") which will be')
        print('\tsubstituted for different fields in the return set. As an example, if --out is not provided, then the')
        print('\tdefault return string used is:')
        print('\t\tbook chapter.verse: clause')
        print('\tAnd the return looks like:')
        print('\t\tJohn 1.1: Ἐν ἀρχῇ ἦν ὁ Λόγος')
        print()
        print('\tHowever, I could use --out to provide a custom return string:')
        print('\t\tλογος --out I found λογος at book chapter:verse')
        print('\tAnd the output would look like:')
        print('\t\tI found λογος at John 1:1')
        print()
        print('OUT:')
        print('\tbook\t\t\tThe book the search term was found in.')
        print('\tchapter\t\t\tThe chapter the search term was found in.')
        print('\tclause\t\t\tThe text of the containing clause of the search term.')
        print('\tnum_rows\t\t\tThe total number of occurrences found from the search.')
        print('\tparsing\t\t\tThe parsing for the found term.')
        print('\tverse\t\t\tThe verse the search term was found in.')


def main_loop(gnt_file):
    """The main program."""
    if len(sys.argv) == 1:
        return

    # If any help command is in the string, print the help and quit.
    if '-h' in sys.argv or '--help' in sys.argv:
        h_index = sys.argv.index('-h' if '-h' in sys.argv else '--help')
        help_arg = ''
        if h_index != len(sys.argv) - 1:
            help_arg = sys.argv[h_index + 1]
        print_help(help_arg)
        return

    # If '--out' has been given as an argument, take it and everything after as the string to be given to format
    # output.
    out_format_str = 'book chapter.verse: clause'
    if '--out' in sys.argv:
        out_idx = sys.argv.index('--out')
        if out_idx == len(sys.argv) - 1:
            out_format_str = ''
        else:
            out_format_str = ' '.join(sys.argv[out_idx + 1:])
            del sys.argv[out_idx:]

    args = ' '.join(sys.argv[1:])
    query = query_string_parsing.to_query(args)

    # Load the GNT database.
    gnt_data = json.load(gnt_file)

    # Print the output.
    output_data = query.search(gnt_data)
    for idx, row in output_data:
        print(out_format(out_format_str, row, idx, len(output_data), gnt_data))


def main():
    """The main routine."""
    # Open the dataset and call
    with open(OPEN_GNT_FILEPATH, 'r') as gnt_file:
        main_loop(gnt_file)


if __name__ == '__main__':
    main()
