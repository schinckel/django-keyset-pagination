from types import SimpleNamespace

import pytest

from keyset_pagination.paginator import InvalidPage, KeysetPage, KeysetPaginator

from ..models import Event


@pytest.fixture
def events():
    Event.objects.bulk_create(
        [
            Event(timestamp="2017-01-01T01:23:45Z", group="bar", reading=2),
            Event(timestamp="2017-01-01T01:23:45Z", group="baz", reading=3),
            Event(timestamp="2017-01-01T01:23:45Z", group="foo", reading=1),
            Event(timestamp="2017-01-01T01:23:45Z", group="qux", reading=4),
            Event(timestamp="2017-01-01T05:23:45Z", group="foo", reading=5),
            Event(timestamp="2017-01-01T06:23:45Z", group="foo", reading=6),
        ]
    )


def test_has_next_previous(events):
    paginator = KeysetPaginator(Event.objects.order_by("-timestamp", "group"), 5)
    page = paginator.page(None)

    assert page.has_next()
    assert not page.has_previous()

    page = paginator.page(page.next_page_number())
    assert not page.has_next()
    assert page.has_previous()

    page = paginator.page(page.previous_page_number())
    assert page.has_next()
    assert not page.has_previous()


def test_empty_results():
    paginator = KeysetPaginator(Event.objects.order_by("-timestamp", "group"), 5)
    page = paginator.page(None)

    assert not page.has_next()
    assert not page.has_previous()


def test_invalid_page():
    paginator = KeysetPaginator(Event.objects.order_by("-timestamp", "group"), 5)
    with pytest.raises(InvalidPage):
        paginator.page('["foo","bar"]')


class CountingIterable:
    def __init__(self, values):
        self.values = values
        self.iteration_count = 0

    def __iter__(self):
        self.iteration_count += 1
        return iter(self.values)


def test_object_list_is_materialized_once():
    iterable = CountingIterable([1, 2, 3])
    page = KeysetPage(iterable, None, SimpleNamespace(per_page=2))

    first_object_list = page.object_list
    second_object_list = page.object_list

    assert [1, 2] == first_object_list
    assert first_object_list is second_object_list
    assert iterable.iteration_count == 1
