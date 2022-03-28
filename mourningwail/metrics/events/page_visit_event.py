from django.utils import timezone
from elasticsearch_metrics import metrics

from mourningwail.metrics.base import MeteredEvent


class PageVisitEvent(MeteredEvent):
    referer_domain = metrics.Keyword()
    hour_of_day = metrics.Integer()

    # TODO-quest i don't think copy_to works this way
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
