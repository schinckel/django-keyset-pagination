# Keyset Pagination for Django

[![CI](https://github.com/schinckel/django-keyset-pagination/actions/workflows/ci.yml/badge.svg)](https://github.com/schinckel/django-keyset-pagination/actions/workflows/ci.yml)

Django's built-in pagination uses `LIMIT/OFFSET`. That works well for small offsets, but it gets progressively more expensive as the offset grows because the database still has to walk past the earlier rows.

This package implements keyset pagination, also called the seek method. Instead of asking for "page 200", the client asks for "the next page after this row" or "the previous page before this row". That keeps pagination efficient for large result sets, but it also means random page access and page-number iteration are not supported.

If you are new to the approach, the background articles from [Markus Winand](https://use-the-index-luke.com/sql/partial-results/fetch-next-page) and [Joe Nelson](https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/) are worth reading.

## Installation

Install the published package:

```bash
python -m pip install django-keyset-pagination-plus
```

The import path remains `keyset_pagination`.

## Usage

In most class-based views you will want both the paginator and the included mixin, because Django's default pagination flow assumes integer page numbers.

```python
from django.views.generic import ListView

from keyset_pagination.mixin import PaginateMixin
from keyset_pagination.paginator import KeysetPaginator


class EventList(PaginateMixin, ListView):
    paginator_class = KeysetPaginator
    paginate_by = 10
    queryset = Event.objects.order_by("-timestamp", "group", "pk")
```

If your queryset does not call `.order_by(...)`, the paginator will also honor the model's `Meta.ordering`. That lets you rely on a model's default ordering without repeating it in every view:

```python
class Event(models.Model):
    label = models.TextField()
    sequence = models.IntegerField()

    class Meta:
        ordering = ("label", "sequence")


paginator = KeysetPaginator(Event.objects.all(), 10)
```

A few important constraints:

- The queryset must have a deterministic ordering. If you do not provide `.order_by(...)`, the paginator falls back to the model's `Meta.ordering`.
- If you explicitly clear ordering with `.order_by()`, the paginator raises `ValueError`.
- Use a stable ordering. In practice that usually means appending a unique tiebreaker such as `pk`.
- Ordering across related fields such as `location__name` is supported, but you should usually pair that with `select_related()` to avoid extra queries when page tokens are generated.
- Only next/previous navigation is available. `count`, `num_pages`, and page-number iteration are intentionally unavailable.

## Template usage

Cursor values are opaque JSON tokens built from the queryset ordering columns. Treat them as implementation details and pass them back unchanged.

```django
{% if page_obj.has_previous %}
  <a href="?page={{ page_obj.previous_page_number }}">Previous page</a>
{% endif %}

{% if page_obj.has_next %}
  <a href="?page={{ page_obj.next_page_number }}">Next page</a>
{% endif %}
```

The same approach works well with `GET` forms when the list also has filters:

```django
{% if page_obj.has_previous %}
  <button form="target-form"
          name="page"
          value="{{ page_obj.previous_page_number }}"
          type="submit">
    &larr; Previous page
  </button>
{% endif %}

{% if page_obj.has_next %}
  <button form="target-form"
          name="page"
          value="{{ page_obj.next_page_number }}"
          type="submit">
    Next page &rarr;
  </button>
{% endif %}
```

Cursor serialization handles values that do not round-trip cleanly through plain JSON types, including `Decimal`, `datetime`, `date`, `time`, and PostgreSQL range values. Decimal cursor values are parsed with `Decimal`, so precision is preserved even when the incoming token contains a bare JSON number.

## Supported versions

The package supports Python 3.10+ and Django `>=4.2,<6.1`.

Continuous integration currently exercises Django 4.2, 5.2, and 6.0 on SQLite, plus PostgreSQL and MySQL integration environments for those Django releases.

## Development

```bash
python -m pip install -e ".[dev,test]"
pre-commit install
tox -e py312-django52-sqlite
tox -p auto
```

Helpful shortcuts are also available through `make`:

```bash
make lint
make test
make test-all
make package
```

For local MySQL runs on macOS with Homebrew, install `mysql-client` and `pkgconf`. The MySQL tox environments default `MYSQLCLIENT_CFLAGS` and `MYSQLCLIENT_LDFLAGS` to Homebrew's `mysql-client` paths, and you can override them with environment variables if your local setup differs.

See [schinckel.net: Keyset Pagination in Django](https://schinckel.net/2018/11/23/keyset-pagination-in-django/) for a longer walkthrough of the approach.
