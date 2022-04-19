from datetime import timedelta
import logging

from django.utils import timezone

from framework.celery_tasks import app as celery_app
from mourningwail.reporters import DAILY_REPORTERS
from scripts.utils import add_file_logger


logger = logging.getLogger(__file__)


@celery_app.task(name='mourningwail.tasks.run_daily_reports')
def run_daily_reports():
    add_file_logger(logger, __file__)

    # run all reports for the same yesterday
    yesterday = (timezone.now() - timedelta(days=1)).date()

    for reporter_class in DAILY_REPORTERS:
        reporter_class().run_and_record_for_yesterday(
            verify_yesterday=yesterday,
            # also_send_to_keen=True,
        )
