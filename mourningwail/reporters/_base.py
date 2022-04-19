from datetime import datetime, timedelta
import pytz

from django.utils import timezone

from mourningwail.exceptions import WrongYesterday


class DailyReporter:
    def run_and_record_for_yesterday(self, *, verify_yesterday=None, also_send_to_keen=False):
        yesterday = (timezone.now() - timedelta(days=1)).date()

        if verify_yesterday is not None:
            agreed_on_yesterday = (verify_yesterday == yesterday)
            if not agreed_on_yesterday:
                raise WrongYesterday(verify_yesterday, my_yesterday=yesterday)

        reported_metrics = self.report(yesterday)

        for metric_instance in reported_metrics:
            metric_instance.save()

        if also_send_to_keen:
            keen_event_timestamp = datetime(
                yesterday.year,
                yesterday.month,
                yesterday.day,
                tzinfo=pytz.utc,
            )
            keen_events = self.get_keen_events(reported_metrics, keen_event_timestamp)
            send_events_to_keen(keen_events)  # TODO-quest

    def report(self, date):
        raise NotImplementedError(f'{self.__name__} must implement `report`')

    def get_keen_events(self, reported_metrics, keen_event_timestamp):
        # for back-compat; to be deleted once we don't need keen anymore
        # TODO-quest: implement in subclasses
        raise NotImplementedError(f'{self.__name__} should probably implement get_keen_events')
