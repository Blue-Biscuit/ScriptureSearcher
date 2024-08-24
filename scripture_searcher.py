#!/bin/python3
"""A tool to make complex searches through the OpenGNT database,
to help further biblical studies."""
import json
import sys
import query_string_parsing


OPEN_GNT_FILEPATH = "opengnt.json"
LXX_FILEPATH = 'lxx.json'
APP_NAME = 'SyntaxSearcher'
APP_VERSION = 'alpha'
EXECUTABLE_NAME = 'scripture_searcher.py'


def get_window(word: dict, before: int, after: int) -> str:
    """Gets a window of words from the original dataset."""
    parent_set = word['parent_set']
    book = word['Book']

    # If these flags are high, that means we hit the beginning / end of a book.
    early_before = False
    early_after = False

    # Get relevant indices.
    center_idx = word['word_index']
    left_idx = center_idx - before
    right_idx = center_idx + after

    # Handle the possibility that we went off the edge of the dataset.
    if left_idx < 0:
        early_before = True
        left_idx = 0
    if right_idx >= len(parent_set):
        early_after = True
        right_idx = len(parent_set) - 1

    # Handle the possibility that we leave the current book.
    while parent_set[left_idx]['Book'] != book:
        early_before = True
        left_idx = left_idx + 1
    while parent_set[right_idx]['Book'] != book:
        early_after = True
        right_idx = right_idx - 1

    # Create the window.
    window_words = parent_set[left_idx:right_idx+1]
    text_list = [word['word'] for word in window_words]
    text = f'{"" if early_before else "..."}{" ".join(text_list)}{"" if early_after else "..."}'
    return text


def get_verse(word: dict) -> str:
    """Gets the text of the containing verse."""
    word_index = word['word_index']
    verse_number = word['Verse']
    parent_set = word['parent_set']

    # Find the start of the verse.
    start_verse_index = word_index
    while start_verse_index >= 0 and parent_set[start_verse_index]['Verse'] == verse_number:
        start_verse_index = start_verse_index - 1
    start_verse_index = start_verse_index + 1

    # Find the end of the verse.
    end_verse_index = word_index
    while end_verse_index < len(parent_set) and parent_set[end_verse_index]['Verse'] == verse_number:
        end_verse_index = end_verse_index + 1
    end_verse_index = end_verse_index - 1

    # Return the slice of the words.
    words_from_verse = parent_set[start_verse_index:end_verse_index+1]
    words_string = ' '.join([x['word'] for x in words_from_verse])
    return words_string

def out_format(
        format_str: str, row: dict[str, str | int], num_rows: int) -> str:
    """Conforms output to the given format string."""
    # Book, chapter, and verse.
    result = format_str.replace('book', (row['Book']))
    result = result.replace('chapter', row['Chapter'])
    result = result.replace('verse', row['Verse'])

    # Parsing.
    # result = result.replace('parsing', row['morph_code'])

    # The number of rows returned as a result.
    result = result.replace('num_rows', str(num_rows))

    while 'window' in result:
        result = result.replace('window', get_window(row, 5, 5))
    while 'vss_string' in result:
        result = result.replace('vss_string', get_verse(row))

    return result


def print_help(help_arg: list[str]):
    """Prints help. Takes in argv """
    # If no argument was provided, just print general help.
    if not help_arg:
        print(f'USAGE: {EXECUTABLE_NAME} [ARGS] SEARCH [--out OUT]')
        print("\tPerforms complex searches through the Greek New Testament's and the Septuagint's text.")
        print()
        print('ARGS:')
        print('\t-h | --help H\t\t\tPrints this help and exits. Prints help about a specific part of the program')
        print('\t\t\t\t\tgiven an argument. "-h help" prints possible arguments.')
    elif 'help' == help_arg[0]:
        print(f'USAGE: {EXECUTABLE_NAME} -h H')
        print('\tPrints help about a specific aspect of the program.')
        print()
        print('H:')
        print('\t(empty)\t\t\tPrints help for the general program.')
        print('\thelp\t\t\tPrints help for the help command.')
        print('\tsearch\t\t\tPrints help for searching.')
        print('\tout\t\t\tPrints help for output.')
    elif 'search' == help_arg[0]:
        if len(help_arg) == 1:
            print(f'USAGE: {EXECUTABLE_NAME} SEARCH')
            print("\tSpecifies the specific search on the New Testament and Septuagint's text.")
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
            print('\tThere are different types of searches; to see them, type -h search <search type>')
            print('\tThe search types are as follows:')
            print('\t\tlexeme')
        elif help_arg[1] == 'lexeme':
            print(f'USAGE: {EXECUTABLE_NAME} lexeme LEXEME [ARGS]')
            print('\tSearches for a lexeme in the dataset. Also takes certain arguments which can specify properties.')
            print()
            print('ARGS:')
            print('\t--case C\t\t\tThe case of the lexeme to search.')
            print('\t--number N\t\t\tThe number of the lexeme to search.')
            print('\t--gender G\t\t\tThe gender of the lexeme to search.')
            print('\t--tense T\t\t\tThe tense of the lexeme to search.')
            print('\t--voice V\t\t\tThe voice of the lexeme to search.')
            print('\t--mood M\t\t\tThe mood of the lexeme to search.')
            print('\t--person P\t\t\tThe person of the lexeme to search.')
        else:
            print(f'Unknown search type: {help_arg[1]}')
    elif 'out' == help_arg[0]:
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
        print('\tvss_string\t\t\tThe string of text of the verse in which the word was found.')
    else:
        print(f'Unrecognized help argument: {" ".join(help_arg)}')


def main_loop(gnt_file, lxx_file):
    """The main program."""
    if len(sys.argv) == 1:
        return

    # If any help command is in the string, print the help and quit.
    if '-h' in sys.argv or '--help' in sys.argv:
        h_index = sys.argv.index('-h' if '-h' in sys.argv else '--help')
        help_arg = ''
        if h_index != len(sys.argv) - 1:
            help_arg = sys.argv[h_index + 1:]
        print_help(help_arg)
        return

    # If '--out' has been given as an argument, take it and everything after as the string to be given to format
    # output.
    out_format_str = 'book chapter.verse: vss_string'
    if '--out' in sys.argv:
        out_idx = sys.argv.index('--out')
        if out_idx == len(sys.argv) - 1:
            out_format_str = ''
        else:
            out_format_str = ' '.join(sys.argv[out_idx + 1:])
            del sys.argv[out_idx:]

    args = ' '.join(sys.argv[1:])
    query = query_string_parsing.to_query(args)

    # Load the relevant databases.
    gnt_data = json.load(gnt_file)
    for word in gnt_data:
        word['parent_set'] = gnt_data

    lxx_data = json.load(lxx_file)
    for word in lxx_data:
        word['parent_set'] = lxx_data

    search_data = lxx_data + gnt_data

    # Print the output.
    output_data = query.search(search_data)
    for row in output_data:
        print(out_format(out_format_str, row, len(output_data)))


def main():
    """The main routine."""
    # Open the dataset and call
    with open(OPEN_GNT_FILEPATH, 'r') as gnt_file:
        with open(LXX_FILEPATH, 'r') as lxx_file:
            main_loop(gnt_file, lxx_file)


if __name__ == '__main__':
    main()
