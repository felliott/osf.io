import pytest

from api.base.settings.defaults import API_BASE
from osf_tests.factories import (
    ProjectFactory,
    OSFGroupFactory,
    AuthUserFactory,
    NodeFactory
)
from osf.utils.permissions import READ


@pytest.fixture()
def admin_contributor():
    return AuthUserFactory()


@pytest.fixture()
def implicit_contributor():
    return AuthUserFactory(given_name='Henrique')

@pytest.fixture()
def parent(implicit_contributor):
    return ProjectFactory(
        title='Parent Project',
        creator=implicit_contributor
    )

@pytest.fixture()
def component(admin_contributor, parent):
    return NodeFactory(parent=parent, creator=admin_contributor)


@pytest.mark.django_db
class TestNodeImplicitContributors:
    def test_list_and_filter_implicit_contributors(self, app, component, admin_contributor, implicit_contributor):
        url = f'/{API_BASE}nodes/{component._id}/implicit_contributors/'
        res = app.get(url, auth=admin_contributor.auth)
        assert res.status_code == 200
        assert res.content_type == 'application/vnd.api+json'
        assert len(res.json['data']) == 1
        assert res.json['data'][0]['id'] == implicit_contributor._id

        url = f'/{API_BASE}nodes/{component._id}/implicit_contributors/?filter[given_name]={implicit_contributor.given_name}'
        res = app.get(url, auth=admin_contributor.auth)
        assert res.status_code == 200
        assert res.content_type == 'application/vnd.api+json'
        assert len(res.json['data']) == 1
        assert res.json['data'][0]['id'] == implicit_contributor._id

        url = f'/{API_BASE}nodes/{component._id}/implicit_contributors/?filter[given_name]=NOT_EVEN_A_NAME'
        res = app.get(url, auth=admin_contributor.auth)
        assert res.status_code == 200
        assert res.content_type == 'application/vnd.api+json'
        assert len(res.json['data']) == 0

        component.add_contributor(implicit_contributor, save=True)
        res = app.get(url, auth=admin_contributor.auth)
        assert res.status_code == 200
        assert res.content_type == 'application/vnd.api+json'
        assert len(res.json['data']) == 0

    def test_osf_group_members_can_view_implicit_contributors(self, app, component, admin_contributor, implicit_contributor):
        group_mem = AuthUserFactory()
        group = OSFGroupFactory(creator=group_mem)
        component.add_osf_group(group, READ)

        url = f'/{API_BASE}nodes/{component._id}/implicit_contributors/'
        res = app.get(url, auth=group_mem.auth)
        assert res.status_code == 200
        assert res.content_type == 'application/vnd.api+json'
        assert len(res.json['data']) == 1
        assert res.json['data'][0]['id'] == implicit_contributor._id
