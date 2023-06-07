from addons.base.serializer import StorageAddonSerializer
from addons.box import settings

from website.util import api_url_for

from boxsdk import Client, OAuth2
from boxsdk.exception import BoxAPIException

class BoxSerializer(StorageAddonSerializer):

    addon_short_name = 'box'

    def credentials_are_valid(self, user_settings, client):
        from addons.box.models import Provider as Box  # Avoid circular import
        if self.node_settings.has_auth:
            if Box(self.node_settings.external_account).refresh_oauth_key():
                return True

        if user_settings:
            oauth = OAuth2(client_id=settings.BOX_KEY, client_secret=settings.BOX_SECRET, access_token=user_settings.external_accounts[0].oauth_key)
            client = client or Client(oauth)
            try:
                client.user()
            except (BoxAPIException, IndexError):
                return False
        return True

    def serialized_folder(self, node_settings):
        path = node_settings.fetch_full_folder_path()
        return {
            'path': path,
            'name': path.replace('All Files', '', 1) if path != '/' else '/ (Full Box)'
        }

    @property
    def addon_serialized_urls(self):
        node = self.node_settings.owner
        guid = node.guids.first()._id
        return {
            # 'auth': api_url_for('oauth_connect', service_name='box'),
            'auth': 'http://localhost:8011/charon/box/connect',

            # 'importAuth': node.api_url_for('box_import_auth'),
            'importAuth': 'http://localhost:8011/charon/projects/{}/box/user_auth/'.format(guid),

            # 'files': node.web_url_for('collect_file_trees'),
            'files': node.web_url_for('collect_file_trees'),

            # 'folders': node.api_url_for('box_folder_list'),
            'folders': 'http://localhost:8011/charon/projects/{}/box/folders/'.format(guid),

            # 'config': node.api_url_for('box_set_config'),
            'config': 'http://localhost:8011/charon/projects/{}/box/settings/'.format(guid),

            'deauthorize': node.api_url_for('box_deauthorize_node'),
            # 'deauthorize': 'http://localhost:8011/charon/projects/{}/box/user_auth/'.format(guid),

            # 'accounts': node.api_url_for('box_account_list'),
            'accounts': 'http://localhost:8011/charon/settings/box/accounts/',
        }
