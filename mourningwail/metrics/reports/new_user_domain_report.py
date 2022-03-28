import pytz
import logging
from datetime import datetime, timedelta

from django.db.models import Q

from osf.models import OSFUser
from framework.database import paginated
from mourningwail.metrics.base import DailyReport

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class NewUserDomainReport(DailyReport):
    @classmethod
    def run_daily_report(cls, date):
        # In the end, turn the date back into a datetime at midnight for queries
        date = datetime(date.year, date.month, date.day).replace(tzinfo=pytz.UTC)

        logger.info('Gathering user domains between {} and {}'.format(
            date, (date + timedelta(days=1)).isoformat()
        ))
        user_query = (Q(date_confirmed__lt=date + timedelta(days=1)) &
                      Q(date_confirmed__gte=date) &
                      Q(username__isnull=False))
        users = paginated(OSFUser, query=user_query)
        user_domain_events = []
        for user in users:
            user_date = user.date_confirmed.replace(tzinfo=pytz.UTC)
            event = {
                'keen': {'timestamp': user_date.isoformat()},
                'date': user_date.isoformat(),
                'domain': user.username.split('@')[-1]
            }
            user_domain_events.append(event)

        logger.info('User domains collected. {} users and their email domains.'.format(len(user_domain_events)))
        return user_domain_events
