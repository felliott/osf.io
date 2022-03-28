from elasticsearch_metrics import metrics

from mourning_wail.metrics.base import MeteredEvent


class FileDownloadEvent(MeteredEvent):
    file_guid = metrics.Keyword()
