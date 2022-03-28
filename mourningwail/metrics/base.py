from datetime import datetime, timedelta
import pytz

from django.utils import timezone

from elasticsearch_metrics import metrics


class MeteredEvent(metrics.Metric):
    """MeteredEvent (abstract base for event-based metrics)

    Something happened! Let's quickly take note of it and move on,
    then come back later to query/analyze/investigate.
    """

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')  # TODO-quest: is this inherited?
        # source = metrics.MetaField(enabled=True)


class DailyReport(metrics.Metric):
    """DailyReport (abstract base for the report-based metrics in mourningwail.reports)

    There's something we'd like to know about every so often,
    so let's regularly run a report and stash the results here
    (then come back later to query/analyze/investigate)
    """

    run_duration_milliseconds = metrics.Integer()

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')  # TODO-quest: is this inherited?
        # source = metrics.MetaField(enabled=True)

    @classmethod
    def run_and_record_daily_report(cls, date):
        day_start = datetime(date.year, date.month, date.day, tzinfo=pytz.UTC)
        day_end = day_start + timedelta(days=1)

        # measure duration using wall-clock time (not cpu time),
        # because a database likely does much of the work
        time_report_started = timezone.now()
        daily_report = cls.run_daily_report(day_start, day_end)
        time_report_finished = timezone.now()

        run_duration = (time_report_finished - time_report_started)

        cls.record(
            # TODO-quest: decide what shape daily_report is, put it here
            run_duration_milliseconds=(run_duration / timedelta(milliseconds=1)),
        )

        keen_events = cls.get_keen_events(daily_report)

    @classmethod
    def run_daily_report(cls, day_start, day_end):
        raise NotImplementedError(f'{cls.__name__} must implement run_daily_report')

    @classmethod
    def get_keen_events(cls, daily_report):
        # for back-compat; to be deleted once we don't need keen anymore
        # TODO-quest: implement in subclasses
        raise NotImplementedError(f'{cls.__name__} should probably implement get_keen_events')
