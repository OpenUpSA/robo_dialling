from django.shortcuts import redirect
from django.template import loader
import re

from .models import CallStat, CeleryPhoneModel
from django.http import HttpResponse
from django.db.models import Count
import json
from datetime import timedelta
from django.utils import timezone
from .exporter import Exporter
from .call_maker import TwilioCaller, TwilioConnecter


def generate_chart_object(names, data):
    graphs = []

    for n in names:
        tmp = {
            "bullet": "round",
            "valueField": n,
            "labelText": "[[key]]",
            "title": n
        }

        graphs.append(tmp)

    chart_settings = {
        "type": "serial",
        "theme": "light",
        "dataProvider": data,
        "graphs": graphs,
        "legend": {
            "useGraphSettings": True,
        },
        "categoryAxis": {
            "parseDates": True,
            "minPeriod": "hh"
        },
        "categoryField": "date",
        "dataDateFormat": "YYYY-MM-DD JJ:NN:SS",
    }

    return chart_settings


def index(request):
    template = loader.get_template("call_stats/index.html")

    some_day_last_week = timezone.now().date() - timedelta(days=7)
    monday_of_last_week = some_day_last_week - timedelta(days=(some_day_last_week.isocalendar()[2] - 1))
    monday_of_this_week = monday_of_last_week + timedelta(days=7)

    week_count = CallStat.objects.filter(date__gte=monday_of_this_week).count()

    a = CallStat.objects.all()\
        .values('date', 'phone_dialed__organization')\
        .annotate(total=Count('phone_dialed'))\
        .order_by('date')\
        .prefetch_related("phone_dialed")\
        .filter(date__gte=timezone.now().date() - timedelta(days=2))

    l = []
    names = []
    tmp = {}

    for data in a:
        names.append(data["phone_dialed__organization"])
        if "date" not in tmp:
            tmp["date"] = data["date"].strftime('%Y-%m-%d %H')
            tmp[data["phone_dialed__organization"]] = data['total']
        else:
            if tmp["date"] == data["date"].strftime('%Y-%m-%d %H'):
                if data["phone_dialed__organization"] in tmp:
                    tmp[data["phone_dialed__organization"]] += data['total']
                else:
                    tmp[data["phone_dialed__organization"]] = data['total']
            else:
                l.append(tmp)
                tmp = {}
                tmp["date"] = data["date"].strftime('%Y-%m-%d %H')
                tmp[data["phone_dialed__organization"]] = data['total']
        l.append(tmp)
    myset = set(names)
    names = list(myset)
    chart_object = generate_chart_object(names, l)

    connecter = TwilioConnecter()
    balance = connecter.get_balance()

    context = {
        "chart": json.dumps(chart_object),
        "twilio_balance": "{}".format(str(balance)),
        "total_this_week": week_count
    }
    return HttpResponse(template.render(context, request))


def upload_file(request):
    file_obj = request.FILES['db_file']
    try:
        Exporter(file_object=file_obj)
    except BaseException as e:
        print(e.args)

    return redirect("call_stats/celeryphonemodel")


def twilio_callback(request):
    pass


def debug_call_route(request):
    if request.GET["action"] == "simulate_cron":
        """something like first time call make. We get only sid from twilio."""
        connecter = TwilioConnecter()
        call_list = connecter.get_calls_list()
        hardcoded_numbers = ["12094397527", "27780142469", "27216851846"]
        sids = {}
        for number in hardcoded_numbers:
            for data in call_list:
                if re.sub("[^0-9]", "", data["to"]) == number:
                    print(data["to"], data["sid"], re.sub("[^0-9]", "", data["to"]))
                    sids[re.sub("[^0-9]", "", data["to"])] = data["sid"]

        numbers = CeleryPhoneModel.objects.filter(number__in=hardcoded_numbers)
        infos = []
        print(sids)
        for number in numbers:
            print(number)
            info = CallStat(phone_dialed=number, time_before_hang=0, sid=sids[number.number], status="sended")
            infos.append(info)
        # print(infos)
        CallStat.objects.bulk_create(infos)
    else:
        pass

    # for number in call_list:
    #     info = CallStat(
    #         phone_dialed=number["to"],
    #         time_before_hang=number["duration"],
    #         sid=number["sid"])
    #     infos.append(info)

    # CallStat.objects.bulk_create(infos)
    # todo find in db by sid to update
    return HttpResponse("debug only")
