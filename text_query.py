"""Defines data structures for doing Queries on the text."""

import helpers
import re


class TextQuery:
    """A superclass for different kinds of searches over the text of the NT.
    Should be extended with unique fields and a search() function."""
    def search(self, dataset: list[dict[str, str|int]]) -> list[dict[str, str|int]]:
        """Searches through the given dataset with the fields set up in the class.
        Returns a tuple of row number in the given dataset as well as the actual data."""
        raise NotImplementedError('Call search() from a subclass!')


class AndQuery(TextQuery):
    """A query which performs an AND operation with two queries."""

    def __init__(self, lhs: TextQuery, rhs: TextQuery):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f'<{str(self.lhs)} & {str(self.rhs)}>'

    def search(self, dataset: list[dict[str, str|int]]) -> list[dict[str, str|int]]:
        """Finds the intersection of the two queries."""
        lhs_result = self.lhs.search(dataset)
        rhs_result = self.rhs.search(lhs_result)

        return rhs_result


class OrQuery(TextQuery):
    """A query which performs an OR operation with two queries."""

    def __init__(self, lhs: TextQuery, rhs: TextQuery):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f"<{self.lhs} | {self.rhs}>"

    def search(self, dataset: list[dict[str, str|int]]) -> list[dict[str, str|int]]:
        """Finds the union between the two search results."""
        lhs_result = self.lhs.search(dataset)
        rhs_result = self.rhs.search(dataset)

        lhs_result.extend(rhs_result)
        return lhs_result


class LexemeQuery(TextQuery):
    """Searches by lexeme."""

    def __init__(self, lexeme: str):
        self.lexeme = lexeme
        self.case = None
        self.number = None
        self.gender = None
        self.tense = None
        self.voice = None
        self.mood = None
        self.person = None

    def __str__(self):
        return f'<{self.lexeme}>'  # TODO: make better

    def search(self, dataset: list[dict]) -> list[dict[str, str|int]]:
        """Searches for the given lexeme."""
        # Create a sublist of rows with the given lexeme.
        def matches_lex(row, lex):
            """True if one of the lexemes is matched."""
            # Strip the accents in lexeme.
            stripped = [helpers.strip_accents(x) for x in row['lexeme']]

            for x in stripped:
                if re.match(lex, x):
                    return True
            return False

        lexeme_rows = [
            row for row in dataset if matches_lex(row, self.lexeme)]

        # Further limit based upon other fields if provided.
        if self.case is not None:
            lexeme_rows = [row
                           for row in lexeme_rows
                           if 'case' in row['morph_code'] and self.case == row['morph_code']['case']]
        if self.number is not None:
            lexeme_rows = [row
                           for row in lexeme_rows
                           if 'number' in row['morph_code'] and self.number == row['morph_code']['number']]
        if self.gender is not None:
            lexeme_rows = [row
                           for row in lexeme_rows
                           if 'gender' in row['morph_code'] and self.gender == row['morph_code']['gender']]
        if self.tense is not None:
            lexeme_rows = [row
                           for row in lexeme_rows
                           if 'tense' in row['morph_code'] and self.tense == row['morph_code']['tense']]
        if self.voice is not None:
            lexeme_rows = [
                row
                for row in lexeme_rows
                if 'voice' in row['morph_code'] and self.voice == row['morph_code']['voice']
            ]
        if self.mood is not None:
            lexeme_rows = [
                row
                for row in lexeme_rows
                if 'mood' in row['morph_code'] and self.mood == row['morph_code']['mood']
            ]
        if self.person is not None:
            lexeme_rows = [
                row
                for row in lexeme_rows
                if 'person' in row['morph_code'] and self.person == row['morph_code']['person']
            ]

        return lexeme_rows


class MorphologySearch(TextQuery):
    """Searches by a morphology on the word."""

    def __init__(self, property_string: str, value: str):
        self.property = property_string
        self.value = value

    def __str__(self):
        return f'<Property: {self.property}, {self.value}>'

    def search(self, dataset: list[dict]) -> list[dict]:
        """Searches the dataset for the presence of a given property."""

        return [x for x in dataset if self.property in x['morph_code'] and x['morph_code'][self.property] == self.value]


class AnteQuery(TextQuery):
    """Gets all terms a certain number of terms before the input term."""

    def __init__(self, number: int):
        self.number = number

    def __str__(self):
        return f'<AnteQuery: {self.number}>'

    def search(self, dataset: list[dict]) -> list[dict]:
        result = []
        if self.number == 0:
            return result

        for word in dataset:
            i = word['word_index']
            parent_set = word['parent_set']

            start_index = i - self.number
            if start_index < 0:
                start_index = 0

            result = result + parent_set[start_index:i]
        return result


class PostQuery(TextQuery):
    """Gets all terms a certain number of terms after the input term."""

    def __init__(self, number: int):
        self.number = number

    def __str__(self):
        return f'<PostQuery: {self.number}>'

    def search(self, dataset: list[dict]) -> list[dict]:
        result = []
        if self.number == 0:
            return result

        for word in dataset:
            i = word['word_index']
            parent_set = word['parent_set']

            end_idx = i + self.number
            if end_idx >= len(parent_set):
                end_idx = len(parent_set) - 1

            result = result + parent_set[i+1:end_idx+1]
        return result


class WindowQuery(OrQuery):
    """Gets all terms in a window before and after the input. This is a shorthand for an OrQuery between an ante and
    post."""

    def __init__(self, ante: int, post: int):
        self.ante_num = ante
        self.post_num = post
        super().__init__(AnteQuery(ante), PostQuery(post))

    def __str__(self):
        return f'<WindowSearch: {self.ante_num}, {self.post_num}>'
