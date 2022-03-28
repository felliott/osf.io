from mourningwail.metrics.base import DailyReport
from osf.models import PageCounter


class DownloadCountReport(DailyReport):
    @classmethod
    def run_daily_report(cls, day_start, day_end):
        return [{
                'keen': {
                    'timestamp': day_start.isoformat()
                },
                'files': {
                    'total': int(PageCounter.get_all_downloads_on_date(day_start) or 0)
                },
                }
                ]
