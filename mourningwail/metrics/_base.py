from datetime import date
from hashlib import sha256

from elasticsearch_metrics import metrics


class MeteredEvent(metrics.Metric):
    """MeteredEvent (abstract base for event-based metrics in mourningwail.events)

    Something happened! Let's quickly take note of it and move on,
    then come back later to query/analyze/investigate.
    """

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')
        source = metrics.MetaField(enabled=True)


class DailyReport(metrics.Metric):
    """DailyMeteredReport (abstract base for the report-based metrics in mourningwail.reports)

    There's something we'd like to know about every so often,
    so let's regularly run a report and stash the results here
    (then come back later to query/analyze/investigate)
    """
    report_date = metrics.Date(format='strict_date')

    def get_report_key(self) -> str:
        """a unique key for the report, to avoid accidental duplication

        override in any subclass with multiple reports per date
        """
        report_date = self.report_date
        if isinstance(report_date, date):
            report_date = report_date.isoformat()
        if not isinstance(report_date, str):
            raise ValueError(f'a DailyReport\'s report_date should be date or str, got {type(report_date)}')
        return report_date

    def save(self, **kwargs):
        # hash the report key to get an opaque id
        encoded_key = bytes(self.get_report_key(), encoding='utf')
        self.meta.id = sha256(encoded_key).hexdigest()

        return super().save(**kwargs)

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')
        source = metrics.MetaField(enabled=True)
