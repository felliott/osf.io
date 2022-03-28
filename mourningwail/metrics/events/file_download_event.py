from elasticsearch_metrics import metrics

from mourningwail.metrics.base import MeteredEvent


class FileDownloadEvent(MeteredEvent):
    file_guid = metrics.Keyword()
