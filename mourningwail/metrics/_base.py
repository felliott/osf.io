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


class DailyMeteredReport(metrics.Metric):
    """DailyMeteredReport (abstract base for the report-based metrics in mourningwail.reports)

    There's something we'd like to know about every so often,
    so let's regularly run a report and stash the results here
    (then come back later to query/analyze/investigate)
    """
    date_reported_on = metrics.Date()

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')
        source = metrics.MetaField(enabled=True)
