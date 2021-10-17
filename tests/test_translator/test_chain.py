from perl.chain import Item as BaseItem


class Item(BaseItem):
    """
    Thin wrapper around the normal Item class to make debugging easier
    """

    def __init__(self, uid):
        self.uid = uid
        super().__init__(uid)

    def __repr__(self):
        return f"<perl.chain.Item: {self.uid}>"


def gen_chain(n, chain=None):
    items = []
    for i in range(n):
        # Label the items to make debugging easier
        if chain:
            uid = f"[{chain}] {i}"
        else:
            uid = i

        item = Item(uid)
        if not i:
            items.append(item)
            continue
        items[-1].next = item
        items.append(item)
    return items


def test_item__add_by_next():
    item1 = Item(1)
    item2 = Item(2)
    item1.next = item2
    assert item1.prev is None
    assert item1.next == item2
    assert item2.prev == item1
    assert item2.next is None


def test_item__add_by_prev():
    item1 = Item(1)
    item2 = Item(2)
    item2.prev = item1
    assert item1.prev is None
    assert item1.next == item2
    assert item2.prev == item1
    assert item2.next is None


def test_item__set_next_when_next_exists__next_replaced():
    item1 = Item(1)
    item2 = Item(2)
    item3 = Item(3)
    item1.next = item2
    item1.next = item3
    assert item1.prev is None
    assert item1.next == item3
    assert item2.prev is None
    assert item2.next is None
    assert item3.prev == item1
    assert item3.next is None


def test_item__set_prev_when_prev_exists__prev_replaced():
    item1 = Item(1)
    item2 = Item(2)
    item3 = Item(3)
    item3.prev = item2
    item3.prev = item1
    assert item1.prev is None
    assert item1.next == item3
    assert item2.prev is None
    assert item2.next is None
    assert item3.prev == item1
    assert item3.next is None


def test_item__first():
    chain = gen_chain(3)
    assert chain[0].first is chain[0]
    assert chain[1].first is chain[0]
    assert chain[2].first is chain[0]


def test_item__last():
    chain = gen_chain(3)
    assert chain[0].last is chain[2]
    assert chain[1].last is chain[2]
    assert chain[2].last is chain[2]


def test_item__get_exists__returns_item():
    chain = gen_chain(10)
    item5 = chain[0].get(5)
    assert chain[5] is item5


def test_item__get_negative_int__returns_item():
    chain = gen_chain(10)
    item_i3 = chain[5].get(-2)
    assert item_i3 == chain[3]


def test_item__get_positive_int__returns_item():
    chain = gen_chain(10)
    item_i7 = chain[5].get(2)
    assert item_i7 == chain[7]


def test_item__get_before_start__returns_item():
    chain = gen_chain(5)
    item0 = chain[0].get(-10)
    assert chain[0] is item0


def test_item__get_past_end__returns_item():
    chain = gen_chain(5)
    item5 = chain[0].get(10)
    assert chain[-1] is item5


def test_item__to_list_empty__just_item():
    chain = gen_chain(5)
    assert chain[1].to_list() == [chain[1]]


def test_item__to_list_start_item_end_item__list_to_item():
    chain = gen_chain(5)
    assert chain[3].to_list(start=chain[1], end=chain[4]) == [
        chain[1],
        chain[2],
        chain[3],
        chain[4],
    ]


def test_item__insert_chain__chain_inserted():
    chain1 = gen_chain(4, chain=1)
    chain2 = gen_chain(2, chain=2)
    chain1[1].insert(chain2[0])
    assert chain1[0].to_list(start=chain1[0], end=chain1[3]) == [
        chain1[0],
        chain1[1],
        chain2[0],
        chain2[1],
        chain1[2],
        chain1[3],
    ]


def test_item__replace_item__chain_replaces():
    chain1 = gen_chain(3, chain=1)
    chain2 = gen_chain(2, chain=2)
    chain1[1].replace(chain2[0])
    assert chain1[0].to_list(start=chain1[0], end=chain1[2]) == [
        chain1[0],
        chain2[0],
        chain2[1],
        chain1[2],
    ]


def test_item__replace_range__chain_replaces():
    chain1 = gen_chain(5, chain=1)
    chain2 = gen_chain(2, chain=2)
    chain1[2].replace(chain2[0], start=-1, end=1)
    assert chain1[0].to_list(start=chain1[0], end=chain1[4]) == [
        chain1[0],
        chain2[0],
        chain2[1],
        chain1[4],
    ]


def test_item__delete_item__item_deleted():
    chain = gen_chain(3)
    chain[1].delete()
    assert chain[0].to_list(start=chain[0], end=chain[2]) == [chain[0], chain[2]]


def test_item__delete_range__items_deleted():
    chain = gen_chain(5)
    chain[2].delete(start=-1, end=1)
    assert chain[0].to_list(start=chain[0], end=chain[4]) == [chain[0], chain[4]]
