from datetime import timedelta

from django.utils import timezone

from elasticsearch_metrics import metrics


##### BEGIN BASES #####

class MeteredEvent(metrics.Metric):
    """MeteredEvent (abstract base for event-based metrics)

    Something happened! Let's quickly take note of it and move on,
    then come back later to query/analyze/investigate.
    """

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')  # TODO: is this inherited?
        # source = metrics.MetaField(enabled=True)


class DailyReport(metrics.Metric):
    """DailyReport (abstract base for the report-based metrics in mourning_wail.reports)

    There's something we'd like to know about every so often,
    so let's regularly run a report and stash the results here
    (then come back later to query/analyze/investigate)
    """

    run_duration_milliseconds = metrics.Integer()

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')  # TODO: is this inherited?
        # source = metrics.MetaField(enabled=True)

    @classmethod
    def run_and_record_daily_report(cls, date):
        # measure duration using wall-clock time (not cpu time),
        # because a database likely does much of the work
        time_report_started = timezone.now()
        daily_report = cls.run_daily_report(date)
        time_report_finished = timezone.now()

        run_duration = (time_report_finished - time_report_started)

        cls.record(
            **daily_report,
            run_duration_milliseconds=(run_duration / timedelta(milliseconds=1)),
        )

    @classmethod
    def run_daily_report(cls, date):
        raise NotImplementedError(f'{cls.__name__} must implement run_daily_report')

##### END BASES #####


##### BEGIN EVENTS #####

class PageVisitEvent(MeteredEvent):
    referer_domain = metrics.Keyword()
    hour_of_day = metrics.Integer()

    # TODO i don't think copy_to works this way
    page_title = metrics.Keyword(copy_to='path_n_title')
    page_path = metrics.Keyword(copy_to='path_n_title')
    path_n_title = metrics.Keyword()

    def record(self, *, timestamp=None, **kwargs):
        timestamp = timestamp or timezone.now()
        return super().record(
            timestamp=timestamp,
            hour_of_day=timestamp.hour,
            **kwargs,
        )


class FileDownloadEvent(MeteredEvent):
    file_guid = metrics.Keyword()


class UiInteractionEvent(MeteredEvent):
    pass  # TODO


class SystemLogEvent(MeteredEvent):
    pass  # TODO

##### END EVENTS #####
