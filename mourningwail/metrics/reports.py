from elasticsearch_metrics import metrics

from ._base import DailyReport


class PreprintCountReport(DailyReport):
    provider_key = metrics.Keyword()
    preprint_count = metrics.Integer()

    def get_report_key(self):
        key = super().get_report_key()
        return f'{key}--{self.provider_key}'


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
    institution_key = metrics.Keyword()
    total_users = metrics.Integer()
    new_users_today = metrics.Integer()

    def get_report_key(self):
        key = super().get_report_key()
        return f'{key}--{self.institution_key}'


class ActiveUsersReport(DailyReport):
    past_day = metrics.Integer()
    past_week = metrics.Integer()
    past_30_days = metrics.Integer()
    past_year = metrics.Integer()
