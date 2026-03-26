from decimal import Decimal

import pytest

from keyset_pagination.paginator import InvalidPage, KeysetPaginator

from ..models import Event, Location, OrderedEvent


@pytest.fixture
def events():
    Event.objects.bulk_create(
        [
            Event(
                timestamp="2017-01-01T01:23:45Z", group="bar", reading=2, ratio=Decimal("0.1232")
            ),
            Event(
                timestamp="2017-01-01T01:23:45Z", group="baz", reading=3, ratio=Decimal("0.1233")
            ),
            Event(
                timestamp="2017-01-01T01:23:45Z", group="foo", reading=1, ratio=Decimal("0.1231")
            ),
            Event(
                timestamp="2017-01-01T01:23:45Z", group="qux", reading=4, ratio=Decimal("0.1234")
            ),
            Event(
                timestamp="2017-01-01T05:23:45Z", group="foo", reading=5, ratio=Decimal("0.1235")
            ),
            Event(
                timestamp="2017-01-01T06:23:45Z", group="foo", reading=6, ratio=Decimal("0.1236")
            ),
        ]
    )


def test_paginator_single_page():
    Event.objects.create(timestamp="2017-01-01T01:23:45Z", reading=1)

    paginator = KeysetPaginator(Event.objects.order_by("-timestamp"), 10)
    assert paginator.page(1).object_list[0].reading == 1
    assert paginator.page(None).object_list[0].reading == 1


def test_paginator_multiple_pages():
    Event.objects.bulk_create(
        [
            Event(timestamp="2017-01-01T01:23:45Z", reading=1),
            Event(timestamp="2017-01-01T02:23:45Z", reading=2),
            Event(timestamp="2017-01-01T03:23:45Z", reading=3),
            Event(timestamp="2017-01-01T04:23:45Z", reading=4),
            Event(timestamp="2017-01-01T05:23:45Z", reading=5),
            Event(timestamp="2017-01-01T06:23:45Z", reading=6),
        ]
    )

    paginator = KeysetPaginator(Event.objects.order_by("timestamp"), 5)
    page = paginator.page(1)
    assert len(page.object_list) == 5
    assert page.next_page_number() == '[false, "2017-01-01 05:23:45+00:00"]'
    page = paginator.page(page.next_page_number())
    assert len(page.object_list) == 1

    paginator = KeysetPaginator(Event.objects.order_by("-timestamp"), 5)
    page = paginator.page(None)
    assert len(page.object_list) == 5
    assert page.next_page_number() == '[false, "2017-01-01 02:23:45+00:00"]'
    page = paginator.page(page.next_page_number())
    assert len(page.object_list) == 1
    assert page.object_list[0].reading == 1


def test_paginator_multiple_ordering_columns(events):
    paginator = KeysetPaginator(Event.objects.order_by("timestamp", "group"), 3)
    page = paginator.page(1)
    assert page.next_page_number() == '[false, "2017-01-01 01:23:45+00:00", "foo"]'
    assert [2, 3, 1] == [x.reading for x in page.object_list]

    page = paginator.page(page.next_page_number())
    assert [4, 5, 6] == [x.reading for x in page.object_list]
    assert page.previous_page_number() == '[true, "2017-01-01 01:23:45+00:00", "qux"]'

    page = paginator.page(page.previous_page_number())
    assert [2, 3, 1] == [x.reading for x in page.object_list]


def test_paginator_previous_links(events):
    paginator = KeysetPaginator(Event.objects.order_by("timestamp", "group"), 2)
    page = paginator.page(1)
    assert page.next_page_number() == '[false, "2017-01-01 01:23:45+00:00", "baz"]'
    assert [2, 3] == [x.reading for x in page.object_list]

    page = paginator.page(page.next_page_number())
    assert [1, 4] == [x.reading for x in page.object_list]
    assert page.next_page_number() == '[false, "2017-01-01 01:23:45+00:00", "qux"]'

    page = paginator.page(page.next_page_number())
    assert [5, 6] == [x.reading for x in page.object_list]
    assert not page.has_next()
    assert page.next_page_number() is None

    page = paginator.page(page.previous_page_number())
    assert [1, 4] == [x.reading for x in page.object_list]


def test_paginator_with_multiple_ordering_keys():
    Event.objects.bulk_create(
        [
            Event(timestamp="2019-01-01T01:02:03Z", tag="ordered", group="foo", reading=i)
            for i in range(20)
        ]
    )
    paginator = KeysetPaginator(Event.objects.order_by("tag", "group", "reading", "pk"), 10)
    page = paginator.page(1)
    assert 10 == len(page.object_list)
    assert page.has_next()
    assert not page.has_previous()

    page = paginator.page(page.next_page_number())
    assert 10 == len(page.object_list)
    assert page.has_previous()
    assert not page.has_next()


def test_paginator_three_or_more_keys_keep_lexicographic_boundaries():
    Event.objects.bulk_create(
        [
            Event(timestamp="2019-01-01T01:02:03Z", tag="k", group="a", reading=100),
            Event(timestamp="2019-01-01T01:02:03Z", tag="k", group="b", reading=1),
            Event(timestamp="2019-01-01T01:02:03Z", tag="k", group="b", reading=2),
            Event(timestamp="2019-01-01T01:02:03Z", tag="k", group="c", reading=1),
            Event(timestamp="2019-01-01T01:02:03Z", tag="k", group="c", reading=2),
        ]
    )
    paginator = KeysetPaginator(Event.objects.order_by("tag", "group", "reading", "pk"), 3)

    page = paginator.page(1)
    assert [("a", 100), ("b", 1), ("b", 2)] == [(x.group, x.reading) for x in page.object_list]

    page = paginator.page(page.next_page_number())
    assert [("c", 1), ("c", 2)] == [(x.group, x.reading) for x in page.object_list]
    assert page.next_page_number() is None


def test_paginator_lookup_keys():
    location = Location.objects.create(name="A")
    Event.objects.bulk_create(
        [
            Event(
                timestamp="2019-01-01T01:02:03Z",
                group="foo",
                reading=i,
                location=location,
            )
            for i in range(20)
        ]
    )
    paginator = KeysetPaginator(Event.objects.order_by("location__name", "pk"), 10)
    page = paginator.page(1)
    assert 10 == len(page.object_list)
    assert page.has_next()
    assert not page.has_previous()

    page = paginator.page(page.next_page_number())
    assert 10 == len(page.object_list)
    assert page.has_previous()
    assert not page.has_next()


def test_friendly_error_when_no_keys():
    with pytest.raises(ValueError):
        KeysetPaginator(Event.objects.all(), 10)


def test_uses_meta_ordering_when_queryset_has_no_explicit_order_by():
    OrderedEvent.objects.bulk_create(
        [
            OrderedEvent(label="b", sequence=3),
            OrderedEvent(label="a", sequence=2),
            OrderedEvent(label="a", sequence=1),
            OrderedEvent(label="c", sequence=4),
        ]
    )

    paginator = KeysetPaginator(OrderedEvent.objects.all(), 2)
    page = paginator.page(1)

    assert paginator.keys == ["label", "sequence"]
    assert [x.sequence for x in page.object_list] == [1, 2]

    page = paginator.page(page.next_page_number())
    assert [x.sequence for x in page.object_list] == [3, 4]


def test_explicitly_clearing_ordering_still_errors():
    with pytest.raises(ValueError):
        KeysetPaginator(OrderedEvent.objects.order_by(), 10)


def test_ignore_pagination_when_empty_list():
    assert KeysetPaginator([], 10).object_list == []


def test_1_as_string_is_a_valid_page_number(events):
    paginator = KeysetPaginator(Event.objects.order_by("location__name", "pk"), 5)
    page = paginator.page("1")
    assert 5 == len(page.object_list)


def test_invalid_page_number(events):
    paginator = KeysetPaginator(Event.objects.order_by("location__name", "pk"), 5)
    with pytest.raises(InvalidPage):
        paginator.page("2")

    with pytest.raises(InvalidPage):
        paginator.page("[2,true")


def test_decimal_in_page_number(events):
    paginator = KeysetPaginator(Event.objects.order_by("ratio", "pk"), 3)
    page = paginator.page(1)

    assert [1, 2, 3] == [x.reading for x in page.object_list]
    last_pk = page.object_list[-1].pk
    assert page.next_page_number() == f'[false, "0.1233", {last_pk}]'

    page = paginator.page(page.next_page_number())
    assert [4, 5, 6] == [x.reading for x in page.object_list]

    page = paginator.page(f"[false, 0.1233, {last_pk}]")
    assert [4, 5, 6] == [x.reading for x in page.object_list]


def test_non_first_page_does_not_coerce_queryset_to_bool(events, monkeypatch):
    paginator = KeysetPaginator(Event.objects.order_by("reading"), 3)

    def fail_on_bool(_self):
        raise AssertionError("QuerySet.__bool__ should not be called for cursor pages")

    monkeypatch.setattr(type(paginator.object_list), "__bool__", fail_on_bool)

    next_page = paginator.page("[false, 3]")
    assert [4, 5, 6] == [x.reading for x in next_page.object_list]
