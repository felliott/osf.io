import pytz
from datetime import datetime


from mourning_wail.metrics.base import DailyReport
from osf.models import PageCounter


class DownloadCountReport(DailyReport):
    @classmethod
    def run_daily_report(cls, date):
        timestamp_datetime = datetime(date.year, date.month, date.day).replace(tzinfo=pytz.UTC)
        return [{
                'keen': {
                    'timestamp': timestamp_datetime.isoformat()
                },
                'files': {
                    'total': int(PageCounter.get_all_downloads_on_date(timestamp_datetime) or 0)
                },
        }]
