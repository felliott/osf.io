from datetime import timedelta
import logging

from django.utils import timezone

from framework.celery_tasks import app as celery_app
from mourning_wail.reports import DAILY_REPORTS
from scripts.utils import add_file_logger


logger = logging.getLogger(__file__)


@celery_app.task(name='mourning_wail.tasks.run_daily_reports')
def run_daily_reports():
    add_file_logger(logger, __file__)

    # run all reports for the same yesterday
    yesterday = (timezone.now() - timedelta(days=1)).date()

    for report_class in DAILY_REPORTS:
        report_class.run_and_record_daily_report(yesterday)
