from osf.models import OSFUser

from mourningwail.metrics import UserCountReport
from ._base import DailyReporter


class UserCountReporter(DailyReporter):

    def report(self, report_date):
        # TODO-quest: consider an index on is_active,date_confirmed
        active_user_count = OSFUser.objects.filter(
            is_active=True,
            date_confirmed__date__lte=report_date,
        ).count()
        new_user_count = OSFUser.objects.filter(
            is_active=True,
            date_confirmed__date=report_date,
        ).count()

        return UserCountReport(
            total_user_count=active_user_count,
            new_user_count=new_user_count,
        )

    # TODO-quest
    # def get_keen_events(self, report_result, keen_event_timestamp):
    #         'status': {
    #             'active': confirmed_users,
    #             'depth': depth_users,
    #             'new_users_daily': new_users.count(),
    #             'new_users_with_institution_daily': new_users.filter(affiliated_institutions__isnull=False).count(),
    #             'unconfirmed': OSFUser.objects.filter(date_registered__date__lte=date, date_confirmed__isnull=True).count(),
    #             'deactivated': OSFUser.objects.filter(date_disabled__isnull=False, date_disabled__date__lte=date).count(),
    #             'merged': OSFUser.objects.filter(date_registered__date__lte=date, merged_by__isnull=False).count(),
    #             'profile_edited': profile_edited,
    #         }
