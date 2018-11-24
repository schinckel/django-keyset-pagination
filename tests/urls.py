from django.urls import path

from . import views


urlpatterns = [
    path('events/', views.EventList.as_view(), name='events'),
]
