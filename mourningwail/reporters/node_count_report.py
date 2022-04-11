from django.db.models import Q
import logging

from ._base import DailyReport


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class NodeCountReport(DailyReport):

    @classmethod
    def run_daily_report(cls, day_start, day_end):
        from osf.models import Node, Registration
        from osf.models.spam import SpamStatus

        node_qs = Node.objects.filter(is_deleted=False, created__lte=day_end)
        registration_qs = Registration.objects.filter(is_deleted=False, created__lte=day_end)

        public_query = Q(is_public=True)
        private_query = Q(is_public=False)

        # node_query encompasses lte query_datetime
        daily_query = Q(created__gte=day_start)
        retracted_query = Q(retraction__isnull=False)

        # `embargoed` used private status to determine embargoes, but old registrations could be private and unapproved registrations can also be private
        # `embargoed_v2` uses future embargo end dates on root
        embargo_v2_query = Q(root__embargo__end_date__gt=day_end)

        exclude_spam = ~Q(spam_status__in=[SpamStatus.SPAM, SpamStatus.FLAGGED])

        totals = {
            'keen': {
                'timestamp': day_start.isoformat()
            },
            # Nodes - the number of projects and components
            'nodes': {
                'total': node_qs.count(),
                'total_excluding_spam': node_qs.filter(exclude_spam).count(),
                'public': node_qs.filter(public_query).count(),
                'private': node_qs.filter(private_query).count(),
                'total_daily': node_qs.filter(daily_query).count(),
                'total_daily_excluding_spam': node_qs.filter(daily_query).filter(exclude_spam).count(),
                'public_daily': node_qs.filter(public_query & daily_query).count(),
                'private_daily': node_qs.filter(private_query & daily_query).count(),
            },
            # Projects - the number of top-level only projects
            'projects': {
                'total': node_qs.get_roots().count(),
                'total_excluding_spam': node_qs.get_roots().filter(exclude_spam).count(),
                'public': node_qs.filter(public_query).get_roots().count(),
                'private': node_qs.filter(private_query).get_roots().count(),
                'total_daily': node_qs.filter(daily_query).get_roots().count(),
                'total_daily_excluding_spam': node_qs.filter(daily_query).get_roots().filter(exclude_spam).count(),
                'public_daily': node_qs.filter(public_query & daily_query).get_roots().count(),
                'private_daily': node_qs.filter(private_query & daily_query).get_roots().count(),
            },
            # Registered Nodes - the number of registered projects and components
            'registered_nodes': {
                'total': registration_qs.count(),
                'public': registration_qs.filter(public_query).count(),
                'embargoed': registration_qs.filter(private_query).count(),
                'embargoed_v2': registration_qs.filter(private_query & embargo_v2_query).count(),
                'withdrawn': registration_qs.filter(retracted_query).count(),
                'total_daily': registration_qs.filter(daily_query).count(),
                'public_daily': registration_qs.filter(public_query & daily_query).count(),
                'embargoed_daily': registration_qs.filter(private_query & daily_query).count(),
                'embargoed_v2_daily': registration_qs.filter(private_query & daily_query & embargo_v2_query).count(),
                'withdrawn_daily': registration_qs.filter(retracted_query & daily_query).count(),

            },
            # Registered Projects - the number of registered top level projects
            'registered_projects': {
                'total': registration_qs.get_roots().count(),
                'public': registration_qs.filter(public_query).get_roots().count(),
                'embargoed': registration_qs.filter(private_query).get_roots().count(),
                'embargoed_v2': registration_qs.filter(private_query & embargo_v2_query).get_roots().count(),
                'withdrawn': registration_qs.filter(retracted_query).get_roots().count(),
                'total_daily': registration_qs.filter(daily_query).get_roots().count(),
                'public_daily': registration_qs.filter(public_query & daily_query).get_roots().count(),
                'embargoed_daily': registration_qs.filter(private_query & daily_query).get_roots().count(),
                'embargoed_v2_daily': registration_qs.filter(private_query & daily_query & embargo_v2_query).get_roots().count(),
                'withdrawn_daily': registration_qs.filter(retracted_query & daily_query).get_roots().count(),
            }
        }

        logger.info(
            'Nodes counted. Nodes: {}, Projects: {}, Registered Nodes: {}, Registered Projects: {}'.format(
                totals['nodes']['total'],
                totals['projects']['total'],
                totals['registered_nodes']['total'],
                totals['registered_projects']['total']
            )
        )

        logger.info(totals)
        return [totals]
