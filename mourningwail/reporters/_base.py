from datetime import datetime, timedelta
import pytz

from django.utils import timezone

from mourningwail.exceptions import WrongYesterday
from mourningwail.metrics._base import DailyReport


def send_events_to_keen(keen_events):
    raise NotImplementedError  # TODO-quest


class DailyReporter:
    def run_and_record_for_yesterday(self, *, verify_yesterday=None, also_send_to_keen=False):
        yesterday = (timezone.now() - timedelta(days=1)).date()

        if verify_yesterday is not None:
            agreed_on_yesterday = (verify_yesterday == yesterday)
            if not agreed_on_yesterday:
                raise WrongYesterday(verify_yesterday, my_yesterday=yesterday)
        return self.run_and_record_for_date(
            report_date=yesterday,
            also_send_to_keen=also_send_to_keen,
        )

    def run_and_record_for_date(self, report_date, *, also_send_to_keen=False):
        reports = self.report(report_date)
        if isinstance(reports, DailyReport):
            reports = [reports]

        for report in reports:
            report.save()

        if also_send_to_keen:
            keen_event_timestamp = datetime(
                report_date.year,
                report_date.month,
                report_date.day,
                tzinfo=pytz.utc,
            )
            keen_events = self.get_keen_events(reports, keen_event_timestamp)
            send_events_to_keen(keen_events)

    def report(self, report_date):
        """build one or more reports for the given date

        return mourningwail.metrics._base.DailyReport or a list of them
        """
        raise NotImplementedError(f'{self.__name__} must implement `report`')

    def get_keen_events(self, reports, keen_event_timestamp):
        # for back-compat; to be deleted once we don't need keen anymore
        # TODO-quest: implement in subclasses
        raise NotImplementedError(f'{self.__name__} should probably implement get_keen_events')
