from django.utils import timezone
from elasticsearch_metrics import metrics

from mourningwail.metrics._base import MeteredEvent


class PageVisitEvent(MeteredEvent):
    # fields that should be provided by the client
    referer_url = metrics.Keyword()
    session_id = metrics.Keyword()
    node_guid = metrics.Keyword()
    page_title = metrics.Keyword()
    page_path = metrics.Keyword()

    # fields generated from the above
    path_n_title = metrics.Keyword()
    hour_of_day = metrics.Integer()

    # whatever dumpbucket
    keenstyle_event_info = metrics.Object(dynamic=True)

    @classmethod
    def record(cls, *, timestamp=None, **kwargs):
        timestamp = timestamp or timezone.now()
        return super().record(
            timestamp=timestamp,
            hour_of_day=timestamp.hour,
            **kwargs,
        )


class FileDownloadEvent(MeteredEvent):
    file_guid = metrics.Keyword()


class SystemLogEvent(MeteredEvent):
    pass  # TODO-quest


class UiInteractionEvent(MeteredEvent):
    pass  # TODO-quest
