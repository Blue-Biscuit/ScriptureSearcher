#!/bin/python3
"""A tool to make complex searches through the OpenGNT database,
to help further biblical studies."""
import json
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


def out_format(
        format_str: str, row: dict[str, str], row_index: int, num_rows: int, gnt_data: list[dict[str, str]]) -> str:
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
    for row in output_data:
        print(out_format(out_format_str, row, row['word_index'], len(output_data), gnt_data))


def main():
    """The main routine."""
    # Open the dataset and call
    with open(OPEN_GNT_FILEPATH, 'r') as gnt_file:
        main_loop(gnt_file)


if __name__ == '__main__':
    main()
