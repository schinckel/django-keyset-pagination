from django.views.generic import ListView

from keyset_pagination.mixin import PaginateMixin
from keyset_pagination.paginator import KeysetPaginator

from .models import Event


class EventList(PaginateMixin, ListView):
    paginator_class = KeysetPaginator
    paginate_by = 5
    template_name = "events.html"
    queryset = Event.objects.order_by("-timestamp", "group")
