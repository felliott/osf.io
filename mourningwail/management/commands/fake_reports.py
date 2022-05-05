from datetime import date, timedelta
from random import randint

from django.core.management.base import BaseCommand

from mourningwail.metrics import UserCountReport, PreprintCountReport


def fake_user_counts(days_back):
    yesterday = date.today() - timedelta(days=1)
    first_report = UserCountReport(
        report_date=(yesterday - timedelta(days=days_back)),
        new_user_count=randint(0, 7),
        total_user_count=randint(0, 23),
    )
    first_report.save()

    last_report = first_report
    while last_report.report_date < yesterday:
        new_user_count = randint(0, 500)
        this_report = UserCountReport(
            report_date=(last_report.report_date + timedelta(days=1)),
            new_user_count=new_user_count,
            total_user_count=(last_report.total_user_count + new_user_count),
        )
        this_report.save()
        last_report = this_report


FAKE_PREPRINT_PROVIDERS = ['foop', 'barp', 'bazp', 'quxp']

def fake_preprint_counts(days_back):
    yesterday = date.today() - timedelta(days=1)
    for day_delta in range(days_back):
        for provider_key in FAKE_PREPRINT_PROVIDERS:
            preprint_count = randint(100, 5000) * (days_back - day_delta)
            PreprintCountReport(
                report_date=yesterday - timedelta(days=day_delta),
                provider_key=provider_key,
                preprint_count=preprint_count,
            ).save()

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fake_user_counts(1000)
        fake_preprint_counts(1000)
        # TODO-quest: more reports
