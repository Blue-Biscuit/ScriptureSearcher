"""Defines data structures for doing Queries on the text."""

import helpers


class TextQuery:
    """A superclass for different kinds of searches over the text of the NT.
    Should be extended with unique fields and a search() function."""
    def search(self, dataset: list[list[str]]) -> list[list[str]]:
        """Searches through the given dataset with the fields set up in the class."""
        raise NotImplementedError('Call search() from a subclass!')


class LexemeQuery(TextQuery):
    """Searches by lexeme."""

    def __init__(self, lexeme: str):
        self.lexeme = lexeme
        self.case = None
        self.number = None
        self.gender = None

    def search(self, dataset: list[list[str]]) -> list[list[str]]:
        """Searches for the given lexeme."""
        # Create a sublist of rows with the given lexeme.
        lexeme_rows = [row for row in dataset if helpers.get_row_val('lexeme', row) == self.lexeme]

        # Further limit based upon other fields if provided.
        if self.case is not None:
            lexeme_rows = [row
                           for row in lexeme_rows
                           if self.case in helpers.interpret_rmac_code(helpers.get_row_val('rmac', row))]
        if self.number is not None:
            lexeme_rows = [row
                           for row in lexeme_rows
                           if self.number in helpers.interpret_rmac_code(helpers.get_row_val('rmac', row))]
        if self.gender is not None:
            lexeme_rows = [row
                           for row in lexeme_rows
                           if self.gender in helpers.interpret_rmac_code(helpers.get_row_val('rmac', row))]

        return lexeme_rows