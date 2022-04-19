
QUERYABLE_METRICS = {
    'page_view_event': PageViewEvent,
}


def query_metric_field(metric_name, field_name, query_type, start_date, end_date):
    # metric_name: checked against static QUERYABLE_METRICS
    # field_name: checked against static list of allowed fields per metric
    # query_type: "sum" or "count" or "count_unique"?
    pass
