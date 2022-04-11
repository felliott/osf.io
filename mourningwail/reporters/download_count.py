from osf.models import PageCounter

from ._base import DailyReporter


class DownloadCountReporter(DailyReporter):
    def report(self, date):
        return int(PageCounter.get_all_downloads_on_date(date) or 0)

    def get_keen_events(self, report_result, keen_event_timestamp):
        return [
            {
                'keen': {
                    'timestamp': keen_event_timestamp,
                },
                'files': {
                    'total': report_result,
                },
            }
        ]
