from furl import furl
import responses
import datetime
import json
from django.utils import timezone
import pytest

from framework.auth.core import Auth

from api.base.settings.defaults import API_BASE
from tests.base import ApiTestCase
from osf_tests.factories import (
    AuthUserFactory,
    PrivateLinkFactory,
    DraftRegistrationFactory,
)
from addons.github.models import GithubFolder
from addons.github.tests.factories import GitHubAccountFactory
from api.base.utils import waterbutler_api_url_for
from api_tests import utils as api_utils
from website import settings


class TestDraftNodeProvidersList(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = AuthUserFactory()
        self.draft_reg = DraftRegistrationFactory(creator=self.user)
        self.draft_node = self.draft_reg.branched_from
        self.url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/'

        self.user_two = AuthUserFactory()
        self.draft_reg.add_contributor(self.user_two)
        self.draft_reg.save()

        self.user_three = AuthUserFactory()

    def test_draft_node_files(self):
        # Unauthenticated
        res = self.app.get(self.url, expect_errors=True)
        assert res.status_code == 401

        # Noncontrib
        res = self.app.get(self.url, auth=self.user_three.auth, expect_errors=True)
        assert res.status_code == 403

        # Write contributor on draft
        res = self.app.get(self.url, auth=self.user_two.auth)
        assert res.status_code == 200

        # Admin contrib on draft
        res = self.app.get(self.url, auth=self.user.auth)
        assert res.status_code == 200

    def test_deleted_draft_node_files(self):
        self.draft_node.is_deleted = True
        self.draft_node.save()

        # Admin contrib
        res = self.app.get(self.url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == 410

    def test_returns_provider_data(self):
        res = self.app.get(self.url, auth=self.user.auth)
        assert res.status_code == 200
        assert isinstance(res.json['data'], list)
        assert res.content_type == 'application/vnd.api+json'
        data = res.json['data'][0]
        assert data['attributes']['kind'] == 'folder'
        assert data['attributes']['name'] == 'osfstorage'
        assert data['attributes']['provider'] == 'osfstorage'
        assert data['attributes']['node'] == self.draft_node._id
        assert data['attributes']['path'] == '/'
        assert (
            data['relationships']['target']['links']['related']['href'] ==
            f'{settings.API_DOMAIN}v2/draft_nodes/{self.draft_node._id}/'
        )

    def test_returns_osfstorage_folder_version_two(self):
        res = self.app.get(f'{self.url}osfstorage/', auth=self.user.auth)
        assert res.status_code == 200

    def test_returns_osf_storage_folder_version_two_point_two(self):
        res = self.app.get(f'{self.url}osfstorage/?version=2.2', auth=self.user.auth)
        assert res.status_code == 200


def prepare_mock_wb_response(
        node=None,
        provider='github',
        files=None,
        folder=True,
        path='/',
        method=responses.GET,
        status_code=200,
        view_only=None):
    """Prepare a mock Waterbutler response with responses library.

    :param Node node: Target node.
    :param str provider: Addon provider
    :param list files: Optional list of files. You can specify partial data; missing values
        will have defaults.
    :param folder: True if mocking out a folder response, False if a file response.
    :param path: Waterbutler path, passed to waterbutler_api_url_for.
    :param str method: HTTP method.
    :param int status_code: HTTP status.
    """
    node = node
    files = files or []
    wb_url = waterbutler_api_url_for(node._id, provider=provider, _internal=True, path=path, meta=True, view_only=view_only, base_url=node.osfstorage_region.waterbutler_url)

    default_file = {
        'contentType': None,
        'extra': {'downloads': 0, 'version': 1},
        'kind': 'file',
        'modified': None,
        'name': 'NewFile',
        'path': '/NewFile',
        'provider': provider,
        'size': None,
        'materialized': '/',
    }

    if len(files):
        data = [dict(default_file, **each) for each in files]
    else:
        data = [default_file]

    jsonapi_data = []
    for datum in data:
        jsonapi_data.append({'attributes': datum})

    if not folder:
        jsonapi_data = jsonapi_data[0]

    responses.add(
        responses.Response(
            method=method,
            url=wb_url,
            json={'data': jsonapi_data},
            status=status_code,
            content_type='application/json'
        )
    )


class TestNodeFilesList(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.user = AuthUserFactory()
        self.draft_reg = DraftRegistrationFactory(creator=self.user)
        self.draft_node = self.draft_reg.branched_from
        self.private_url = '/{}draft_nodes/{}/files/'.format(
            API_BASE, self.draft_node._id)

        self.user_two = AuthUserFactory()

    def add_github(self):
        user_auth = Auth(self.user)
        self.draft_node.add_addon('github', auth=user_auth)
        addon = self.draft_node.get_addon('github')
        addon.repo = 'something'
        addon.user = 'someone'
        oauth_settings = GitHubAccountFactory()
        oauth_settings.save()
        self.user.add_addon('github')
        self.user.external_accounts.add(oauth_settings)
        self.user.save()
        addon.user_settings = self.user.get_addon('github')
        addon.external_account = oauth_settings
        addon.save()
        self.draft_node.save()
        addon.user_settings.oauth_grants[self.draft_node._id] = {
            oauth_settings._id: []}
        addon.user_settings.save()

    def view_only_link(self):
        private_link = PrivateLinkFactory(creator=self.user)
        private_link.nodes.add(self.draft_node)
        private_link.save()
        return private_link

    def _prepare_mock_wb_response(self, node=None, **kwargs):
        prepare_mock_wb_response(node=node or self.draft_node, **kwargs)

    def test_returns_storage_addons_link(self):
        res = self.app.get(self.private_url, auth=self.user.auth)
        assert 'storage_addons' in res.json['data'][0]['links']

    def test_returns_file_data(self):
        fobj = self.draft_node.get_addon(
            'osfstorage').get_root().append_file('NewFile')
        fobj.save()
        res = self.app.get(
            f'{self.private_url}osfstorage/{fobj._id}', auth=self.user.auth)
        assert res.status_code == 200
        assert isinstance(res.json['data'], dict)
        assert res.content_type == 'application/vnd.api+json'
        assert res.json['data']['attributes']['kind'] == 'file'
        assert res.json['data']['attributes']['name'] == 'NewFile'

    def test_returns_osfstorage_folder_version_two(self):
        fobj = self.draft_node.get_addon(
            'osfstorage').get_root().append_folder('NewFolder')
        fobj.save()
        res = self.app.get(
            f'{self.private_url}osfstorage/', auth=self.user.auth)
        assert res.status_code == 200

    def test_returns_osf_storage_folder_version_two_point_two(self):
        fobj = self.draft_node.get_addon(
            'osfstorage').get_root().append_folder('NewFolder')
        fobj.save()
        res = self.app.get(
            f'{self.private_url}osfstorage/?version=2.2', auth=self.user.auth)
        assert res.status_code == 200

    def test_list_returns_folder_data(self):
        fobj = self.draft_node.get_addon(
            'osfstorage').get_root().append_folder('NewFolder')
        fobj.save()
        res = self.app.get(
            f'{self.private_url}osfstorage/', auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 1
        assert res.content_type == 'application/vnd.api+json'
        assert res.json['data'][0]['attributes']['name'] == 'NewFolder'

    def test_returns_folder_data(self):
        fobj = self.draft_node.get_addon(
            'osfstorage').get_root().append_folder('NewFolder')
        fobj.save()
        res = self.app.get(
            f'{self.private_url}osfstorage/{fobj._id}/', auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 0
        assert res.content_type == 'application/vnd.api+json'

    def test_returns_private_files_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        assert res.status_code == 401
        assert 'detail' in res.json['errors'][0]

    def test_returns_private_files_logged_in_contributor(self):
        res = self.app.get(self.private_url, auth=self.user.auth)
        assert res.status_code == 200
        assert res.content_type == 'application/vnd.api+json'
        assert len(res.json['data']) == 1
        assert res.json['data'][0]['attributes']['provider'] == 'osfstorage'

    def test_returns_private_files_logged_in_non_contributor(self):
        res = self.app.get(
            self.private_url,
            auth=self.user_two.auth,
            expect_errors=True)
        assert res.status_code == 403
        assert 'detail' in res.json['errors'][0]

    def test_returns_addon_folders(self):
        user_auth = Auth(self.user)
        res = self.app.get(self.private_url, auth=self.user.auth)
        assert len(res.json['data']) == 1
        assert res.json['data'][0]['attributes']['provider'] == 'osfstorage'

        self.draft_node.add_addon('github', auth=user_auth)
        addon = self.draft_node.get_addon('github')
        addon.repo = 'something'
        addon.user = 'someone'
        oauth_settings = GitHubAccountFactory()
        oauth_settings.save()
        self.user.add_addon('github')
        self.user.external_accounts.add(oauth_settings)
        self.user.save()
        addon.user_settings = self.user.get_addon('github')
        addon.external_account = oauth_settings
        addon.save()
        self.draft_node.save()
        addon.user_settings.oauth_grants[self.draft_node._id] = {
            oauth_settings._id: []}
        addon.user_settings.save()
        res = self.app.get(self.private_url, auth=self.user.auth)
        data = res.json['data']
        providers = [item['attributes']['provider'] for item in data]
        assert len(data) == 2
        assert 'github' in providers
        assert 'osfstorage' in providers

    @responses.activate
    def test_vol_node_files_list(self):
        vol = self.view_only_link()
        self._prepare_mock_wb_response(
            provider='github', files=[{'name': 'NewFile'}], view_only=vol.key)
        self.add_github()
        url = '/{}draft_nodes/{}/files/github/?view_only={}'.format(
            API_BASE, self.draft_node._id, vol.key)
        res = self.app.get(url, auth=self.user_two.auth)
        wb_request = responses.calls[-1].request
        url = furl(wb_request.url)

        assert url.query == f'meta=True&view_only={vol.key}'
        assert res.json['data'][0]['attributes']['name'] == 'NewFile'
        assert res.json['data'][0]['attributes']['provider'] == 'github'
        assert vol.key in res.json['data'][0]['links']['info']
        assert vol.key in res.json['data'][0]['links']['move']
        assert vol.key in res.json['data'][0]['links']['upload']
        assert vol.key in res.json['data'][0]['links']['download']
        assert vol.key in res.json['data'][0]['links']['delete']

    @responses.activate
    def test_returns_node_files_list(self):
        self._prepare_mock_wb_response(
            provider='github', files=[{'name': 'NewFile'}])
        self.add_github()
        url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/github/'

        # test create
        res = self.app.get(url, auth=self.user.auth)
        assert res.json['data'][0]['attributes']['name'] == 'NewFile'
        assert res.json['data'][0]['attributes']['provider'] == 'github'

        # test get
        res = self.app.get(url, auth=self.user.auth)
        assert res.json['data'][0]['attributes']['name'] == 'NewFile'
        assert res.json['data'][0]['attributes']['provider'] == 'github'

    @responses.activate
    def test_returns_folder_metadata_not_children(self):
        folder = GithubFolder(
            name='Folder',
            target=self.draft_node,
            path='/Folder/'
        )
        folder.save()
        self._prepare_mock_wb_response(provider='github', files=[{'name': 'Folder'}], path='/Folder/')
        self.add_github()
        url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/github/Folder/'
        res = self.app.get(url, params={'info': ''}, auth=self.user.auth)

        assert res.status_code == 200
        assert res.json['data'][0]['attributes']['kind'] == 'folder'
        assert res.json['data'][0]['attributes']['name'] == 'Folder'
        assert res.json['data'][0]['attributes']['provider'] == 'github'

    @responses.activate
    def test_returns_node_file(self):
        self._prepare_mock_wb_response(
            provider='github', files=[{'name': 'NewFile'}],
            folder=False, path='/file')
        self.add_github()
        url = '/{}draft_nodes/{}/files/github/file'.format(
            API_BASE, self.draft_node._id)
        res = self.app.get(url, auth=self.user.auth, headers={
            'COOKIE': 'foo=bar;'  # Webtests doesnt support cookies?
        })
        # test create
        assert res.status_code == 200
        assert res.json['data']['attributes']['name'] == 'NewFile'
        assert res.json['data']['attributes']['provider'] == 'github'

        # test get
        assert res.status_code == 200
        assert res.json['data']['attributes']['name'] == 'NewFile'
        assert res.json['data']['attributes']['provider'] == 'github'

    @responses.activate
    def test_notfound_node_file_returns_folder(self):
        self._prepare_mock_wb_response(
            provider='github', files=[{'name': 'NewFile'}],
            path='/file')
        url = '/{}draft_nodes/{}/files/github/file'.format(
            API_BASE, self.draft_node._id)
        res = self.app.get(
            url, auth=self.user.auth,
            expect_errors=True,
            headers={'COOKIE': 'foo=bar;'}  # Webtests doesnt support cookies?
        )
        assert res.status_code == 404

    # This test is skipped because it was wrongly configured in the first place
    # The reason OSF returns a 404 is not because WB returns a file when OSF expects a folder
    # But because the addon itself is not configured for the node
    @pytest.mark.skip('TODO: ENG-7256')
    @responses.activate
    def test_notfound_node_folder_returns_file(self):
        self._prepare_mock_wb_response(
            provider='github', files=[{'name': 'NewFile'}],
            folder=False, path='/')

        url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/github/'
        res = self.app.get(
            url, auth=self.user.auth,
            expect_errors=True,
            headers={'COOKIE': 'foo=bar;'}  # Webtests doesnt support cookies?
        )
        assert res.status_code == 404

    @responses.activate
    def test_waterbutler_server_error_returns_503(self):
        self._prepare_mock_wb_response(status_code=500)
        self.add_github()
        url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/github/'
        res = self.app.get(
            url, auth=self.user.auth,
            expect_errors=True,
            headers={'COOKIE': 'foo=bar;'}  # Webtests doesnt support cookies?
        )
        assert res.status_code == 503

    @responses.activate
    def test_waterbutler_invalid_data_returns_503(self):
        # TODO: ENG-7256 -if WB returns 400, we should return 503
        # However because of the change in get_file_object(), we can't distinguish
        # between a 400 that's caused by an addon not found and a more general 400 meaning invalid data was passed
        # We should handle this more gracefully
        wb_url = waterbutler_api_url_for(self.draft_node._id, _internal=True, provider='github', path='/', meta=True, base_url=self.draft_node.osfstorage_region.waterbutler_url)
        self.add_github()
        responses.add(
            responses.Response(
                responses.GET,
                wb_url,
                body=json.dumps({}),
                status=400
            )
        )
        url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/github/'
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == 404

    @responses.activate
    def test_handles_unauthenticated_waterbutler_request(self):
        self._prepare_mock_wb_response(status_code=401)
        self.add_github()
        url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/github/'
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == 403
        assert 'detail' in res.json['errors'][0]

    @responses.activate
    def test_handles_notfound_waterbutler_request(self):
        invalid_provider = 'gilkjadsflhub'
        self._prepare_mock_wb_response(
            status_code=404, provider=invalid_provider)
        url = '/{}draft_nodes/{}/files/{}/'.format(API_BASE,
                                             self.draft_node._id, invalid_provider)
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == 404
        assert 'detail' in res.json['errors'][0]

    @responses.activate
    def test_handles_request_to_provider_not_configured_on_project(self):
        self._prepare_mock_wb_response(
            provider='box', status_code=400,
        )
        provider = 'box'
        url = '/{}draft_nodes/{}/files/{}/'.format(
            API_BASE, self.draft_node._id, provider)
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert not self.draft_node.get_addon(provider)
        assert res.status_code == 404
        # TODO: ENG-7256 Handle this case more gracefully
        # assert res.json['errors'][0]['detail'] == f'The {provider} provider is not configured for this project.'

    @responses.activate
    def test_handles_bad_waterbutler_request(self):
        wb_url = waterbutler_api_url_for(self.draft_node._id, _internal=True, provider='github', path='/', meta=True, base_url=self.draft_node.osfstorage_region.waterbutler_url)
        responses.add(
            responses.Response(
                responses.GET,
                wb_url,
                json={'bad': 'json'},
                status=418
            )
        )
        self.add_github()
        url = f'/{API_BASE}draft_nodes/{self.draft_node._id}/files/github/'
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == 503
        assert 'detail' in res.json['errors'][0]

    def test_files_list_contains_relationships_object(self):
        res = self.app.get(self.private_url, auth=self.user.auth)
        assert res.status_code == 200
        assert 'relationships' in res.json['data'][0]


class TestNodeFilesListFiltering(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.user = AuthUserFactory()
        self.draft_reg = DraftRegistrationFactory(creator=self.user)
        self.draft_node = self.draft_reg.branched_from
        # Prep HTTP mocks
        prepare_mock_wb_response(
            node=self.draft_node, provider='github',
            files=[
                {'name': 'abc', 'path': '/abc/', 'materialized': '/abc/', 'kind': 'folder'},
                {'name': 'xyz', 'path': '/xyz', 'materialized': '/xyz', 'kind': 'file'},
            ]
        )

    def add_github(self):
        user_auth = Auth(self.user)
        self.draft_node.add_addon('github', auth=user_auth)
        addon = self.draft_node.get_addon('github')
        addon.repo = 'something'
        addon.user = 'someone'
        oauth_settings = GitHubAccountFactory()
        oauth_settings.save()
        self.user.add_addon('github')
        self.user.external_accounts.add(oauth_settings)
        self.user.save()
        addon.user_settings = self.user.get_addon('github')
        addon.external_account = oauth_settings
        addon.save()
        self.draft_node.save()
        addon.user_settings.oauth_grants[self.draft_node._id] = {
            oauth_settings._id: []}
        addon.user_settings.save()

    @responses.activate
    def test_node_files_are_filterable_by_name(self):
        url = '/{}draft_nodes/{}/files/github/?filter[name]=xyz'.format(
            API_BASE, self.draft_node._id)
        self.add_github()

        # test create
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 1  # filters out 'abc'
        assert res.json['data'][0]['attributes']['name'] == 'xyz'

        # test get
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 1  # filters out 'abc'
        assert res.json['data'][0]['attributes']['name'] == 'xyz'

    @responses.activate
    def test_node_files_filter_by_name_case_insensitive(self):
        url = '/{}draft_nodes/{}/files/github/?filter[name]=XYZ'.format(
            API_BASE, self.draft_node._id)
        self.add_github()

        # test create
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        # filters out 'abc', but finds 'xyz'
        assert len(res.json['data']) == 1
        assert res.json['data'][0]['attributes']['name'] == 'xyz'

        # test get
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        # filters out 'abc', but finds 'xyz'
        assert len(res.json['data']) == 1
        assert res.json['data'][0]['attributes']['name'] == 'xyz'

    @responses.activate
    def test_node_files_are_filterable_by_path(self):
        url = '/{}draft_nodes/{}/files/github/?filter[path]=abc'.format(
            API_BASE, self.draft_node._id)
        self.add_github()

        # test create
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 1  # filters out 'xyz'
        assert res.json['data'][0]['attributes']['name'] == 'abc'

        # test get
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 1  # filters out 'xyz'
        assert res.json['data'][0]['attributes']['name'] == 'abc'

    @responses.activate
    def test_node_files_are_filterable_by_kind(self):
        url = '/{}draft_nodes/{}/files/github/?filter[kind]=folder'.format(
            API_BASE, self.draft_node._id)
        self.add_github()

        # test create
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 1  # filters out 'xyz'
        assert res.json['data'][0]['attributes']['name'] == 'abc'

        # test get
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 1  # filters out 'xyz'
        assert res.json['data'][0]['attributes']['name'] == 'abc'

    @responses.activate
    def test_node_files_external_provider_can_filter_by_last_touched(self):
        yesterday_stamp = timezone.now() - datetime.timedelta(days=1)
        self.add_github()
        url = '/{}draft_nodes/{}/files/github/?filter[last_touched][gt]={}'.format(
            API_BASE, self.draft_node._id, yesterday_stamp.isoformat())
        # test create
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 2

        # test get
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == 200
        assert len(res.json['data']) == 2

    def test_node_files_osfstorage_cannot_filter_by_last_touched(self):
        yesterday_stamp = timezone.now() - datetime.timedelta(days=1)
        self.file = api_utils.create_test_file(self.draft_node, self.user)

        url = '/{}draft_nodes/{}/files/osfstorage/?filter[last_touched][gt]={}'.format(
            API_BASE, self.draft_node._id, yesterday_stamp.isoformat())

        # test create
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == 400
        assert len(res.json['errors']) == 1

        # test get
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == 400
        assert len(res.json['errors']) == 1


class TestNodeFilesListPagination(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = AuthUserFactory()
        self.draft_reg = DraftRegistrationFactory(creator=self.user)
        self.draft_node = self.draft_reg.branched_from

    def add_github(self):
        user_auth = Auth(self.user)
        self.draft_node.add_addon('github', auth=user_auth)
        addon = self.draft_node.get_addon('github')
        addon.repo = 'something'
        addon.user = 'someone'
        oauth_settings = GitHubAccountFactory()
        oauth_settings.save()
        self.user.add_addon('github')
        self.user.external_accounts.add(oauth_settings)
        self.user.save()
        addon.user_settings = self.user.get_addon('github')
        addon.external_account = oauth_settings
        addon.save()
        self.draft_node.save()
        addon.user_settings.oauth_grants[self.draft_node._id] = {
            oauth_settings._id: []}
        addon.user_settings.save()

    def check_file_order(self, resp):
        previous_file_name = 0
        for file in resp.json['data']:
            int_file_name = int(file['attributes']['name'])
            assert int_file_name > previous_file_name, 'Files were not in order'
            previous_file_name = int_file_name

    @responses.activate
    def test_node_files_are_sorted_correctly(self):
        prepare_mock_wb_response(
            node=self.draft_node, provider='github',
            files=[
                {'name': '01', 'path': '/01/', 'materialized': '/01/', 'kind': 'folder'},
                {'name': '02', 'path': '/02', 'materialized': '/02', 'kind': 'file'},
                {'name': '03', 'path': '/03/', 'materialized': '/03/', 'kind': 'folder'},
                {'name': '04', 'path': '/04', 'materialized': '/04', 'kind': 'file'},
                {'name': '05', 'path': '/05/', 'materialized': '/05/', 'kind': 'folder'},
                {'name': '06', 'path': '/06', 'materialized': '/06', 'kind': 'file'},
                {'name': '07', 'path': '/07/', 'materialized': '/07/', 'kind': 'folder'},
                {'name': '08', 'path': '/08', 'materialized': '/08', 'kind': 'file'},
                {'name': '09', 'path': '/09/', 'materialized': '/09/', 'kind': 'folder'},
                {'name': '10', 'path': '/10', 'materialized': '/10', 'kind': 'file'},
                {'name': '11', 'path': '/11/', 'materialized': '/11/', 'kind': 'folder'},
                {'name': '12', 'path': '/12', 'materialized': '/12', 'kind': 'file'},
                {'name': '13', 'path': '/13/', 'materialized': '/13/', 'kind': 'folder'},
                {'name': '14', 'path': '/14', 'materialized': '/14', 'kind': 'file'},
                {'name': '15', 'path': '/15/', 'materialized': '/15/', 'kind': 'folder'},
                {'name': '16', 'path': '/16', 'materialized': '/16', 'kind': 'file'},
                {'name': '17', 'path': '/17/', 'materialized': '/17/', 'kind': 'folder'},
                {'name': '18', 'path': '/18', 'materialized': '/18', 'kind': 'file'},
                {'name': '19', 'path': '/19/', 'materialized': '/19/', 'kind': 'folder'},
                {'name': '20', 'path': '/20', 'materialized': '/20', 'kind': 'file'},
                {'name': '21', 'path': '/21/', 'materialized': '/21/', 'kind': 'folder'},
                {'name': '22', 'path': '/22', 'materialized': '/22', 'kind': 'file'},
                {'name': '23', 'path': '/23/', 'materialized': '/23/', 'kind': 'folder'},
                {'name': '24', 'path': '/24', 'materialized': '/24', 'kind': 'file'},
            ]
        )
        self.add_github()
        url = '/{}draft_nodes/{}/files/github/?page[size]=100'.format(
            API_BASE, self.draft_node._id)
        res = self.app.get(url, auth=self.user.auth)
        self.check_file_order(res)


class TestDraftNodeStorageProviderDetail(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.user = AuthUserFactory()
        self.draft_reg = DraftRegistrationFactory(initiator=self.user)
        self.draft_node = self.draft_reg.branched_from
        self.private_url = '/{}draft_nodes/{}/files/providers/osfstorage/'.format(
            API_BASE, self.draft_node._id)

    def test_can_view_if_contributor(self):
        res = self.app.get(self.private_url, auth=self.user.auth)
        assert res.status_code == 200
        assert res.json['data']['id'] == f'{self.draft_node._id}:osfstorage'

    def test_cannot_view_if_private(self):
        res = self.app.get(self.private_url, expect_errors=True)
        assert res.status_code == 401
