#!/bin/python3
"""A script to generate a convenient JSON file from LXX-Rahlfs-1983 dataset."""

import csv
import json

OUT_FILE = 'lxx.json'
PATH_TO_LEXEMES = 'LXX-Rahlfs-1935/12-Marvel.Bible/09-lexemes.csv'
PATH_TO_VERSIFICATION = 'LXX-Rahlfs-1935/08_versification/ossp/versification_original.csv'
PATH_TO_MORPHOLOGY = 'LXX-Rahlfs-1935/03a_morphology_with_JTauber_patches/patched_623693.csv'
PATH_TO_WORDLIST = 'LXX-Rahlfs-1935/01_wordlist_unicode/text_accented.csv'
NUM_WORDS_IN_LXX = 623693


def load_lexemes(lxx_data: list[dict], file):
    reader = csv.reader(file, delimiter='\t')
    for idx, row in enumerate(reader):
        lxx_data[idx]['lexeme'] = row[1]


def load_versification(lxx_data: list[dict], file):
    reader = csv.reader(file, delimiter='\t')
    current_line = next(reader)
    current_versification = current_line[1].split('.')
    next_line = next(reader)
    next_word_number = int(next_line[0])
    next_versification = next_line[1].split('.')
    for word in lxx_data:
        # Get what "word number" this is in the LXX dataset. Remember, the LXX dataset is one-indexed.
        word_num = word['word_index'] + 1

        # If our current word number is equal to the starting word number of the next verse, than change the current
        # versification scheme.
        if word_num == next_word_number:
            # Move the next versification to the current.
            current_versification = next_versification

            # Update the next line.
            next_line = next(reader, None)
            if next_line is None:
                next_versification = None
                next_word_number = (2**64)-1  # integer max
            else:
                next_versification = next_line[1].split('.')
                next_word_number = int(next_line[0])

        # Assign the fields for the versification.
        word['Book'] = current_versification[0]
        word['Chapter'] = current_versification[1]
        word['Verse'] = current_versification[2]


def load_morphology(lxx_data: list[dict], file):
    reader = csv.reader(file, delimiter='\t')
    for idx, row in enumerate(reader):
        lxx_data[idx]['morph_code'] = row[1]


def load_word(lxx_data: list[dict], file):
    reader = csv.reader(file, delimiter='\t')
    for idx, row in enumerate(reader):
        lxx_data[idx]['word'] = row[1]


def main():
    """The main routine."""
    # Initialize the dataset with just word indices. BEWARE! The actual dataset
    # is one-indexed. But we don't want the dataset used by the search app to be one-indexed.
    print('Initializing dataset...')
    lxx_data = [{'word_index': i} for i in range(NUM_WORDS_IN_LXX)]

    # Load wordlist.
    print('Loading word list...')
    with open(PATH_TO_WORDLIST, 'r') as wordlist_file:
        load_word(lxx_data, wordlist_file)

    # Load lexemes.
    print('Loading lexemes...')
    with open(PATH_TO_LEXEMES, 'r') as lexemes_file:
        load_lexemes(lxx_data, lexemes_file)

    # Get references.
    print('Loading versification...')
    with open(PATH_TO_VERSIFICATION, 'r') as versification_file:
        load_versification(lxx_data, versification_file)

    # Load morphology codes.
    print('Loading morphology...')
    with open(PATH_TO_MORPHOLOGY, 'r') as morph_file:
        load_morphology(lxx_data, morph_file)

    # Dump to json.
    print('Writing result...')
    with open(OUT_FILE, 'w') as f:
        json.dump(lxx_data, f)

    print('Done!')


if __name__ == '__main__':
    main()
