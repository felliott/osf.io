from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_GET
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView

from api.nodes.permissions import ContributorOrPublic

from mourningwail.metrics.events import PageVisitEvent
from mourningwail.metrics import reports
from mourningwail.node_analytics import get_node_analytics


class NodeAnalytics(APIView):
    permission_classes = (
        ContributorOrPublic,  # TODO-quest: check this
    )

    view_category = 'mourningwail'
    view_name = 'node-analytics'

    def get(self, request, node_guid, timespan):
        return JsonResponse(
            get_node_analytics(node_guid, timespan)
        )


class PageVisit(APIView):
    view_category = 'mourningwail'
    view_name = 'page-visit'

    def post(self, request):
        request_bod = request.POST

        # TODO-quest: check for obvious fakery
        # TODO-quest: handle dead elastic gracefully (ideally without losing data)

        PageVisitEvent.record(
            node_guid=request_bod.get('node_guid'),
            page_path=request_bod.get('page_path'),
            page_title=request_bod.get('page_title'),
            referer_domain=request_bod.get('referer_domain'),
        )
        return HttpResponse(status=201)


class KeenstylePageVisit(APIView):
    # for compatibility with the requests we were sending to keen.io

    view_category = 'mourningwail'
    view_name = 'keenstyle-page-visit'

    def post(self, request):
        # keen_payload = request.json()

        PageVisitEvent.record(
            # TODO-quest: translate from keen load
        )
        return HttpResponse(status=201)


VIEWABLE_REPORTS = {
    'preprint_count': reports.PreprintCountReport,
    # 'addon_usage': reports.AddonUsageReport,
    # 'daily_download_count': reports.DailyDownloadCountReport,
    # 'institution_summary': reports.InstitutionSummaryReport,
}


def serialize_report(report):
    # TODO-quest: explicit decoupling
    return report.to_dict()


@require_GET
@permission_required('osf.view_metrics')
def get_recent_reports(self, request, report_name):
    try:
        report_class = VIEWABLE_REPORTS[report_name]
    except KeyError:
        return HttpResponse(status=404, content=f'unknown report: "{report_name}"')

    # TODO-quest: start/end daterange
    days_back = request.GET['days_back']

    search_recent = (
        report_class.search()
        .filter('range', date_reported_on={'gte': f'now/d-{days_back}d'})
        .sort('-date_reported_on')
    )

    search_response = search_recent.execute()
    return JsonResponse(
        [serialize_report(hit) for hit in search_response]
    )


@require_GET
@permission_required('osf.view_metrics')
def get_latest_report(self, request, report_name):
    try:
        report_class = VIEWABLE_REPORTS[report_name]
    except KeyError:
        return HttpResponse(status=404, content=f'unknown report: "{report_name}"')

    latest_search = (
        report_class.search()
        .sort('-date_reported_on')
        [0]
    )

    search_response = latest_search.execute()
    if not search_response.hits:
        return HttpResponse(status=404, content=f'no "{report_name}" reports found')
    latest_report = search_response.hits[0]

    return JsonResponse(serialize_report(latest_report))
