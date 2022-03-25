import pytz

import logging
import requests
from datetime import datetime, timedelta

from mourning_wail.metrics import DailyReport

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

LOG_THRESHOLD = 11


class PreprintCountReport(DailyReport):
    @classmethod
    def get_daily_report(cls, date):
        from osf.models import PreprintProvider

        # Convert to a datetime at midnight for queries and the timestamp
        timestamp_datetime = datetime(date.year, date.month, date.day).replace(tzinfo=pytz.UTC)
        query_datetime = timestamp_datetime + timedelta(days=1)

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
                                    'lte': '{}||/d'.format(query_datetime.strftime('%Y-%m-%d'))
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
                    'timestamp': timestamp_datetime.isoformat()
                },
                'provider': {
                    'name': preprint_provider.name,
                    'total': resp['hits']['total'],
                },
            })
            logger.info('{} Preprints counted for the provider {}'.format(resp['hits']['total'], preprint_provider.name))

        return counts
