import logging
import requests

from mourningwail.metrics import PreprintCountReport
from ._base import DailyReporter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

LOG_THRESHOLD = 11


class PreprintCountReporter(DailyReporter):
    def report(self, date):
        from osf.models import PreprintProvider

        elastic_query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'type': 'preprint'
                            }
                        },
                        {
                            'match': {
                                'sources': None
                            }
                        }
                    ],
                    'filter': [
                        {
                            'range': {
                                'date': {
                                    'lte': '{}||/d'.format(date.strftime('%Y-%m-%d'))
                                }
                            }
                        }
                    ]
                }
            }
        }

        counts = []
        for preprint_provider in PreprintProvider.objects.all():
            name = preprint_provider.name if preprint_provider.name != 'Open Science Framework' else 'OSF'
            elastic_query['query']['bool']['must'][1]['match']['sources'] = name
            resp = requests.post('https://share.osf.io/api/v2/search/creativeworks/_search', json=elastic_query).json()
            counts.append(
                PreprintCountReport(
                    date_reported_on=date,
                    provider_name=preprint_provider.name,
                    preprint_count=resp['hits']['total'],
                )
            )
            logger.info('{} Preprints counted for the provider {}'.format(resp['hits']['total'], preprint_provider.name))

        return counts

    def get_keen_events(self, reports, keen_event_timestamp):
        return [
            {
                'keen': {'timestamp': keen_event_timestamp},
                'provider': {
                    'name': preprint_count_metric.provider_name,
                    'total': preprint_count_metric.preprint_count,
                },
            }
            for preprint_count_metric in reports
        ]
