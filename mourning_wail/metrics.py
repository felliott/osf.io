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


class MeteredReport(metrics.Metric):
    """MeteredReport (abstract base for report-based metrics)

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
    def run_report(cls):
        raise NotImplementedError(f'{cls.__name__} must implement run_report')

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


##### BEGIN REPORTS #####

class StorageUsageReport(MeteredReport):
    pass  # TODO


class TotalUsersReport(MeteredReport):
    pass  # TODO


class TotalRegistrationsReport(MeteredReport):
    pass  # TODO


class TotalFilesReport(MeteredReport):
    pass  # TODO


class TotalProjectsReport(MeteredReport):
    pass  # TODO


class TotalPreprintsReport(MeteredReport):
    pass  # TODO

##### END REPORTS #####
