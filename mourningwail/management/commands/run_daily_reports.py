from django.core.management.base import BaseCommand

from mourningwail.tasks import run_daily_reports


class Command(BaseCommand):
    def handle(self, *args, fake=False, **kwargs):
        if fake:
        else:
            run_daily_reports()
