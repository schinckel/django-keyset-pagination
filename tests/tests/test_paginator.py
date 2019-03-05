import pytest

from keyset_pagination.paginator import KeysetPaginator

from ..models import Event, Location


@pytest.fixture
def events():
    Event.objects.bulk_create([
        Event(timestamp='2017-01-01T01:23:45Z', group="bar", reading=2),
        Event(timestamp='2017-01-01T01:23:45Z', group="baz", reading=3),
        Event(timestamp='2017-01-01T01:23:45Z', group="foo", reading=1),
        Event(timestamp='2017-01-01T01:23:45Z', group="qux", reading=4),
        Event(timestamp='2017-01-01T05:23:45Z', group="foo", reading=5),
        Event(timestamp='2017-01-01T06:23:45Z', group="foo", reading=6),
    ])


def test_paginator_single_page():
    Event.objects.create(timestamp='2017-01-01T01:23:45Z', reading=1)

    paginator = KeysetPaginator(Event.objects.order_by('-timestamp'), 10)
    assert paginator.page(1).object_list[0].reading == 1
    assert paginator.page(None).object_list[0].reading == 1


def test_paginator_multiple_pages():
    Event.objects.bulk_create([
        Event(timestamp='2017-01-01T01:23:45Z', reading=1),
        Event(timestamp='2017-01-01T02:23:45Z', reading=2),
        Event(timestamp='2017-01-01T03:23:45Z', reading=3),
        Event(timestamp='2017-01-01T04:23:45Z', reading=4),
        Event(timestamp='2017-01-01T05:23:45Z', reading=5),
        Event(timestamp='2017-01-01T06:23:45Z', reading=6),
    ])

    paginator = KeysetPaginator(Event.objects.order_by('timestamp'), 5)
    page = paginator.page(1)
    assert len(page.object_list) == 5
    assert page.next_page_number() == '[false, "2017-01-01 05:23:45+00:00"]'
    page = paginator.page(page.next_page_number())
    assert len(page.object_list) == 1

    paginator = KeysetPaginator(Event.objects.order_by('-timestamp'), 5)
    page = paginator.page(None)
    assert len(page.object_list) == 5
    assert page.next_page_number() == '[false, "2017-01-01 02:23:45+00:00"]'
    page = paginator.page(page.next_page_number())
    assert len(page.object_list) == 1
    assert page.object_list[0].reading == 1


def test_paginator_multiple_ordering_columns(events):
    paginator = KeysetPaginator(Event.objects.order_by('timestamp', 'group'), 3)
    page = paginator.page(1)
    assert page.next_page_number() == '[false, "2017-01-01 01:23:45+00:00", "foo"]'
    assert [2, 3, 1] == [x.reading for x in page.object_list]

    page = paginator.page(page.next_page_number())
    assert [4, 5, 6] == [x.reading for x in page.object_list]
    assert page.previous_page_number() == '[true, "2017-01-01 01:23:45+00:00", "qux"]'

    page = paginator.page(page.previous_page_number())
    assert [2, 3, 1] == [x.reading for x in page.object_list]


def test_paginator_previous_links(events):
    paginator = KeysetPaginator(Event.objects.order_by('timestamp', 'group'), 2)
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
    Event.objects.bulk_create([
        Event(timestamp='2019-01-01T01:02:03Z', group='foo', reading=i) for i in range(20)
    ])
    paginator = KeysetPaginator(Event.objects.order_by('-timestamp', 'group', 'pk'), 10)
    page = paginator.page(1)
    assert 10 == len(page.object_list)
    assert page.has_next()
    assert not page.has_previous()

    page = paginator.page(page.next_page_number())
    assert 10 == len(page.object_list)
    assert page.has_previous()
    assert not page.has_next()


def test_paginator_lookup_keys():
    location = Location.objects.create(name='A')
    Event.objects.bulk_create([
        Event(timestamp='2019-01-01T01:02:03Z', group='foo', reading=i, location=location) for i in range(20)
    ])
    paginator = KeysetPaginator(Event.objects.order_by('location__name', 'pk'), 10)
    page = paginator.page(1)
    assert 10 == len(page.object_list)
    assert page.has_next()
    assert not page.has_previous()

    page = paginator.page(page.next_page_number())
    assert 10 == len(page.object_list)
    assert page.has_previous()
    assert not page.has_next()