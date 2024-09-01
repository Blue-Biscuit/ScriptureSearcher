#!/bin/python3
"""A script to generate a convenient JSON file from LXX-Rahlfs-1983 dataset."""

import csv
import json
import re
import os
import sys

_script_dir_path = os.path.dirname(os.path.abspath(sys.argv[0]))
_proj_root = f'{_script_dir_path}/..'
_gen_path = f'{_proj_root}/generation'
_lxx_path = f'{_proj_root}/LXX-Rahlfs-1935'
OUT_FILE = f'{_gen_path}/lxx.json'
PATH_TO_LEXEMES = f'{_lxx_path}/12-Marvel.Bible/09-lexemes.csv'
PATH_TO_VERSIFICATION = f'{_lxx_path}/08_versification/ossp/versification_original.csv'
PATH_TO_MORPHOLOGY = f'{_lxx_path}/03a_morphology_with_JTauber_patches/patched_623693.csv'
PATH_TO_WORDLIST = f'{_lxx_path}/01_wordlist_unicode/text_accented.csv'
NUM_WORDS_IN_LXX = 623693


def load_lexemes(lxx_data: list[dict], file):
    reader = csv.reader(file, delimiter='\t')
    for idx, row in enumerate(reader):
        lxx_data[idx]['lexeme'] = [row[1]]


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
        lxx_data[idx]['word'] = row[-1]


def interpret_morphology(lxx_data: list[dict]):
    """Interprets the already loaded morphology codes in a way which agrees with the other Syntax Searcher datasets."""
    for word in lxx_data:
        morph_code = word['morph_code']
        result = {}

        case_map = {
            'N': 'nominative',
            'G': 'genitive',
            'D': 'dative',
            'A': 'accusative',
            'V': 'vocative'
        }
        number_map = {
            'S': 'singular',
            'P': 'plural',
            'D': 'dual'
        }
        gender_map = {
            'M': 'masculine',
            'F': 'feminine',
            'N': 'neuter'
        }
        tense_map = {
            'P': 'present',
            'I': 'imperfect',
            'A': 'aorist',
            'X': 'perfect',
            'F': 'future',
            'Y': 'pluperfect'
        }
        voice_map = {
            'A': 'active',
            'M': 'middle',
            'P': 'passive'
        }
        mood_map = {
            'I': 'indicative',
            'D': 'imperative',
            'P': 'participle',
            'N': 'infinitive',
            'S': 'subjunctive',
            'O': 'optative'
        }
        person_map = {
            '1': 'first',
            '2': 'second',
            '3': 'third'
        }

        # Correct what appear to be typos in the dataset.
        # TODO: look these up in the key and just a bare search to ensure I'm not missing something.
        if 239870 == word['word_index']:
            morph_code = 'V.API3S'
        if 332804 == word['word_index']:
            morph_code = 'A'
        if 335067 == word['word_index']:
            morph_code = 'A.N'
        if 422765 == word['word_index']:
            morph_code = 'V.APS2S'
        if 422848 == word['word_index']:
            morph_code = 'V.PMI3P'
        if 433328 == word['word_index']:
            morph_code = 'N.DSF'
        if 473507 == word['word_index']:
            morph_code = 'A.APN'
        if 483471 == word['word_index']:
            morph_code = 'A.NSM'

        if morph_code == 'P':  # Preposition
            result['part_of_speech'] = 'preposition'
        elif morph_code == 'P+X':  # Preposition with a conjunction. Classifying as conjunction for now.
            result['part_of_speech'] = 'conjunction'
        elif morph_code == 'C':  # Conjunction
            result['part_of_speech'] = 'conjunction'
        elif morph_code == 'X':  # Particle?
            result['part_of_speech'] = 'particle'
        elif morph_code == 'C+X':  # A particle with a conjunction.
            result['part_of_speech'] = 'particle'
        elif morph_code == 'D':  # Adverb
            result['part_of_speech'] = 'adverb'
        elif morph_code == 'D.P':  # Adverb. TODO: Identify what the 'P' is.
            result['part_of_speech'] = 'adverb'
        elif morph_code == 'C+D':  # Adverb + conjunction
            result['part_of_speech'] = 'adverb'
        elif morph_code == 'M':  # A numeral. These are handled as adjectives in OpenGNT.
            result['part_of_speech'] = 'adjective'
        elif morph_code == 'I':  # Interjection
            result['part_of_speech'] = 'interjection'
        elif morph_code == 'N':  # Noun with unknown other things.
            result['part_of_speech'] = 'noun'
        elif morph_code == 'A':
            result['part_of_speech'] = 'adjective'
        elif morph_code == 'A.B':  # I think this is an adjective used adverbially, but unsure. TODO: investigate.
            result['part_of_speech'] = 'adjective'
        elif morph_code == 'RA+A':  # I don't know whether to characterize this as an adj or a pronoun. Going with adj.
            result['part_of_speech'] = 'adjective'
        elif morph_code == 'RI':  # Pronoun with nothing else.
            result['part_of_speech'] = 'pronoun'
        elif re.match('N\\.[NGDAV][SPD][MFN]', morph_code):  # Nouns
            result['part_of_speech'] = 'noun'
            result['case'] = case_map[morph_code[2]]
            result['number'] = number_map[morph_code[3]]
            result['gender'] = gender_map[morph_code[4]]
        elif re.match('RD\\+N\\.[NGDAV][SPD][MFN]', morph_code):  # Nouns + relative. I'm classifying this as a noun for now.
            result['part_of_speech'] = 'noun'
            result['case'] = case_map[morph_code[5]]
            result['number'] = number_map[morph_code[6]]
            result['gender'] = gender_map[morph_code[7]]
        elif re.match('M3M\\.[NGDAV][SPD][MFN]', morph_code):  # TODO: some kind of noun, other than that, not really sure. investigate.
            result['part_of_speech'] = 'noun'
            result['case'] = case_map[morph_code[4]]
            result['number'] = number_map[morph_code[5]]
            result['gender'] = gender_map[morph_code[6]]
        elif re.match('N\\.[NGDAV][SPD]', morph_code):  # TODO: verify. Indeclinable noun.
            result['part_of_speech'] = 'noun'
            result['case'] = case_map[morph_code[2]]
            result['number'] = number_map[morph_code[3]]
        elif re.match('N\\.[SPD]', morph_code):  # Noun without a case; I don't know how this works. TODO: verify.
            result['part_of_speech'] = 'noun'
            result['number'] = number_map[morph_code[2]]
        elif re.match('N\\.[NGDAV] [MFN]', morph_code):  # TODO: verify. I think this is a word of unknown number.
            result['part_of_speech'] = 'noun'
            result['gender'] = gender_map[morph_code[4]]
        elif re.match('N\\.[NGDAV]', morph_code):  # TODO: verify.
            result['part_of_speech'] = 'noun'
            result['case'] = case_map[morph_code[2]]
        elif re.match('A\\.[NGDAV][SPD][MFN]', morph_code):  # Adjectives
            result['part_of_speech'] = 'adjective'
            result['case'] = case_map[morph_code[2]]
            result['number'] = number_map[morph_code[3]]
            result['gender'] = gender_map[morph_code[4]]
        elif re.match('P\\+A\\.[NGDAV][SPD][MFN]', morph_code):  # Adjectives
            result['part_of_speech'] = 'adjective'
            result['case'] = case_map[morph_code[2+2]]
            result['number'] = number_map[morph_code[3+2]]
            result['gender'] = gender_map[morph_code[4+2]]
        elif re.match('RA\\+A\\.[NGDAV][SPD][MFN]', morph_code):  # Adjectives
            result['part_of_speech'] = 'adjective'
            result['case'] = case_map[morph_code[5]]
            result['number'] = number_map[morph_code[6]]
            result['gender'] = gender_map[morph_code[7]]
        elif re.match('A\\.[NGDAV]', morph_code):  # Adjectives
            result['part_of_speech'] = 'adjective'
            result['case'] = case_map[morph_code[2]]
        elif re.match('A\\.[SPD]', morph_code):  # Adjectives
            result['part_of_speech'] = 'adjective'
            result['number'] = number_map[morph_code[2]]
        elif re.match('A[1-9]', morph_code):  # Not really sure at all what the number is for. TODO: investigate.
            result['part_of_speech'] = 'adjective'
        elif re.match('M\\.[NGDAV][SPD][MFN]', morph_code):  # Numeric Adjective
            result['part_of_speech'] = 'adjective'
            result['case'] = case_map[morph_code[2]]
            result['number'] = number_map[morph_code[3]]
            result['gender'] = gender_map[morph_code[4]]
        elif re.match('M\\.[NGDAV][SPD][MFN]', morph_code):  # Numeric Adjective
            result['part_of_speech'] = 'adjective'
            result['case'] = case_map[morph_code[2]]
            result['number'] = number_map[morph_code[3]]
            result['gender'] = gender_map[morph_code[4]]
        elif re.match('M\\.[NGDAV][SPD]', morph_code):  # TODO: verify. I think this is a numeric adjective.
            result['part_of_speech'] = 'adjective'
            result['case'] = case_map[morph_code[2]]
            result['number'] = number_map[morph_code[3]]
        elif re.match('V\\.[PFIAXY][AMP][IDSO][123][SPD]', morph_code):  # Verbs
            result['part_of_speech'] = 'verb'
            result['tense'] = tense_map[morph_code[2]]
            result['voice'] = voice_map[morph_code[3]]
            result['mood'] = mood_map[morph_code[4]]
            result['person'] = person_map[morph_code[5]]
            result['number'] = number_map[morph_code[6]]
        elif re.match('V\\.[PFIAXY][AMP][IDSO]', morph_code):  # Verbs
            result['part_of_speech'] = 'verb'
            result['tense'] = tense_map[morph_code[2]]
            result['voice'] = voice_map[morph_code[3]]
            result['mood'] = mood_map[morph_code[4]]
        elif re.match('V.[PFIAXY][AMP]P[NGDAV][SPD][MFN]', morph_code):  # Participle
            result['part_of_speech'] = 'verb'
            result['tense'] = tense_map[morph_code[2]]
            result['voice'] = voice_map[morph_code[3]]
            result['mood'] = mood_map[morph_code[4]]
            result['case'] = case_map[morph_code[5]]
            result['number'] = number_map[morph_code[6]]
            result['gender'] = gender_map[morph_code[7]]
        elif re.match('V.[PFIAXY][AMP]P', morph_code):  # Participle
            result['part_of_speech'] = 'verb'
            result['tense'] = tense_map[morph_code[2]]
            result['voice'] = voice_map[morph_code[3]]
            result['mood'] = mood_map[morph_code[4]]
        elif re.match('V\\.[PFIAXY][AMP]N', morph_code):  # Infinitive
            result['part_of_speech'] = 'verb'
            result['tense'] = tense_map[morph_code[2]]
            result['voice'] = voice_map[morph_code[3]]
            result['mood'] = mood_map[morph_code[4]]
        elif re.match('RA\\.[NGDAV][SPD][MFN]', morph_code):  # The article
            result['part_of_speech'] = 'article'
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
            result['gender'] = gender_map[morph_code[5]]
        elif re.match('RR\\.[NGDAV][SPD][MFN]', morph_code):  # The relative pronoun
            result['part_of_speech'] = 'pronoun'
            result['extras'] = ['relative']
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
            result['gender'] = gender_map[morph_code[5]]
        elif re.match('RA\\.[NGDAV][SPD]', morph_code):  # The relative pronoun
            result['part_of_speech'] = 'pronoun'
            result['extras'] = ['relative']
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
        elif re.match('RD\\.[NGDAV][SPD][MFN]', morph_code):  # The third-person pronoun
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
            result['gender'] = gender_map[morph_code[5]]
        elif re.match('C\\+RD\\.[NGDAV][SPD][MFN]', morph_code):  # The third-person pronoun, plus conj.
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[5]]
            result['number'] = number_map[morph_code[6]]
            result['gender'] = gender_map[morph_code[7]]
        elif re.match('RD\\.[NGDAV][SPD]', morph_code):  # The third-person pronoun
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
        elif re.match('RP.[NGDAV][SPD]', morph_code):  # The second-person pronoun.
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
        elif re.match('RI\\.[NGDAV][SPD][MFN]', morph_code):  # The interrogative pronoun.
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
            result['gender'] = gender_map[morph_code[5]]
        elif re.match('RI\\.[NGDAV]', morph_code):  # The interrogative pronoun.
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[3]]
        elif re.match('RX\\.[NGDAV][SPD][MFN]', morph_code):  # The pronoun TODO: figure out what kind
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[3]]
            result['number'] = number_map[morph_code[4]]
            result['gender'] = gender_map[morph_code[5]]
        elif re.match('C\\+RP\\.[NGDAV][SPD]', morph_code):  # conj + a relative pronoun.
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[5]]
            result['number'] = number_map[morph_code[6]]
        elif re.match('RP\\+X\\.[NGDAV][SPD]', morph_code):  # particle + a relative pronoun.
            result['part_of_speech'] = 'pronoun'
            result['case'] = case_map[morph_code[5]]
            result['number'] = number_map[morph_code[6]]
        else:
            raise ValueError(f'Unknown morphology code: {morph_code}; word: {word["word"]}; idx: {word["word_index"]}/{len(lxx_data)}')

        word['morph_code'] = result


def to_stats(dataset: list[dict]) -> dict:
    book_names = []
    chapter_limits = {}
    for i, x in enumerate(dataset):
        book = x['Book']
        if book not in book_names:
            book_names.append(book)
        if i >= len(dataset) - 1 or (book != dataset[i+1]['Book'] or dataset[i]['Chapter'] != dataset[i+1]['Chapter']):
            if book not in chapter_limits:
                chapter_limits[book] = {}
            chapter_limits[book][x['Chapter']] = x['Verse']

    return {
        'book_names': book_names,
        'chapter_limits': chapter_limits
    }


def main():
    """The main routine."""
    # Initialize the dataset with just word indices. BEWARE! The actual dataset
    # is one-indexed. But we don't want the dataset used by the search app to be one-indexed.
    print('Initializing dataset...')
    lxx_data = [{'word_index': i} for i in range(NUM_WORDS_IN_LXX)]

    # Load wordlist.
    print('Loading word list...')
    with open(PATH_TO_WORDLIST, 'r', encoding='utf-8') as wordlist_file:
        load_word(lxx_data, wordlist_file)

    # Load lexemes.
    print('Loading lexemes...')
    with open(PATH_TO_LEXEMES, 'r', encoding='utf-8') as lexemes_file:
        load_lexemes(lxx_data, lexemes_file)

    # Get references.
    print('Loading versification...')
    with open(PATH_TO_VERSIFICATION, 'r', encoding='utf-8') as versification_file:
        load_versification(lxx_data, versification_file)

    # Load morphology codes.
    print('Loading morphology...')
    with open(PATH_TO_MORPHOLOGY, 'r', encoding='utf-8') as morph_file:
        load_morphology(lxx_data, morph_file)

    # Interpret morphology codes.
    print('Interpreting morphology...')
    interpret_morphology(lxx_data)

    # Dump to json.
    print('Writing result...')
    with open(OUT_FILE, 'w') as f:
        json.dump(lxx_data, f)

    # Dump statistics.
    print('Writing statistics...')
    with open('lxx_stats.json', 'w') as f:
        json.dump(to_stats(lxx_data), f)

    print('Done!')


if __name__ == '__main__':
    main()
