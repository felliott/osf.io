import pytz
import logging

from django.db.models import Q

from osf.models import OSFUser
from framework.database import paginated
from ._base import DailyReport

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class NewUserDomainReport(DailyReport):
    def run_daily_report(self):

    def backfill_report(self, date):
        

    def _run_report(self, date):
        user_query = (Q(date_confirmed__date=date) &
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
