from functools import reduce
from operator import and_, or_
import json

from django.core.paginator import Paginator, Page, InvalidPage
from django.db import models

try:
    text = (unicode, str)
except NameError:
    text = (str,)


def build_filter(key, value, include=False):
    # Examine the key: if it has a - prefix, then that means we were sorted
    # DESC, and thus need to use lt. Otherwise it will be gt.
    # If `include`, that means lte/gte.
    if key[0] == '-':
        return models.Q(**{'{}__lt{}'.format(key.lstrip('-'), 'e' if include else ''): value})
    return models.Q(**{'{}__gt{}'.format(key, 'e' if include else ''): value})


class KeysetPaginator(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        super(KeysetPaginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)
        self.keys = object_list.query.order_by

    def _get_page(self, number):
        if number is None:
            object_list = self.object_list
        else:
            # We can build up the various Q objects we will need for this query beforehand.
            # These are the filters that apply to break a tie on the previous level.
            key_filters = [
                build_filter(key, value)
                for key, value in zip(self.keys, number)
            ]
            # And these are the filters that detect a tie at each level.
            equality_filters = [
                models.Q(**{
                    key.lstrip('-'): value
                    for key, value in zip(self.keys, number)
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
                page_filter & build_filter(self.keys[0], number[0], True)
            )

        return KeysetPage(object_list[:self.per_page], number, self)

    def page(self, number):
        return self._get_page(self.validate_number(number))

    def validate_number(self, number):
        if not number or number == 1:
            return None
        if isinstance(number, text):
            number = json.loads(number)
        if len(number) != len(self.keys):
            raise InvalidPage('Key length mismatch')
        return number


class KeysetPage(Page):
    def has_next(self):
        return True

    def has_previous(self):
        return False

    def next_page_number(self):
        last_instance = self[-1]
        return json.dumps([
            getattr(last_instance, key.lstrip('-'))
            for key in self.paginator.keys
        ], default=str)

    def previous_page_number(self):
        return None

    def start_index(self):
        return 0

    def end_index(self):
        return 1
