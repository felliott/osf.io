from django.conf.urls import url

from . import views


app_name = 'mourningwail'


urlpatterns = [
    url(r'^report/$', views.get_report_names, name='report-names'),
    url(r'^report/(?P<report_name>[a-z0-9_]+)/latest/$', views.get_latest_report, name='latest-report'),
    url(r'^report/(?P<report_name>[a-z0-9_]+)/recent/$', views.get_recent_reports, name='recent-reports'),

    url(r'^event/page_visit/$', views.PageVisit.as_view(), name=views.PageVisit.view_name),

    url(r'^query/node_analytics/(?P<node_guid>[a-z0-9]+)/(?P<timespan>week|fortnight|month)/$', views.NodeAnalytics.as_view(), name=views.NodeAnalytics.view_name),

    # TODO-quest: endpoint for full back-compat with existing keen usage
]
