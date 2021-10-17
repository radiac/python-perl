from __future__ import annotations

from typing import List, Optional, Type, TypeVar, Union


T = TypeVar("T", bound="Item")


class ChainError(Exception):
    """
    Problem with the chain
    """

    pass


class IteratorEmptyError(ChainError):
    """
    Expected iterator to contain at least one value
    """

    pass


class Item:
    """
    Item in a chain linked list
    """

    _next: Optional[Item]
    _prev: Optional[Item]

    def __init__(self, *args, **kwargs):
        self._next = None
        self._prev = None

    @classmethod
    def from_iterator(cls: Type[T], iterator) -> T:
        """
        Given an iterator, turn it into a chain and return the first item (or None if
        there is no first item)
        """
        try:
            start = cls(next(iterator))
        except StopIteration:
            raise IteratorEmptyError("Expected iterator to contain at least one value")

        item = start
        for raw in iterator:
            item._next = cls(raw)
            item._next._prev = item
            item = item._next

        # Give subclasses an opportunity to perform an action on a new chain
        start._from_iterator_complete()

        return start

    def _from_iterator_complete(self):
        """
        Called once from_iterator has completed building a new chain
        """
        pass

    @property
    def next(self) -> Optional[Item]:
        return self._next

    @next.setter
    def next(self, item: Optional[Item]) -> None:
        """
        Set next in chain to new item, detach whatever was next
        """
        # Break backwards chain for next
        if self._next:
            self._next._prev = None

        # Set item as next
        self._next = item

        # Tell item about its prev
        if item:
            item._prev = self

        self.validate()

    @property
    def prev(self) -> Optional[Item]:
        return self._prev

    @prev.setter
    def prev(self, item: Optional[Item]) -> None:
        """
        Set prev in chain to new item, detach whatever was prev
        """
        # Break forward chain for prev
        if self._prev:
            self._prev._next = None

        # Set item as prev
        self._prev = item

        # Tell item about its next
        if item:
            item._next = self

        self.validate()

    @property
    def first(self):
        tok = self
        prev_tok = self
        while prev_tok:
            tok = prev_tok
            prev_tok = tok._prev
        return tok

    @property
    def last(self):
        tok = self
        next_tok = self
        while next_tok:
            tok = next_tok
            next_tok = tok._next
        return tok

    def __iter__(self):
        """
        Iterate over the rest of the chain
        """
        item = self
        while item:
            yield item
            item = item.next

    def validate(self):
        """
        Validate this chain - check there are no infinite loops
        """
        seen = {self}

        # Look backwards
        item = self._prev
        while item:
            if item._prev in seen:
                raise ChainError(f"Invalid chain: {item} appears more than once")
            item = item._prev
            if item is None:
                break
            seen.add(item)

        # Look forwards
        item = self._next
        while item:
            if item._next in seen:
                raise ChainError(f"Invalid chain: {item} appears more than once")
            item = item._next
            if item is None:
                break
            seen.add(item)

        return True

    def get(self, distance: int):
        """
        Return the Item ``distance`` away (inclusive), stopping at the first/last item
        """
        tok = self
        while distance > 0 and tok._next:
            tok = tok._next
            distance -= 1

        while distance < 0 and tok._prev:
            tok = tok._prev
            distance += 1
        return tok

    def to_list(
        self, start: Union[Item, int, None] = None, end: Union[Item, int, None] = None
    ) -> List:
        """
        Return Items as a list.

        Arguments:
            start   Item    Start at this Item
                    int     Start this far forward or back from this Item
                    None    Start here

            end     Item    End at this Item
                    int     End this far forward or back from this Item
                    None    End here

        The start and end are inclusive (returned in the list)
        """
        # Convert start and end to Item
        start = self._pos_to_item(start)
        end = self._pos_to_item(end)

        toks = []
        tok: Optional[Item] = start
        while tok:
            toks.append(tok)
            if tok == end:
                break
            tok = tok._next
        return toks

    def _pos_to_item(self, pos: Union[Item, int, None]) -> Item:
        """
        Arguments:
            pos     Item    Specified Item
                    int     This far forward or back from this Item
                    None    Here
        """
        item: Item
        if isinstance(pos, int):
            item = self.get(pos)
        elif pos is None:
            item = self
        else:
            # We've handled the other two type options, must be an item
            item = pos
        return item

    def insert(self, chain: Item) -> None:
        """
        Insert a chain after this item
        """
        # Attach end of chain to the start of the next item
        chain_last = chain.last
        chain_last._next = self._next
        if self._next:
            self._next._prev = chain_last

        # Attach start of chain to end of this item
        self._next = chain
        chain._prev = self

        self.validate()

    def replace(
        self,
        chain: Item,
        start: Union[Item, int, None] = None,
        end: Union[Item, int, None] = None,
    ) -> None:
        """
        Replace the start, end and everything in between with the chain starting with
        chain
        """
        start = self._pos_to_item(start)
        end = self._pos_to_item(end)

        if start._prev:
            start._prev._next = chain
            chain._prev = start._prev
        if end._next:
            chain_last = chain.last
            end._next._prev = chain_last
            chain_last._next = end._next

        self.validate()

    def delete(
        self, start: Union[Item, int, None] = None, end: Union[Item, int, None] = None
    ):
        """
        Delete start and end and everything in between
        """
        start = self._pos_to_item(start)
        end = self._pos_to_item(end)

        if start._prev:
            start._prev._next = end._next
        if end._next:
            end._next._prev = start._prev

        self.validate()
