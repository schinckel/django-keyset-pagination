import pytest

from keyset_pagination.paginator import KeysetPaginator

from ..models import Period


@pytest.fixture
def periods():
    Period.objects.bulk_create([
        Period(valid_period=('2019-01-01', '2019-01-02')),
        Period(valid_period=('2019-02-01', '2019-02-02')),
        Period(valid_period=('2019-03-01', '2019-03-02')),
        Period(valid_period=('2019-04-01', '2019-04-02')),
        Period(valid_period=('2019-05-01', '2019-05-02')),
        Period(valid_period=('2019-06-01', '2019-06-02')),
        Period(valid_period=('2019-07-01', '2019-07-02')),
        Period(valid_period=('2019-08-01', '2019-08-02')),
        Period(valid_period=('2019-09-01', '2019-09-02')),
        Period(valid_period=('2019-10-01', '2019-10-02')),
        Period(valid_period=('2019-11-01', '2019-11-02')),
        Period(valid_period=('2019-12-01', '2019-12-02')),
    ])


@pytest.mark.skipif(Period.skip, reason="Postgres not found")
def test_pagination_using_date_range(periods):
    paginator = KeysetPaginator(Period.objects.order_by('valid_period'), 7)
    page = paginator.page(1)
    assert len(page.object_list) == 7
    assert page.next_page_number() == '[false, "[2019-07-01, 2019-07-02)"]'
    page = paginator.page(page.next_page_number())
    assert len(page.object_list) == 5
    assert page.next_page_number() is None
    assert page.previous_page_number() == '[true, "[2019-08-01, 2019-08-02)"]'

    paginator = KeysetPaginator(Period.objects.order_by('-valid_period'), 7)
    page = paginator.page(1)
    assert len(page.object_list) == 7
    assert page.next_page_number() == '[false, "[2019-06-01, 2019-06-02)"]'
    page = paginator.page(page.next_page_number())
    assert len(page.object_list) == 5
    assert page.next_page_number() is None
    assert page.previous_page_number() == '[true, "[2019-05-01, 2019-05-02)"]'
