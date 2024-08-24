"""Defines data structures for doing Queries on the text."""

import helpers


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

    def __str__(self):
        return f'<{self.lexeme}>'  # TODO: make better

    def search(self, dataset: list[dict]) -> list[dict[str, str|int]]:
        """Searches for the given lexeme."""
        # Create a sublist of rows with the given lexeme.
        lexeme_rows = [
            row for row in dataset if helpers.strip_accents(row['lexeme']) == self.lexeme]

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

        return lexeme_rows
