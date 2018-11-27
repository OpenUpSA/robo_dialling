import json
from django.db import models
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask


# class PhoneNumber(models.Model):
#     title = models.CharField(max_length=100, null=True, blank=True)
#     number = models.CharField(max_length=14, null=True, blank=True)
#     department = models.CharField(max_length=255, null=True, blank=True)
#     organization = models.CharField(max_length=255, null=True, blank=True)
#
#     def __str__(self):
#         return self.number


class CeleryPhoneModel(PeriodicTask):
    title = models.CharField(max_length=100, null=True, blank=True)
    number = models.CharField(max_length=14, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    organization = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.args = [self.pk]
        self.exchange = self.exchange or None
        self.routing_key = self.routing_key or None
        self.queue = self.queue or None
        if not self.enabled:
            self.last_run_at = None
        super(PeriodicTask, self).save(*args, **kwargs)


class CallStat(models.Model):
    phone_dialed = models.ForeignKey(CeleryPhoneModel, null=True, blank=True, on_delete=models.CASCADE)
    time_before_hang = models.IntegerField()
    phone_is_active = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_dialed.number


# class RepeatPeriod(models.Model):
#     period_name = models.CharField(max_length=255, null=True, blank=True)
#     period = models.CharField(max_length=255, null=True, blank=True)
#
#     def __str__(self):
#         return self.period_name


# class WeekDay(models.Model):
#     name = models.CharField(max_length=15, null=True, blank=True)
#     day_num = models.IntegerField()
#
#     def __str__(self):
#         return self.name


# class Schedule(models.Model):
#     phone_number = models.ForeignKey(PhoneNumber, null=True, blank=True, on_delete=models.CASCADE)
#     period = models.ForeignKey(RepeatPeriod, null=True, blank=True, on_delete=models.CASCADE)
#     days = models.ManyToManyField(WeekDay)
#     disabled = models.BooleanField(default=False)
#
#     def __str__(self):
#         return self.phone_number.number


class TwilioSettings(models.Model):
    pass
