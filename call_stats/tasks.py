from __future__ import absolute_import, unicode_literals

import json

import celery
from celery import shared_task, task
from .models import CeleryPhoneModel, CallStat
import logging
from .call_maker import TwilioConnecter, TwilioCaller


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='robo_call.log',
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


class TaskWrapper(celery.Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        msg = '{0!r} failed: {1!r} args:{2!}'.format(task_id, exc, str(args))
        logging.error(msg)

    def on_success(self, retval, task_id, args, kwargs):
        msg = '{0!r} success: {1!r}'.format(task_id, str(args))
        logging.info(msg)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        msg = 'RETRY {0!r} failed: {1!r} args:{2!}'.format(task_id, exc, str(args))
        logging.info(msg)


@shared_task(name='TwilioCaller', base=TaskWrapper)
def make_twilio_call(*args, **kwargs):
    numbers = CeleryPhoneModel.objects.filter(id__in=args)
    # infos = []
    connecter = TwilioConnecter()
    caller = TwilioCaller(connecter.client)

    for number_model in numbers:
        data = caller.make_call(number=number_model.number)

        if data[0]:
            call_stat = CallStat(phone_dialed=number_model, time_before_hang=0, sid=data[0].sid, status=data[0].status)
        else:
            stat = True
            if data[1].phone_status:
                stat = False
            debug_info = json.dumps(data[1].__dict__)
            call_stat = CallStat(phone_dialed=number_model, debug_info=debug_info, time_before_hang=0, phone_is_active=stat, sid=None, status="wrong")

        call_stat.save()

    # CallStat.objects.bulk_create(infos)


@shared_task(name="SyncWithTwilioStats")
def sync_with_twilio_stats(*args, **kwargs):
    """need if callbacks will not work correctly"""
    connecter = TwilioConnecter()
    """set this data to task kwargs"""
    kw = {"start_time_after": "2015-01-01", "start_time_before": "2016-01-01"}
    calls = connecter.get_calls_list(**kw)
    print(calls)
    for c in calls:
        call_stat = CallStat.objects.filter(sid=c["sid"]).first()
        if call_stat:
            call_stat.time_before_hang = c["duration"]
            call_stat.status = c["status"]
            print(call_stat.__dict__)
            # call_stat.save()
