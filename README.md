# Keyset Pagination for Django.

[![CI](https://github.com/schinckel/django-keyset-pagination/actions/workflows/ci.yml/badge.svg)](https://github.com/schinckel/django-keyset-pagination/actions/workflows/ci.yml)

Django pagination uses the LIMIT/OFFSET method. This is fine for smaller offsets, but once you start getting beyond a few pages, it can perform really badly. This is because the database needs to fetch all of the previous rows, even though it discards them.

Using Keyset Pagination allows for better performing "next page" fetches, at the cost of not being able to randomly fetch a page. That is, if you know the last element from page N-1, then you may fetch page N, but otherwise you really can't.

Keyset Pagination, sometimes called the Seek Method, has been documented by [Markus Winand](https://use-the-index-luke.com/sql/partial-results/fetch-next-page) and [Joe Nelson](https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/). If you are not familiar with the concept, I strongly suggest you read the articles above.

In order to use the paginator within this package, you will probably also need to use the provided View mixin: this changes the way a queryset is paginated to enable non-integer "page numbers".

    class List(PaginationMixin, ListView):
        paginator_class = KeysetPaginator
        paginate_by = 10
        queryset = MyModel.objects.order_by('-timestamp', 'group')

You won't be able to iterate through page numbers in a template in the same way: you are limited to next and previous pages. Otherwise, you construct them in largely the same way:

    <a href="{% url 'mymodel:list' %}?page={{ page_obj.previous_page_number }}">
      Prev Page
    </a>

    <a href="{% url 'mymodel:list' %}?page={{ page_obj.next_page_number }}">
      Next Page
    </a>

Page tokens are JSON payloads built from the ordering columns in your queryset. They are opaque from the caller's perspective and should be passed back unchanged. Ordering by `DecimalField` values is supported, and decimal cursor values are preserved without being coerced through binary floats.

Note that you do not get access to the length of the queryset, nor the number of pages, because these could be expensive queries. You really don't need to know that ;)

However, I like to use GET forms to [enable pagination of filtered results](https://schinckel.net/2014/08/17/leveraging-html-and-django-forms%3A-pagination-of-filtered-results/):

    <button form="target-form"
            name="page"
            value="{{ page_obj.previous_page_number }}"
            type="submit">
      &larr; Prev Page
    </button>

    <button form="target-form"
            name="page"
            value="{{ page_obj.next_page_number }}"
            type="submit">
      Next Page &rarr;
    <button>


## Supported versions

The package is now tested against modern Django and Python releases via GitHub Actions, with a current matrix covering Django 4.2, 5.2, and 6.0 on SQLite and additional integration coverage for PostgreSQL and MySQL.

## Development

```bash
python -m pip install -e ".[dev,test]"
pre-commit install
tox -e py312-django52-sqlite
tox -p auto
```

The repository includes GitHub Actions workflows for CI and release publishing, Dependabot updates, Ruff linting/formatting, and tox-driven test environments for SQLite and PostgreSQL. For a full local run, use `tox -p auto` or `make test-all` to execute the tox matrix in parallel.

For local MySQL runs on macOS with Homebrew, install `mysql-client` and `pkgconf`. The MySQL tox environments default `MYSQLCLIENT_CFLAGS` and `MYSQLCLIENT_LDFLAGS` to the Homebrew `mysql-client` paths, and you can override them with environment variables if your local setup differs.

See https://schinckel.net/2018/11/23/keyset-pagination-in-django/ for more details about how this package works.
