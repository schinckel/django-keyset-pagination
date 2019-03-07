import pytest

from keyset_pagination.paginator import KeysetPaginator, InvalidPage

from ..models import Event


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


def test_has_next_previous(events):
    paginator = KeysetPaginator(Event.objects.order_by('-timestamp', 'group'), 5)
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
    paginator = KeysetPaginator(Event.objects.order_by('-timestamp', 'group'), 5)
    page = paginator.page(None)

    assert not page.has_next()
    assert not page.has_previous()


def test_invalid_page():
    paginator = KeysetPaginator(Event.objects.order_by('-timestamp', 'group'), 5)
    with pytest.raises(InvalidPage):
        paginator.page('["foo","bar"]')
