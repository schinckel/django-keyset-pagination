"""
A Paginator that uses Keyset Pagination to allow for efficient fetching
of subsequent pages.

Probably requires you use the `keyset_pagination.mixin.PaginateMixin` in
your view.
"""

import json
from functools import reduce
from operator import and_, or_

from django.core.paginator import InvalidPage, Page, Paginator
from django.db import models

try:
    text = (unicode, str)   # NOQA
except NameError:
    text = (str,)           # NOQA


def build_filter(key, value, include=False, flip=False):
    """
    Examine the key: if it has a - prefix, then that means we were sorted
    DESC, and thus need to use lt. Otherwise it will be gt.
    If `include`, that means lte/gte.
    """
    direction = key[0] == '-'

    if flip:
        direction = not direction

    return models.Q(**{
        '{key}__{direction}{e}'.format(
            key=key.lstrip('-'),
            direction='lt' if direction else 'gt',
            e='e' if include else ''
        ): value
    })


class KeysetPaginator(Paginator):
    "Keyset Pagination: does not use OFFSET."

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        super(KeysetPaginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)
        self.keys = object_list.query.order_by

    def _get_page_filters(self, number):
        # The first part of our key is always the "previous" link indicator. If this
        # value is true, that means this is a previous link, so we need to reverse all
        # of the tests and the ordering later.
        flip = number[0]
        values = number[1:]

        # We can build up the various Q objects we will need for this query beforehand.
        # These are the filters that apply to break a tie on the previous level.
        key_filters = [
            build_filter(key, value, flip=flip)
            for key, value in zip(self.keys, values)
        ]
        # And these are the filters that detect a tie at each level.
        equality_filters = [
            models.Q(**{
                key.lstrip('-'): value
                for key, value in zip(self.keys, values)
            })
        ]

        # We want to use (A < ? OR (A = ? AND B < ?) OR (A = ? AND B = ? AND C < ?))
        # Except that the < could be a > depending upon the sort direction.
        page_filters = reduce(or_, [
            reduce(and_, [key_filter] + equality_filters[:i - 1])
            for i, key_filter in enumerate(key_filters)
        ])
        # To make the query planner able to use an index, we use an AND with the
        # filters above and "A <= ?" (or >=). This allows the query planner to use
        # and index on that column.
        index_helper = build_filter(self.keys[0], values[0], include=True, flip=flip)

        return page_filters & index_helper

    def _get_ordering(self, number):
        # If we are using a "previous" link, we need to flip all of the keys around
        # to generate the reverse ordering. We have to rely on the KeysetPage object
        # to notice that we have done this, and it will reverse the results it
        # gets from the database.

        if number[0]:
            return [
                '-' + key if key[0] != '-' else key.lstrip('-')
                for key in self.keys
            ]
        return self.keys

    def _get_page(self, *args, **kwargs):
        return KeysetPage(*args, **kwargs)

    def page(self, number):
        number = self.validate_number(number)

        if number is None:
            object_list = self.object_list
        else:
            object_list = self.object_list.filter(
                self._get_page_filters(number)
            ).order_by(*self._get_ordering(number))

        return self._get_page(object_list[:self.per_page + 1], number, self)

    def validate_number(self, number):
        if not number or number == 1:
            return None
        if isinstance(number, text):
            number = json.loads(number)
        if len(number) != 1 + len(self.keys):
            raise InvalidPage('Key length mismatch')
        return number

    @property
    def count(self):
        return None

    @property
    def num_pages(self):
        return None

    @property
    def page_range(self):
        return []


class KeysetPage(Page):
    "Custom Page for KeysetPaginator"
    # pylint: disable=too-many-ancestors

    def __init__(self, object_list, number, paginator):
        # We can't call our ancestor's __init__, because that will set
        # self.object_list, which we don't want to set.
        # pylint: disable=super-init-not-called
        self._object_list = object_list
        self.number = number
        self.direction = 'previous' if number and number[0] else 'next'
        self.paginator = paginator
        self._continues = None

    def __repr__(self):
        # I'm not sure we want to be doing this: I think it may result in more
        # queries. It will do for now though.
        return "<KeysetPage: {} of {}>".format(self.page_index, self.paginator.num_pages)

    @property
    def page_index(self):
        "The page_index of a keyset page is always None."
        return None

    @property
    def continues(self):
        "Does this queryset continue in the direction it was fetched?"
        if self._continues is None:
            # This will set the _continues instance variable to the correct value.
            # pylint: disable=pointless-statement
            self.object_list
        return self._continues

    @property
    def object_list(self):  # NOQA
        # We need to replace the normal attribute with a cached_property, so we can
        # have it more lazily calculated, because we need to set
        object_list = self._object_list
        if not isinstance(object_list, list):
            object_list = list(object_list)

        # What about orphans?
        self._continues = len(object_list) > self.paginator.per_page

        object_list = object_list[:self.paginator.per_page]

        if self.direction == 'previous':
            object_list = list(reversed(object_list))

        return object_list

    def has_next(self):
        # We pre-fetch one extra object - this enables us to detect if we
        # have another page after us. We can assume that if we did a "previous"
        # page fetch, that means there were results in the previous page, else
        # we know for sure by the fact we got more than our allocated items.
        return self.direction == 'previous' or self.continues

    def has_previous(self):
        # If we are doing a "next" page fetch, then we know we have previous results
        # if we fetched anything other than the first page (which will have an empty
        # number). Otherwise, we use the fetch of more than our amount to detect in
        # the case of a "previous" fetch if we have another previous page.
        if self.direction == 'next':
            return self.number
        return self.continues

    def _key_for_instance(self, instance, prev=False):
        # We need to build up a special key that contains the direction we need to fetch
        # the target page in, and the data from the first/last item in our object_list.
        # JSON should be fine here? As long as the str(unknown_type) gives us something
        # we will be able to push back into the database for querying.
        return json.dumps([prev] + [
            getattr(instance, key.lstrip('-'))
            for key in self.paginator.keys
        ], default=str)

    def next_page_number(self):
        if self.has_next():
            return self._key_for_instance(self[-1])
        return None

    def previous_page_number(self):
        if self.has_previous():
            return self._key_for_instance(self[0], True)
        return None

    def start_index(self):
        return None

    def end_index(self):
        return None
