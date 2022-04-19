from elasticsearch_metrics import metrics

from ._base import DailyMeteredReport


class PreprintCountReport(DailyMeteredReport):
    provider_name = metrics.Keyword()
    preprint_count = metrics.Integer()


class AddonUsageReport(DailyMeteredReport):
    addon_shortname = metrics.Keyword()
    users_enabled_count = metrics.Integer()
    users_authorized_count = metrics.Integer()
    users_linked_count = metrics.Integer()
    nodes_total_count = metrics.Integer()
    nodes_connected_count = metrics.Integer()
    nodes_deleted_count = metrics.Integer()
    nodes_disconnected_count = metrics.Integer()


class DailyDownloadCountReport(DailyMeteredReport):
    report_date = metrics.Date()
    total_file_downloads = metrics.Integer()


class InstitutionSummaryReport(DailyMeteredReport):
    total_users = metrics.Integer()
    new_users_today = metrics.Integer()
