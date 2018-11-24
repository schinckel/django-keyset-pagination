from functools import reduce
from operator import and_, or_
import json

from django.core.paginator import Paginator, Page, InvalidPage
from django.db import models

try:
    text = (unicode, str)
except NameError:
    text = (str,)


def build_filter(key, value, include=False, flip=False):
    # Examine the key: if it has a - prefix, then that means we were sorted
    # DESC, and thus need to use lt. Otherwise it will be gt.
    # If `include`, that means lte/gte.
    if key[0] == '-':
        direction = True
    else:
        direction = False

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
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        super(KeysetPaginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)
        self.keys = object_list.query.order_by

    def _get_page(self, number):
        if number is None:
            object_list = self.object_list
        else:
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
            page_filter = reduce(or_, [
                reduce(and_, [key_filter] + equality_filters[:i - 1])
                for i, key_filter in enumerate(key_filters)
            ])

            # To make the query planner able to use an index, we will use an AND with the
            # filters above and "A <= ?" (or >=). This allows the query planner to use
            # and index on that column.
            object_list = self.object_list.filter(
                page_filter & build_filter(self.keys[0], values[0], include=True, flip=flip)
            )

            # If we are using a "previous" link, we need to flip all of the keys around
            # to generate the reverse ordering. We have to rely on the KeysetPage object
            # to notice that we have done this, and it will reverse the results it
            # gets from the database.
            if flip:
                reversed_keys = [
                    '-' + key if key[0] != '-' else key.lstrip('-')
                    for key in self.keys
                ]
                object_list = object_list.order_by(*reversed_keys)

        return KeysetPage(object_list[:self.per_page + 1], number, self)

    def page(self, number):
        return self._get_page(self.validate_number(number))

    def validate_number(self, number):
        if not number or number == 1:
            return None
        if isinstance(number, text):
            number = json.loads(number)
        if len(number) != 1 + len(self.keys):
            raise InvalidPage('Key length mismatch')
        return number


class KeysetPage(Page):
    def __init__(self, object_list, number, paginator):
        object_list = list(object_list)
        self.continues = len(object_list) > paginator.per_page
        self.direction = 'previous' if number and number[0] else 'next'
        object_list = object_list[:paginator.per_page]
        if self.direction == 'previous':
            object_list = reversed(object_list)
        super(KeysetPage, self).__init__(object_list, number, paginator)

    def has_next(self):
        return self.direction == 'previous' or self.continues
        # If we are doing a "next" page, then look at the number of results.
        # If that is fewer than our per-page amount, that means we either have
        # more results, or we can't know (because we got exactly all results).
        if not self.number or not self.number[0]:
            return len(self) == self.paginator.per_page
        return True

    def has_previous(self):
        if self.direction == 'next':
            return self.number
        return self.continues
        return (self.direction == 'next' and self.number) or self.continues
        # If we are doing a "previous" page, and we have fewer than the per-page
        # results, that means we don't have a previous page. Otherwise, assume
        # there is a previous page unless we _know_ we are the first page.
        if self.number and self.number[0]:
            return len(self) == self.paginator.per_page
        return self.number

    def _key_for_instance(self, instance, prev=False):
        return json.dumps([prev] + [
            getattr(instance, key.lstrip('-'))
            for key in self.paginator.keys
        ], default=str)

    def next_page_number(self):
        return self._key_for_instance(self[-1])

    def previous_page_number(self):
        return self._key_for_instance(self[0], True)

    def start_index(self):
        return 0

    def end_index(self):
        return 1
