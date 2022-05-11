import re
import json
import logging

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView

from api.nodes.permissions import ContributorOrPublic

from mourningwail.metrics.events import PageVisitEvent
from mourningwail.metrics import reports
from mourningwail.node_analytics import get_node_analytics

logger = logging.getLogger(__name__)


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


@require_POST
def log_keenstyle_page_visit(request):
    request_bod = json.loads(request.body)
    keen_eventdata = request_bod['eventData']

    PageVisitEvent.record(
        referer_url=keen_eventdata.get('referrer', {}).get('url'),
        page_path=keen_eventdata.get('page', {}).get('url'),
        page_title=keen_eventdata.get('page', {}).get('title'),
        session_id=keen_eventdata.get('anon', {}).get('id'),
        node_guid=keen_eventdata.get('node', {}).get('id'),
        keenstyle_event_info=keen_eventdata,
    )
    return HttpResponse(status=201)


VIEWABLE_REPORTS = {
    'preprint_count': reports.PreprintCountReport,
    'user_count': reports.UserCountReport,
    # 'addon_usage': reports.AddonUsageReport,
    # 'daily_download_count': reports.DailyDownloadCountReport,
    # 'institution_summary': reports.InstitutionSummaryReport,
}


def serialize_report(report):
    # TODO-quest: explicit decoupling
    report_as_dict = report.to_dict()
    return {
        **report_as_dict,
        'report_date': report_as_dict['report_date'].date().isoformat(),
    }


MAX_REPORTS = 1000


@require_GET
#@permission_required('osf.view_metrics')
def get_report_names(request):
    return JsonResponse({
        'viewable_reports': list(VIEWABLE_REPORTS.keys()),
    })


@require_GET
#@permission_required('osf.view_metrics')
def get_recent_reports(request, report_name):
    try:
        report_class = VIEWABLE_REPORTS[report_name]
    except KeyError:
        return HttpResponse(status=404, content=f'unknown report: "{report_name}"')

    # TODO-quest: start/end daterange?
    days_back = request.GET.get('days_back', 13)

    logger.info('@@@ checking days_back')
    if request.GET.get('keenStyle', False):
        logger.info('@@@   got keenStyle')
        timeframe = request.GET.get('timeframe')
        logger.info('@@@   timeframe is: ({})'.format(timeframe))
        if timeframe is not None:
            m = re.match(r'previous_(\d+)_days', timeframe)
            if m:
                days_back = m.group(1)
            else:
                raise Exception('Unsupported timeframe format: "{}"'.format(timeframe))
        else:
            pass  # just fallback to days_back for now
    logger.info('@@@ soldiering on, days_back:({})'.format(days_back))


    search_recent = (
        report_class.search()
        .filter('range', report_date={'gte': f'now/d-{days_back}d'})
        .sort('-report_date')
        [:MAX_REPORTS]
    )

    search_response = search_recent.execute()
    return JsonResponse(
        {'reports': [serialize_report(hit) for hit in search_response]}
    )


@require_GET
#@permission_required('osf.view_metrics')
def get_latest_report(request, report_name):
    try:
        report_class = VIEWABLE_REPORTS[report_name]
    except KeyError:
        return HttpResponse(status=404, content=f'unknown report: "{report_name}"')

    latest_search = (
        report_class.search()
        .sort('-report_date', '-timestamp')
        [0]
    )

    search_response = latest_search.execute()
    if not search_response.hits:
        return HttpResponse(status=404, content=f'no "{report_name}" reports found')
    latest_report = search_response.hits[0]

    return JsonResponse(serialize_report(latest_report))
