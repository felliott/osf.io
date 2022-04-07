from datetime import datetime, timedelta
import pytz

from django.utils import timezone

from mourningwail.metrics.base import MeteredReportResult
from mourningwail.exceptions import WrongYesterday


class SnapshotReport:
    # TODO-quest: RESULT_METRIC =

    def run_and_record(self, *, also_send_to_keen=False):
        pass  # TODO-quest

    def get_keen_events(self, snapshot, keen_event_timestamp):
        # for back-compat; to be deleted once we don't need keen anymore
        # TODO-quest: implement in subclasses
        raise NotImplementedError(f'{self.__name__} should probably implement get_keen_events')


class DailySummaryReport:
    def run_and_record_for_yesterday(self, *, verify_yesterday=None, also_send_to_keen=False):
        time_report_started = timezone.now()
        yesterday = (time_report_started - timedelta(days=1)).date()

        if verify_yesterday is not None:
            agreed_on_yesterday = (verify_yesterday == yesterday)
            if not agreed_on_yesterday:
                raise WrongYesterday(verify_yesterday, my_yesterday=yesterday)

        yesterday_summary = self.summarize_day()

        time_report_finished = timezone.now()
        run_duration = (time_report_finished - time_report_started)

        MeteredReport.record(
            # TODO-quest: decide what shape daily_report is, put it here
            run_duration_milliseconds=(run_duration / timedelta(milliseconds=1)),
        )

        if also_send_to_keen:
            keen_event_timestamp = datetime(
                yesterday.year,
                yesterday.month,
                yesterday.day,
                tzinfo=pytz.utc,
            )
            keen_events = self.get_keen_events(yesterday_summary, keen_event_timestamp)
            send_events_to_keen(keen_events)  # TODO-quest

    def summarize_day(self, date):
        raise NotImplementedError(f'{self.__name__} must implement run_daily_report')

    def get_keen_events(self, daily_summary, keen_event_timestamp):
        # for back-compat; to be deleted once we don't need keen anymore
        # TODO-quest: implement in subclasses
        raise NotImplementedError(f'{self.__name__} should probably implement get_keen_events')
