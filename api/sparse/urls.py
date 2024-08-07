from django.urls import re_path

from api.sparse import views

app_name = 'osf'

urlpatterns = [
    re_path(
        r'^nodes/$',
        views.SparseNodeList.as_view(),
        name=views.SparseNodeList.view_name,
    ),
    re_path(
        r'^nodes/(?P<node_id>\w+)/$',
        views.SparseNodeDetail.as_view(),
        name=views.SparseNodeDetail.view_name,
    ),
    re_path(
        r'^nodes/(?P<node_id>\w+)/children/$',
        views.SparseNodeChildrenList.as_view(),
        name=views.SparseNodeChildrenList.view_name,
    ),
    re_path(
        r'^nodes/(?P<node_id>\w+)/linked_nodes/$',
        views.SparseLinkedNodesList.as_view(),
        name=views.SparseLinkedNodesList.view_name,
    ),
    re_path(
        r'^nodes/(?P<node_id>\w+)/linked_registrations/$',
        views.SparseLinkedRegistrationsList.as_view(),
        name=views.SparseLinkedRegistrationsList.view_name,
    ),

    re_path(
        r'^registrations/$',
        views.SparseRegistrationList.as_view(),
        name=views.SparseRegistrationList.view_name,
    ),
    re_path(
        r'^registrations/(?P<node_id>\w+)/$',
        views.SparseRegistrationDetail.as_view(),
        name=views.SparseRegistrationDetail.view_name,
    ),
    re_path(
        r'^registrations/(?P<node_id>\w+)/children/$',
        views.SparseRegistrationChildrenList.as_view(),
        name=views.SparseRegistrationChildrenList.view_name,
    ),
    re_path(
        r'^registrations/(?P<node_id>\w+)/linked_nodes/$',
        views.SparseLinkedNodesList.as_view(),
        name=views.SparseLinkedNodesList.view_name,
    ),
    re_path(
        r'^registrations/(?P<node_id>\w+)/linked_registrations/$',
        views.SparseLinkedRegistrationsList.as_view(),
        name=views.SparseLinkedRegistrationsList.view_name,
    ),

    re_path(
        r'^users/(?P<user_id>\w+)/nodes/$',
        views.SparseUserNodeList.as_view(),
        name=views.SparseUserNodeList.view_name,
    ),
    re_path(
        r'^users/(?P<user_id>\w+)/registrations/$',
        views.SparseUserRegistrationList.as_view(),
        name=views.SparseUserRegistrationList.view_name,
    ),
]
