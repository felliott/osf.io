from django.conf.urls import url

from . import views
from mourning_wail import views as mw_views

app_name = 'osf'

urlpatterns = [
    url(r'^raw/(?P<url_path>[a-z0-9._/]*)$', views.RawMetricsView.as_view(), name=views.RawMetricsView.view_name),
    url(r'^preprints/views/$', views.PreprintViewMetrics.as_view(), name=views.PreprintViewMetrics.view_name),
    url(r'^preprints/downloads/$', views.PreprintDownloadMetrics.as_view(), name=views.PreprintDownloadMetrics.view_name),
    url(r'^registries_moderation/transitions/$', views.RegistriesModerationMetricsView.as_view(), name=views.RegistriesModerationMetricsView.view_name),

    # mourning wail (keen replacement)
    url(r'^node_analytics/(?P<node_guid>[a-z0-9]+)/(?P<timespan>week|fortnight|month)/$', mw_views.NodeAnalytics.as_view(), name=mw_views.NodeAnalytics.view_name),
    url(r'^page_visit/$', mw_views.PageVisit.as_view(), name=mw_views.PageVisit.view_name),
    # TODO endpoint for full back-compat with existing keen usage
]
