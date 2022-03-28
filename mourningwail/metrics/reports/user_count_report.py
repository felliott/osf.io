from __future__ import division

from keen import KeenClient
import logging
import requests

from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from keen import exceptions as keen_exceptions

from osf.models import OSFUser
from framework.database import paginated
from framework import sentry
from mourningwail.metrics.base import DailyReport

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


class UserCountReport(DailyReport):
    @classmethod
    def calculate_stickiness(cls, time_one, time_two):
        """Calculate the stickiness for date: (Unique users yesterday) / (Unique users over yesterday + 29 days) [total of 30 days]"""
        client = KeenClient(
            project_id=settings.KEEN['public']['project_id'],
            read_key=settings.KEEN['public']['read_key'],
        )

        time_two_iso = time_two.isoformat()
        last_thirty = client.count_unique(
            event_collection='pageviews',
            # beginning of yesterday - 29 days = 30 total days
            timeframe={'start': (time_one - timedelta(days=29)).isoformat(), 'end': time_two_iso},
            target_property='user.id',
            timezone='UTC'
        )

        last_one = client.count_unique(
            event_collection='pageviews',
            timeframe={'start': time_one.isoformat(), 'end': time_two_iso},
            target_property='user.id',
            timezone='UTC'
        )

        # avoid unlikely divide by 0 error
        if last_thirty == 0:
            return 0
        return last_one / last_thirty

    @classmethod
    def run_daily_report(cls, day_start, day_end):
        active_user_query = (
            Q(is_registered=True) &
            Q(password__isnull=False) &
            Q(merged_by__isnull=True) &
            Q(date_disabled__isnull=True) &
            Q(date_confirmed__isnull=False) &
            Q(date_confirmed__lt=day_end)
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
        new_users = OSFUser.objects.filter(is_active=True, date_confirmed__gte=day_start, date_confirmed__lt=day_end)
        counts = {
            'keen': {
                'timestamp': day_start.isoformat()
            },
            'status': {
                'active': active_users,
                'depth': depth_users,
                'new_users_daily': new_users.count(),
                'new_users_with_institution_daily': new_users.filter(affiliated_institutions__isnull=False).count(),
                'unconfirmed': OSFUser.objects.filter(date_registered__lt=day_end, date_confirmed__isnull=True).count(),
                'deactivated': OSFUser.objects.filter(date_disabled__isnull=False, date_disabled__lt=day_end).count(),
                'merged': OSFUser.objects.filter(date_registered__lt=day_end, merged_by__isnull=False).count(),
                'profile_edited': profile_edited,
            }
        }

        try:
            # Because this data reads from Keen it could fail if Keen read api fails while writing is still allowed
            counts['status']['stickiness'] = cls.calculate_stickiness(day_start, day_end)
        except (requests.exceptions.ConnectionError, keen_exceptions.InvalidProjectIdError):
            sentry.log_message('Unable to read from Keen. stickiness metric not collected for date {}'.format(day_start.isoformat()))

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
