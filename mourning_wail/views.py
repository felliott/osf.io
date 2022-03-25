from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView

from api.nodes.permissions import ContributorOrPublic

from mourning_wail.metrics import PageVisitEvent
from mourning_wail.node_analytics import get_node_analytics


class NodeAnalytics(APIView):
    permission_classes = (
        ContributorOrPublic,  # TODO check this
    )

    view_category = 'metrics'
    view_name = 'node-analytics'

    def get(self, request, node_guid, timespan):
        return JsonResponse(
            get_node_analytics(node_guid, timespan)
        )


class PageVisit(APIView):
    view_category = 'metrics'
    view_name = 'page-visit'

    def post(self, request):
        request_bod = request.POST

        # TODO check for obvious fakery
        # TODO handle dead elastic gracefully (ideally without losing data)

        PageVisitEvent.record(
            node_guid=request_bod.get('node_guid'),
            page_path=request_bod.get('page_path'),
            page_title=request_bod.get('page_title'),
            referer_domain=request_bod.get('referer_domain'),
        )
        return HttpResponse(status=201)


class MourningWailPageVisit(APIView):
    # for compatibility with the requests we were sending to keen.io
    # "keen (noun): a mourning wail"

    view_category = 'metrics'
    view_name = 'mourning-wail-page-visit'

    def post(self, request):
        # keen_payload = request.json()

        PageVisitEvent.record(
            # TODO translate from keen load
        )
        return HttpResponse(status=201)
