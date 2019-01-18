from . import views


try:
    from django.urls import path
    urlpatterns = [
        path('events/', views.EventList.as_view(), name='events'),
    ]
except ImportError:
    from django.conf.urls import url
    urlpatterns = [
        url(r'^events/$', views.EventList.as_view(), name='events'),
    ]
