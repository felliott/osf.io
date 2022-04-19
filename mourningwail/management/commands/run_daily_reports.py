from django.core.management.base import BaseCommand

from mourningwail.tasks import run_daily_reports


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        run_daily_reports()
