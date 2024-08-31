"""Defines types related to handling chapter/verse references."""
import re

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
        self.verse_number = verse_number
        self.verse_letter = verse_letter

    @staticmethod
    def is_reference(string: str) -> bool:
        """True if the input is the correct format for a chapter/verse reference."""
        regex = re.compile('[0-9]+([.:][0-9]+[a-z]?)?')
        return bool(regex.match(string))

    def __eq__(self, other: 'Reference'):
        return (self.chapter_number == other.chapter_number
                and self.verse_number == other.verse_number
                and self.verse_letter == other.verse_letter)

    def __lt__(self, other: 'Reference'):
        """A reference that is "less than" another is defined as one which comes in a book first."""
        # Deal with the chapter and verse number, since these are easier.
        if self.chapter_number >= other.chapter_number:
            return False
        elif self.verse_number >= other.verse_number:
            return False

        # If the second character is None but the first is not, then that means the second is earlier (hasn't gotten
        # to characters yet).
        if self.verse_letter is not None and other.verse_letter is None:
            return False

        # If both are None, then these are equivalent.
        if self.verse_letter is None and other.verse_letter is None:
            return False

        # Otherwise, compare ord() values (these should all be ASCII).
        return ord(self.verse_letter) < ord(other.verse_letter)

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self < other and not self == other

    def __ge__(self, other):
        return self > other or self == other

    def __str__(self):
        return f'{self.chapter_number}.{self.verse_number}' + self.verse_letter if self.verse_letter is not None else ''

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

            # If there are characters in the verse part, we need to separate that out from the integer part.
            if re.match('.*[a-z]', verse_part):
                verse_part, verse_letter = _split_verse_into_num_and_char(verse_part)

            result = Reference(int(chapter_part), int(verse_part), verse_letter)

        else:
            result = Reference(int(string))

        return result

class CompoundReference:
    """A reference range (so 1.1-2)."""
    def __init__(self, from_ref: Reference, to_ref: Reference):
        if from_ref >= to_ref:
            raise ValueError(f'References must be from lesser to greater (found {str(from_ref)}-{str(to_ref)})')

        self.from_ref = from_ref
        self.to_ref = to_ref

    @staticmethod
    def is_compound_reference(string: str) -> bool:
        """True if the string is the correct format for a compound reference."""
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
        # Assert that this is of the correct format.
        string = string.strip()
        if not CompoundReference.is_compound_reference(string):
            raise ValueError(f'Not a valid compound reference: {string}')

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
