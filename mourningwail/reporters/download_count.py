from osf.models import PageCounter
from mourningwail.metrics.reports import DailyDownloadCountReport
from ._base import DailyReporter


class DownloadCountReporter(DailyReporter):
    def report(self, date):
        total_downloads = int(PageCounter.get_all_downloads_on_date(date) or 0)
        return [
            DailyDownloadCountReport(total_downloads=total_downloads)
        ]

    def get_keen_events(self, reports, keen_event_timestamp):
        return [
            {
                'keen': {
                    'timestamp': keen_event_timestamp,
                },
                'files': {
                    'total': report.total_downloads,
                },
            }
            for report in reports
        ]
