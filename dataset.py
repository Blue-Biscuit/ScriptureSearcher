"""A class which handles the search dataset."""
from helpers import assert_non_null
from reference import BookReference, CompoundReference


class Dataset:
    """ScriptureSearcher data, whether loaded or from the result of a search."""
    def __init__(self, data: list[dict], stats: dict):
        assert_non_null(data, 'data')
        assert_non_null(stats, 'stats')
        self.data = data
        self.stats = stats

    def get_chapter_limit(self, book: str, chapter: int|str) -> int:
        """Gets the largest verse in a chapter from the stats."""
        # Get the value from the list.
        return int(self.stats['chapter_limits'][book][str(chapter)])

    def get_book_limit(self, book: str) -> (int, int):
        """Gets the largest (chapter, verse) in a book."""
        # Get all chapters and verses from the stats.
        chapters = [int(x) for x in self.stats['chapter_limits'][book].keys()]
        largest_chapter = max(chapters)
        return largest_chapter, self.get_chapter_limit(book, largest_chapter)


    def get_from_reference(self, reference: BookReference) -> 'Dataset':
        """Gets the data at the reference and packages it into another Dataset instance."""
        start_idx = None
        end_idx = 0
        for i, word in enumerate(self.data):
            # Update end_idx; if we haven't ended the loop, we haven't found the end yet.
            end_idx = i

            # Package this word's data as a Reference.
            # The string-packing is done here because doing it this way does all the parsing for me on the verse
            # field. There is a more efficient way to do this.
            word_reference = BookReference.from_str(f'{word["Book"]} {word["Chapter"]}.{word["Verse"]}')

            # If this is the first time we've been "in" the reference passed-in, then flag this as the start index.
            if start_idx is None and word_reference in reference:
                start_idx = i

            # If we have since fallen out of the reference, then stop the loop.
            elif start_idx is not None and word_reference not in reference:
                break

        # Return a slice.
        return Dataset(reference[start_idx:end_idx], self.stats)

    def __getitem__(self, item: int | BookReference) -> dict|'Dataset':
        """Implements the array indexing operator. This can do a couple of things. It can get by index in the dataset,
        or it can search by actual book reference, depending on input type."""
        if type(item) is int:
            return self.data[item]
        elif type(item) is BookReference:
            self.get_from_reference(item)
        else:
            raise TypeError('Unrecognized type for Dataset getitem input.')
