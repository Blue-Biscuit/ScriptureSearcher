"""Defines types related to handling chapter/verse references."""
import re

import helpers
from helpers import assert_non_null


def _split_verse_into_num_and_char(verse_string: str) -> (str, str):
    """Splits the given verse number (and ONLY verse number) into a number and char."""
    char_idx = -1
    for i, c in enumerate(verse_string):
        if not c.isdigit():
            char_idx = i
            break
    verse_letter = verse_string[char_idx:]
    verse_part = verse_string[0:char_idx]

    return verse_part, verse_letter

class Reference:
    """A single chapter/verse reference (so no 1.1-2)."""
    def __init__(self, chapter_number: int, verse_number: int = None, verse_letter: str = None):
        self.chapter_number = chapter_number
        self.verse_number: str | None = verse_number
        self.verse_letter: str | None = verse_letter

    @staticmethod
    def is_reference(string: str) -> bool:
        """True if the input is the correct format for a chapter/verse reference."""
        regex = re.compile('[0-9]+([.:][0-9]+[a-z]?)?')
        return bool(regex.match(string))

    def is_chapter(self) -> bool:
        """True if this instance is just a chapter."""
        return self.verse_number is None

    def __eq__(self, other: 'Reference'):
        return (self.chapter_number == other.chapter_number
                and self.verse_number == other.verse_number
                and self.verse_letter == other.verse_letter)

    def __lt__(self, other: 'Reference'):
        """A reference that is "less than" another is defined as one which comes in a book first."""
        # Deal with the chapter; this is the only easy one.
        if self.chapter_number > other.chapter_number:
            return False

        # Deal with the verse number. If either is simply a chapter reference, then simply compare the chapter numbers.
        # Otherwise, if the verse is bigger, fail out.
        elif self.is_chapter() or other.is_chapter():
            return self.chapter_number < other.chapter_number
        elif self.verse_number > other.verse_number:
            return False

        # If both verse letters are none, then compare the equality of the verse number for the result.
        elif self.verse_letter is None and other.verse_letter is None:
            return self.verse_number != other.verse_number

        # If either are None, then return true if it is the second one (because if a letter is specified, that
        # means that it comes later. 30 is earlier in the document than 30a, theoretically).
        elif None in (self.verse_letter, other.verse_letter):
            return other.verse_letter is None

        # Otherwise, compare ord() values (these should all be ASCII).
        else:
            # noinspection PyTypeChecker
            return ord(self.verse_letter) < ord(other.verse_letter)

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self < other and not self == other

    def __ge__(self, other):
        return self > other or self == other

    def __str__(self):
        if self.verse_number is None:
            return str(self.chapter_number)
        else:
            return f'{self.chapter_number}.{self.verse_number}{self.verse_letter if self.verse_letter is not None else ""}'

    def __contains__(self, item):
        """True if this reference encompasses the input."""
        result = False

        # If this instance is just a chapter, return true if this encompasses that chapter.
        if self.is_chapter():
            # If the input is a single reference, return true if the chapter is the same.
            if type(item) is Reference:
                result = item.chapter_number == self.chapter_number

            # If the input is a compound reference, return true if the chapter entirely encompasses the reference.
            elif type(item) is CompoundReference:
                from_ref = item.from_ref
                to_ref = item.to_ref
                result = from_ref.chapter_number == self.chapter_number and to_ref.chapter_number == self.chapter_number

        # Otherwise, just compare the input to see if it precisely matches.
        else:
            if type(item) is Reference:
                result = item == self
            elif type(item) is CompoundReference:
                result = not item.is_range() and item.from_ref.chapter_number == self.chapter_number

        return result

    @staticmethod
    def from_str(string: str) -> 'Reference':
        """Builds a reference from a string representation. This accepts either ":" or "." as the chapter/verse
        separator. This can be either chapter and verse (so 31.5a) or just chapter (31)."""
        # Assert that the string is the right format for a reference.
        string = string.strip()
        if not Reference.is_reference(string):
            raise ValueError(f'String not a valid reference: {string}')

        # Determine how the input was structured.
        if ':' in string:
            separator_index = string.index(':')
            has_verse = True
        elif '.' in string:
            separator_index = string.index('.')
            has_verse = True
        else:
            separator_index = -1
            has_verse = False

        # Parse the verse.
        if has_verse:
            chapter_part = string[0:separator_index]
            verse_part = string[separator_index+1:]
            verse_letter = None

            # In some books in the LXX, there is a weird occurrence where sometimes a verse has a '/' in it. I presume
            # this is because of different numbering systems. A
            if '/' in verse_part:
                verse_part = verse_part[0:verse_part.index('/')]

            # If there are characters in the verse part, we need to separate that out from the integer part.
            if re.match('.*[a-z]', verse_part):
                verse_part, verse_letter = _split_verse_into_num_and_char(verse_part)

            result = Reference(int(chapter_part), int(verse_part), verse_letter)

        else:
            result = Reference(int(string))

        return result

class CompoundReference:
    """A reference which may include a destination reference."""
    def __init__(self, from_ref: Reference, to_ref: Reference = None):
        assert_non_null(from_ref, 'from_ref')
        if to_ref is None:
            to_ref = from_ref

        self.from_ref = from_ref
        self.to_ref = to_ref

    def __str__(self):
        if self.is_range():
            return f'{str(self.from_ref)}-{self.to_ref}'
        else:
            return str(self.from_ref)

    def __contains__(self, item):
        # If the current instance is not a range, then just check if the input is contained within the lhs.
        if not self.is_range():
            result = item in self.from_ref

        # If this is not a range, or if it is a Reference, check if it is within the bounds.
        elif type(item) is Reference or (type(item) is CompoundReference and not item.is_range()):
            ref = item
            if type(item) is CompoundReference:
                ref = item.from_ref

            result = self.from_ref <= ref <= self.to_ref

        # If this is a range, then check if it is a subset of the current instance.
        else:
            result = item.from_ref >= self.from_ref and item.to_ref <= self.to_ref

        return result

    def is_range(self) -> bool:
        """True if this has a destination."""
        return self.from_ref != self.to_ref

    @staticmethod
    def is_compound_reference(string: str) -> bool:
        """True if the string is the correct format for a compound reference. Note that this does not mean that it
        is unparsable, as CompoundReference doesn't have to store a destination. CompoundReference can parse everything
        Reference can."""
        # Ensure that '-' is in the string (it must be for this to be a compound reference)
        if '-' not in string:
            return False

        # Check if the first half is a reference.
        dash_idx = string.index('-')
        if not Reference.is_reference(string[0:dash_idx]):
            return False

        # Check that the second half is just an integer or if it's another reference.
        after_dash = string[dash_idx+1:]
        if not (re.match('[0-9]+[a-z]?', after_dash) or Reference.is_reference(after_dash)):
            return False

        return True

    @staticmethod
    def from_str(string: str) -> 'CompoundReference':
        """Parses the reference range."""
        # If this is not specifically a compound reference, try to parse it as a Reference.
        string = string.strip()
        if not CompoundReference.is_compound_reference(string):
            if not Reference.is_reference(string):
                raise ValueError(f'Not a valid reference: {string}')
            ref = Reference.from_str(string)
            return CompoundReference(ref)

        # Parse everything up until the '-' as a regular reference.
        dash_idx = string.index('-')
        from_ref = Reference.from_str(string[0:dash_idx])

        # Parse after the dash, either as just a verse specifier or as a full reference.
        after_dash = string[dash_idx+1:]
        if re.match('[0-9]+[a-z]?', after_dash):
            if re.match('.*[a-z]', after_dash):
                verse_number, verse_char = _split_verse_into_num_and_char(after_dash)
            else:
                verse_number = after_dash
                verse_char = None
            to_ref = Reference(from_ref.chapter_number, int(verse_number), verse_char)

        elif Reference.is_reference(after_dash):
            to_ref = Reference.from_str(after_dash)

        else:
            raise ValueError(f'Not a valid compound reference: {string}')

        return CompoundReference(from_ref, to_ref)

class BookReference:
    """A CompoundReference with a book."""
    def __init__(self, book: str, reference: CompoundReference = None):
        helpers.assert_non_null(book, 'book')
        self.book = book
        self.reference = reference  # Reference can be None; that means the whole book.

    def __str__(self):
        if self.is_book_reference():
            return self.book
        else:
            return f'{self.book} {str(self.reference)}'

    def __contains__(self, item: 'BookReference'):
        if self.is_book_reference():
            return self.book == item.book
        else:
            return self.book == item.book and item.reference in self.reference

    def is_book_reference(self) -> bool:
        """True if the reference is just a book."""
        return self.reference is None

    def is_range(self) -> bool:
        """True if this reference specifies a range."""
        return not self.is_book_reference() and self.reference.is_range()

    @staticmethod
    def from_str(string: str):
        """Builds a BookReference from a string."""
        string = string.strip()
        tokens = string.split()  # The first token will be the book name. Second will be a reference, if present.

        # Argument checking.
        if len(tokens) == 0 or len(tokens) > 2:
            raise ValueError(f'Invalid BookReference: "{string}"')

        # If this is only a book, parse it as such.
        if len(tokens) == 1:
            return BookReference(tokens[0])

        # If this a book and a reference, parse both.
        else:  # len(tokens) = 2
            return BookReference(tokens[0], CompoundReference.from_str(tokens[1]))

if __name__ == '__main__':
    print(str(Reference(1, 1)))
    print(str(Reference(1, 1, 'a')))
    print(str(Reference(1)))
    print(Reference(1, 1, 'a') < Reference(1, 1, 'b'))