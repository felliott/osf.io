import logging
import requests

from mourningwail.metrics.base import DailyReport

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

LOG_THRESHOLD = 11


class PreprintCountReport(DailyReport):
    @classmethod
    def run_daily_report(cls, day_start, day_end):
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
                                    'lte': '{}||/d'.format(day_end.strftime('%Y-%m-%d'))
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
            counts.append({
                'keen': {
                    'timestamp': day_start.isoformat()
                },
                'provider': {
                    'name': preprint_provider.name,
                    'total': resp['hits']['total'],
                },
            })
            logger.info('{} Preprints counted for the provider {}'.format(resp['hits']['total'], preprint_provider.name))

        return counts
