from elasticsearch_metrics import metrics

from ._base import MeteredReport


class PreprintCountReport(MeteredReport):
    provider_name = metrics.Keyword()
    preprint_count = metrics.Integer()


class AddonUsageReport(MeteredReport):
    addon_shortname = metrics.Keyword()
    users_enabled_count = metrics.Integer()
    users_authorized_count = metrics.Integer()
    users_linked_count = metrics.Integer()
    nodes_total_count = metrics.Integer()
    nodes_connected_count = metrics.Integer()
    nodes_deleted_count = metrics.Integer()
    nodes_disconnected_count = metrics.Integer()

