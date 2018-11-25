"""
A Mixin that make it possible to use pagination with non-integer page
numbers. This is required for keyset pagination (in most cases).
"""

from django.core.paginator import InvalidPage
from django.http import Http404
from django.utils.translation import ugettext as _

# pylint: disable=too-few-public-methods


class PaginateMixin:
    "Make pagination work for non integer page numbers"

    def paginate_queryset(self, queryset, page_size):
        """
        This is very similar to how django currently (2.1) does it: I may submit a PR to use this
        mechanism instead, as it is more flexible.
        """
        paginator = self.get_paginator(
            queryset, page_size, orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty()
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1

        # This is really the only bit that changes. I think it's reasonable to
        # delegate converting the magic string 'last' into the actual page index
        # to the paginator, to be honest.
        try:
            page_number = paginator.validate_number(page)
        except ValueError:
            raise Http404(_('Page could not be parsed.'))

        try:
            page = paginator.page(page_number)
            return (paginator, page, page.object_list, page.has_other_pages())
        except InvalidPage as exc:
            raise Http404(
                _('Invalid page (%(page_number)s): %(message)s') % {
                    'page_number': page_number,
                    'message': str(exc)
                }
            )
