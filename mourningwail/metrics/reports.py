from elasticsearch_metrics import metrics

from ._base import DailyReport


class PreprintCountReport(DailyReport):
    provider_name = metrics.Keyword()
    preprint_count = metrics.Integer()


class AddonUsageReport(DailyReport):
    addon_shortname = metrics.Keyword()
    users_enabled_count = metrics.Integer()
    users_authorized_count = metrics.Integer()
    users_linked_count = metrics.Integer()
    nodes_total_count = metrics.Integer()
    nodes_connected_count = metrics.Integer()
    nodes_deleted_count = metrics.Integer()
    nodes_disconnected_count = metrics.Integer()


class DailyDownloadCountReport(DailyReport):
    total_file_downloads = metrics.Integer()


class InstitutionSummaryReport(DailyReport):
    total_users = metrics.Integer()
    new_users_today = metrics.Integer()


class ActiveUsersReport(DailyReport):
    past_day = metrics.Integer()
    past_week = metrics.Integer()
    past_30_days = metrics.Integer()
    past_year = metrics.Integer()
