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


class WinnowSearch(TextQuery):
    """A search which winnows down its input based upon a condition. This is abstract, and should not be used
    of itself, but through a subclass."""
    def search(self, dataset: list[dict]) -> list[dict]:
        winnow_result = [x for x in dataset if self.winnow(x)]
        result = self.post_winnow(winnow_result)
        return result

    def winnow(self, x: dict):
        """Return true if 'x' should be in the result."""
        raise NotImplementedError("Don't use WinnowSearch directly! Use a subclass!")

    def post_winnow(self, dataset: list[dict]) -> list[dict]:
        """This method can be overridden if transforms are desired to be done to the dataset after winnowing it."""
        return dataset


class LexemeQuery(WinnowSearch):
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

    def winnow(self, x: dict):
        """Should be in the result if x matches the internal lexeme."""
        stripped = [helpers.strip_accents(y) for y in x['lexeme']]
        for y in stripped:
            if re.match(self.lexeme, y):
                return True
        return False

    def post_winnow(self, dataset: list[dict]) -> list[dict]:
        if self.case is not None:
            dataset = [row
                           for row in dataset
                           if 'case' in row['morph_code'] and self.case == row['morph_code']['case']]
        if self.number is not None:
            dataset = [row
                           for row in dataset
                           if 'number' in row['morph_code'] and self.number == row['morph_code']['number']]
        if self.gender is not None:
            dataset = [row
                           for row in dataset
                           if 'gender' in row['morph_code'] and self.gender == row['morph_code']['gender']]
        if self.tense is not None:
            dataset = [row
                           for row in dataset
                           if 'tense' in row['morph_code'] and self.tense == row['morph_code']['tense']]
        if self.voice is not None:
            dataset = [
                row
                for row in dataset
                if 'voice' in row['morph_code'] and self.voice == row['morph_code']['voice']
            ]
        if self.mood is not None:
            dataset = [
                row
                for row in dataset
                if 'mood' in row['morph_code'] and self.mood == row['morph_code']['mood']
            ]
        if self.person is not None:
            dataset = [
                row
                for row in dataset
                if 'person' in row['morph_code'] and self.person == row['morph_code']['person']
            ]
        return dataset


class MorphologySearch(WinnowSearch):
    """Searches by a morphology on the word."""

    def __init__(self, property_string: str, value: str):
        self.property = property_string
        self.value = value

    def __str__(self):
        return f'<Property: {self.property}, {self.value}>'

    def winnow(self, x: dict) -> bool:
        return self.property in x['morph_code'] and x['morph_code'][self.property] == self.value


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
