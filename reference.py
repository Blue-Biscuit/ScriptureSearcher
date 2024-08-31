"""Defines types related to handling chapter/verse references."""
import re

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
                char_idx = -1
                for i, c in enumerate(verse_part):
                    if not c.isdigit():
                        char_idx = i
                        break
                verse_letter = verse_part[char_idx:]
                verse_part = verse_part[0:char_idx]

            result = Reference(int(chapter_part), int(verse_part), verse_letter)

        else:
            result = Reference(int(string))

        return result