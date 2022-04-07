from elasticsearch_metrics import metrics

from mourningwail.metrics._base import MeteredEvent


class FileDownloadEvent(MeteredEvent):
    file_guid = metrics.Keyword()
