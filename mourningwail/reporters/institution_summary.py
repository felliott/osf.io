import logging

from django.db.models import Q

from osf.models import Institution
from ._base import DailyReporter


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class InstitutionSummaryReporter(DailyReporter):
    def report(self, date):
        institutions = Institution.objects.all()
        counts = []

        daily_query = Q(created__date=date)
        public_query = Q(is_public=True)
        private_query = Q(is_public=False)

        # `embargoed` used private status to determine embargoes, but old registrations could be private and unapproved registrations can also be private
        # `embargoed_v2` uses future embargo end dates on root
        embargo_v2_query = Q(root__embargo__end_date__date__gt=date)

        for institution in institutions:
            node_qs = institution.nodes.filter(
                is_deleted=False,
                created__date__lte=date,
            ).exclude(type='osf.registration')
            registration_qs = institution.nodes.filter(
                is_deleted=False,
                created__date__lte=date,
                type='osf.registration',
            )

            count = {
                'institution': {
                    'id': institution._id,
                    'name': institution.name,
                },
                'users': {
                    'total': institution.osfuser_set.filter(is_active=True).count(),
                    'total_daily': institution.osfuser_set.filter(date_confirmed__date=date).count(),
                },
                'nodes': {
                    'total': node_qs.count(),
                    'public': node_qs.filter(public_query).count(),
                    'private': node_qs.filter(private_query).count(),

                    'total_daily': node_qs.filter(daily_query).count(),
                    'public_daily': node_qs.filter(public_query & daily_query).count(),
                    'private_daily': node_qs.filter(private_query & daily_query).count(),
                },
                # Projects use get_roots to remove children
                'projects': {
                    'total': node_qs.get_roots().count(),
                    'public': node_qs.filter(public_query).get_roots().count(),
                    'private': node_qs.filter(private_query).get_roots().count(),

                    'total_daily': node_qs.filter(daily_query).get_roots().count(),
                    'public_daily': node_qs.filter(public_query & daily_query).get_roots().count(),
                    'private_daily': node_qs.filter(private_query & daily_query).get_roots().count(),
                },
                'registered_nodes': {
                    'total': registration_qs.count(),
                    'public': registration_qs.filter(public_query).count(),
                    'embargoed': registration_qs.filter(private_query).count(),
                    'embargoed_v2': registration_qs.filter(private_query & embargo_v2_query).count(),

                    'total_daily': registration_qs.filter(daily_query).count(),
                    'public_daily': registration_qs.filter(public_query & daily_query).count(),
                    'embargoed_daily': registration_qs.filter(private_query & daily_query).count(),
                    'embargoed_v2_daily': registration_qs.filter(private_query & daily_query & embargo_v2_query).count(),
                },
                'registered_projects': {
                    'total': registration_qs.get_roots().count(),
                    'public': registration_qs.filter(public_query).get_roots().count(),
                    'embargoed': registration_qs.filter(private_query).get_roots().count(),
                    'embargoed_v2': registration_qs.filter(private_query & embargo_v2_query).get_roots().count(),

                    'total_daily': registration_qs.filter(daily_query).get_roots().count(),
                    'public_daily': registration_qs.filter(public_query & daily_query).get_roots().count(),
                    'embargoed_daily': registration_qs.filter(private_query & daily_query).get_roots().count(),
                    'embargoed_v2_daily': registration_qs.filter(private_query & daily_query & embargo_v2_query).get_roots().count(),
                },
                'keen': {
                    'timestamp': day_start.isoformat()
                }
            }

            logger.info(
                '{} Nodes counted. Nodes: {}, Projects: {}, Registered Nodes: {}, Registered Projects: {}'.format(
                    count['institution']['name'],
                    count['nodes']['total'],
                    count['projects']['total'],
                    count['registered_nodes']['total'],
                    count['registered_projects']['total']
                )
            )

            counts.append(count)
        return counts

    # TODO-quest
    # def get_keen_events(self, report_result, keen_event_timestamp):
