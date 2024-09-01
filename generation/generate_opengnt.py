#!/bin/python3
"""Takes the OpenGNT database and transforms it to an easily searchable JSON model."""

from generation_helpers import get_row_val
import csv
import json
import sys
import os

# Define input and output files relative to the filepath location.
_script_dir_path = os.path.dirname(os.path.abspath(sys.argv[0]))
_proj_root = f'{_script_dir_path}/..'
INPUT_FILE_NAME = f'{_proj_root}/OpenGNT/OpenGNT_version3_3.csv'
OUTPUT_FILE_NAME = f'{_proj_root}/generation/opengnt.json'

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


def interpret_rmac_code(code: str, word: str, idx: int) -> dict:
    """Converts an RMAC code into a list of attributes."""
    result = {}

    # Different mappings for different concepts.
    part_of_speech_map = {
        'N': 'noun',
        'V': 'verb',
        'T': 'article',
        'P': 'pronoun',
        'R': 'pronoun',  # Relative pronoun.
        'A': 'adjective',
        'D': 'pronoun',  # Demonstrative pronoun.
        'I': 'pronoun',  # Interrogative pronoun.
        'F': 'pronoun',  # Reflexive pronoun.
        'X': 'pronoun',  # Indefinite
        'Q': 'pronoun',  # Correlative/interrogative
        'S': 'pronoun',  # Possessive pronoun.
        'K': 'pronoun',  # Correlative pronoun.
        'C': 'pronoun'  # Reciprocal pronoun.
    }
    case_map = {
        'N': 'nominative',
        'G': 'genitive',
        'D': 'dative',
        'A': 'accusative',
        'V': 'vocative'
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
    noun_extras_map = {
        'P': 'proper',
        'T': 'title',
        'L': 'location',
        'G': 'group',
        'LI': 'indeclinable letter'
    }
    tense_map = {
        'A': 'aorist',
        '2A': 'aorist',
        'P': 'present',
        'I': 'imperfect',
        'F': 'future',
        '2R': 'perfect',
        'R': 'perfect',
        '2F': 'future',
        'L': 'pluperfect',
        '2L': 'pluperfect',
        '2P': 'present'
    }
    voice_map = {
        'A': 'active',
        'P': 'passive',
        'O': 'passive',  # This code seems to be for deponent passives.
        'D': 'middle',
        'N': 'middle/passive',
        'E': 'middle/passive',  # I'm unsure what the difference between this and N is.
        'M': 'middle'
    }
    mood_map = {
        'I': 'indicative',
        'P': 'participle',
        'N': 'infinitive',
        'S': 'subjunctive',
        'M': 'imperative',
        'O': 'optative'
    }
    person_map = {
        '1': 'first',
        '2': 'second',
        '3': 'third'
    }
    particle_kind_map = {
        'N': 'negative',
        'I': 'interrogative'
    }
    pronoun_extras = {
        'K': 'elided with και'  # TODO: verify.
    }
    adjective_extras = {
        'C': 'comparative',
        'P': 'proper',
        'G': 'group',
        'NUI': 'indeclinable numeral',
        'S': 'superlative',
        'L': 'location'
    }
    conjunction_extras = {
        'N': 'negative'
    }
    adverb_extras = {
        'K': 'elided with και',
        'I': 'interrogative',
        'N': 'negative',
        'C': 'comparative'
    }
    hebrew_extras = {
        'T': 'title'
    }

    try:
        result['extras'] = []
        # Handle special, indeclinable things.
        if code.startswith('CONJ'):
            result['part_of_speech'] = 'conjunction'
            sections = code.split('-')
            if len(sections) > 1:
                for extra in sections[1]:
                    result['extras'].append(conjunction_extras[extra])
        elif code == 'PREP':
            result['part_of_speech'] = 'preposition'
        elif code.startswith('HEB'):
            result['part_of_speech'] = 'hebrew word'
            sections = code.split('-')
            if len(sections) > 2:
                for extra in sections[1]:
                    result['extras'].append(hebrew_extras[extra])
        elif code == 'ARAM':
            result['part_of_speech'] = 'aramaic word'
        elif code.startswith('ADV'):
            result['part_of_speech'] = 'adverb'

            if len(code) > 3:
                extras = [x for x in code[3:] if x != '-']
                for extra in extras:
                    result['extras'].append(adverb_extras[extra])
        elif code == 'INJ':
            result['part_of_speech'] = 'interjection'
        elif code.startswith('PRT'):
            result['part_of_speech'] = 'particle'
            if len(code) > 4:
                result['kind'] = particle_kind_map[code[4]]

        # Handle normal parts of speech.
        else:
            pos = part_of_speech_map[code[0]]
            result['part_of_speech'] = pos
            if pos == 'noun' or pos == 'article':
                result['case'] = case_map[code[2]]
                result['number'] = number_map[code[3]]
                result['gender'] = gender_map[code[4]]
                if len(code) > 5:
                    sections = code.split('-')
                    if sections[2] == 'LI':
                        result['extras'].append(noun_extras_map[sections[2]])
                    else:
                        for extra in sections[2]:
                            result['extras'].append(noun_extras_map[extra])
            elif pos == 'adjective':
                sections = code.split('-')
                morph = sections[1]

                if morph == 'NUI':
                    result['extras'].append('indeclinable numeral')
                else:
                    result['case'] = case_map[morph[0]]
                    result['number'] = number_map[morph[1]]
                    result['gender'] = gender_map[morph[2]]

                    if len(sections) > 2:
                        if sections[2] == 'NUI':
                            result['extras'].append(adjective_extras[sections[2]])
                        else:
                            for extra in sections[2]:
                                result['extras'].append(adjective_extras[extra])
            elif pos == 'pronoun':
                if code[0] == 'I':
                    result['extras'].append('interrogative')
                elif code[0] == 'R':
                    result['extras'].append('relative')
                elif code[0] == 'D':
                    result['extras'].append('demonstrative')
                elif code[0] == 'F':
                    result['extras'].append('reflexive')
                elif code[0] == 'X':
                    result['extras'].append('indefinite')
                elif code[0] == 'Q':
                    result['extras'].append('correlative or interrogative')
                elif code[0] == 'S':
                    result['extras'].append('possessive')
                elif code[0] == 'K':
                    result['extras'].append('correlative')
                elif code[0] == 'C':
                    result['extras'].append('reciprocal')

                if code[2] == '1' or code[2] == '2' or code[2] == '3':
                    sections = code.split('-')
                    if sections[1][1] == 'S':
                        result['extras'].append('singular')
                        sections[1] = sections[1][0] + sections[1][2:]
                    elif sections[1][1] == 'P':
                        result['extras'].append('plural')
                        sections[1] = sections[1][0] + sections[1][2:]
                    result['person'] = person_map[sections[1][0]]
                    result['case'] = case_map[sections[1][1]]
                    result['number'] = number_map[sections[1][2]]
                    if len(sections[1]) > 3:
                        result['gender'] = gender_map[sections[1][3]]

                    if len(sections) > 2:
                        for extra in sections[2]:
                            result['extras'].append(pronoun_extras[extra])
                else:
                    result['case'] = case_map[code[2]]
                    result['number'] = number_map[code[3]]
                    result['gender'] = gender_map[code[4]]
                    if len(code) > 5:
                        raise ValueError
            elif pos == 'verb':
                offset = 0
                if code[2:4] == '2A' or code[2:4] == '2R' or code[2:4] == '2F' or code[2:4] == '2L' or code[2:4] == '2P':
                    result['extras'].append('second')
                    result['tense'] = tense_map[code[2:4]]
                    offset = 1
                else:
                    result['tense'] = tense_map[code[2]]
                result['tense'] = tense_map[code[offset+2]]
                result['voice'] = voice_map[code[offset+3]]
                mood = result['mood'] = mood_map[code[offset+4]]
                result['mood'] = mood
                if code[offset+3] == 'O':
                    result['extras'].append('deponent')

                if mood == 'indicative' or mood == 'subjunctive' or mood == 'imperative' or mood == 'optative':
                    result['person'] = person_map[code[offset+6]]
                    result['number'] = number_map[code[offset+7]]
                    if len(code) > offset+8:
                        raise ValueError
                elif mood == 'participle':
                    result['case'] = case_map[code[offset+6]]
                    result['number'] = number_map[code[offset+7]]
                    result['gender'] = gender_map[code[offset+8]]
                    if len(code) > offset+9:
                        raise ValueError
                else:
                    if len(code) > offset+5:
                        raise ValueError
            else:
                raise ValueError

    except Exception as e:
        print(f'Invalid RMAC code: {code}; word: {word}; index: {idx}')
        raise e
    return result


def convert_line(row: list[str], idx: int) -> dict:
    """Converts the line to a dictionary."""
    result = {}
    for field in GENERATION_FIELDS:
        if isinstance(field, tuple):
            result[field[1]] = get_row_val(field[0], row)
        elif field == 'rmac':
            result['morph_code'] = interpret_rmac_code(get_row_val('rmac', row), get_row_val('OGNTa', row), idx)
        elif field == 'Book':
            # Transform the book into a string first.
            book_number = int(get_row_val(field, row))
            result[field] = interpret_book_code(book_number)
        elif field == 'lexeme':
            # There's the possibility of there being multiple "options" for the lexeme. So the lexeme stored on
            # υδωρ is "υδωρ, υδατος." In the future, it would be beneficial to figure out whether the lexeme is always
            # the first option. (υδατος not being a lexeme, but a genitive form) But, for now, this problem is here
            # circumvented by registering them both as lexemes.
            lexemes = get_row_val(field, row).split(',')
            lexemes = [x.strip() for x in lexemes]
            result[field] = lexemes
        else:
            result[field] = get_row_val(field, row)

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
    with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as out_f:
        json.dump(gnt_data_json, out_f)


def main():
    """The main routine."""
    with open(INPUT_FILE_NAME, 'r', encoding='utf-8') as f:
        process_file(f)


if __name__ == '__main__':
    main()
