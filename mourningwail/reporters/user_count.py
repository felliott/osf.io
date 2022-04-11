from __future__ import division

from keen import KeenClient
import logging
import requests

from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Q
from keen import exceptions as keen_exceptions

from osf.models import OSFUser
from framework.database import paginated
from framework import sentry

from ._base import DailyReporter


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

LOG_THRESHOLD = 11


# Modified from scripts/analytics/depth_users.py
def count_user_logs(user):
    logs = user.logs.all()
    length = logs.count()
    if length == LOG_THRESHOLD:
        item = logs.first()
        if item.action == 'project_created' and item.node.is_bookmark_collection:
            length -= 1
    return length


class UserCountReporter(DailyReporter):
    def calculate_stickiness(self, date):
        """Calculate the stickiness for date: (Unique users yesterday) / (Unique users over yesterday + 29 days) [total of 30 days]"""
        day_start = datetime(date.year, date.month, date.day)
        day_end = day_start + timedelta(days=1)

        client = KeenClient(
            project_id=settings.KEEN['public']['project_id'],
            read_key=settings.KEEN['public']['read_key'],
        )

        day_end_iso = day_end.isoformat()
        last_thirty = client.count_unique(
            event_collection='pageviews',
            # beginning of yesterday - 29 days = 30 total days
            timeframe={'start': (day_start - timedelta(days=29)).isoformat(), 'end': day_end_iso},
            target_property='user.id',
            timezone='UTC'
        )

        last_one = client.count_unique(
            event_collection='pageviews',
            timeframe={'start': day_start.isoformat(), 'end': day_end_iso},
            target_property='user.id',
            timezone='UTC'
        )

        # avoid unlikely divide by 0 error
        if last_thirty == 0:
            return 0
        return last_one / last_thirty

    def report(self, date):
        active_user_query = (
            Q(is_registered=True) &
            Q(password__isnull=False) &
            Q(merged_by__isnull=True) &
            Q(date_disabled__isnull=True) &
            Q(date_confirmed__isnull=False) &
            Q(date_confirmed__date__lt=date)
        )

        active_users = 0
        depth_users = 0
        profile_edited = 0
        user_pages = paginated(OSFUser, query=active_user_query)
        for user in user_pages:
            active_users += 1
            log_count = count_user_logs(user)
            if log_count >= LOG_THRESHOLD:
                depth_users += 1
            if user.social or user.schools or user.jobs:
                profile_edited += 1
        new_users = OSFUser.objects.filter(
            is_active=True,
            date_confirmed__date=date,
        )
        counts = {
            'status': {
                'active': active_users,
                'depth': depth_users,
                'new_users_daily': new_users.count(),
                'new_users_with_institution_daily': new_users.filter(affiliated_institutions__isnull=False).count(),
                'unconfirmed': OSFUser.objects.filter(date_registered__date__lte=date, date_confirmed__isnull=True).count(),
                'deactivated': OSFUser.objects.filter(date_disabled__isnull=False, date_disabled__date__lte=date).count(),
                'merged': OSFUser.objects.filter(date_registered__date__lte=date, merged_by__isnull=False).count(),
                'profile_edited': profile_edited,
            }
        }

        try:
            # Because this data reads from Keen it could fail if Keen read api fails while writing is still allowed
            counts['status']['stickiness'] = self.calculate_stickiness(date)
        except (requests.exceptions.ConnectionError, keen_exceptions.InvalidProjectIdError):
            sentry.log_message('Unable to read from Keen. stickiness metric not collected for date {}'.format(date.isoformat()))

        logger.info(
            'Users counted. Active: {}, Depth: {}, Unconfirmed: {}, Deactivated: {}, Merged: {}, Profile Edited: {}'.format(
                counts['status']['active'],
                counts['status']['depth'],
                counts['status']['unconfirmed'],
                counts['status']['deactivated'],
                counts['status']['merged'],
                counts['status']['profile_edited']
            )
        )
        return [counts]

    # TODO-quest
    # def get_keen_events(self, report_result, keen_event_timestamp):
