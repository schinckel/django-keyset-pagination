from django.db import models


class Event(models.Model):
    event_id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    tag = models.TextField(null=True, blank=True)
    group = models.TextField(null=True, blank=True)
    reading = models.IntegerField()
    location = models.ForeignKey(
        'tests.Location', related_name='events', on_delete=models.CASCADE, null=True, blank=True,
    )


class Location(models.Model):
    name = models.TextField(null=True, blank=True)
