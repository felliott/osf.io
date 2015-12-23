import logging
from website.app import init_app
from website.files.models.googledrive import GoogleDriveFileNode
from website.addons.googledrive.model import GoogleDriveNodeSettings
from scripts import utils as scripts_utils
from framework.transactions.context import TokuTransaction
from modularodm.query.querydialect import DefaultQueryDialect as Q
from itertools import groupby
import re
from pprint import pprint
import requests

logger = logging.getLogger(__name__)

regex = re.compile('[^/]+/?$')

def main():
    with TokuTransaction():

        current_node = None
        gdrive_filenodes = []
        for file in GoogleDriveFileNode.find().sort('node'):
            if current_node != file.node_id:
                update_node(current_node, gdrive_filenodes)
                gdrive_filenodes = []
                current_node = file.node_id

            gdrive_filenodes.append(file)

        update_node(current_node, gdrive_filenodes)


def _build_query(folder_id):
    queries = [
        "'{}' in parents".format(folder_id),
        'trashed = false',
        "mimeType != 'application/vnd.google-apps.form'",
    ]
    return ' and '.join(queries)

def update_node(current_node, gdrive_filenodes):
    if current_node is None:
        return

    node_settings = GoogleDriveNodeSettings.find_one(Q('owner', 'eq', current_node))
    access_token = node_settings.fetch_access_token()
    headers = {'authorization': 'Bearer {}'.format(access_token)}
    base_url = 'https://www.googleapis.com/drive/v2/files'

    logger.info(u'--Node: {}  (token:{})'.format(current_node, access_token))

    parent_folders = { '/': node_settings.folder_id }
    merp = map(lambda x: [regex.sub('', x.path), x.path], gdrive_filenodes)
    ordered = sorted(list(merp), key=lambda x: x[0])
    for filenode_root, filenodes in groupby(ordered, lambda x: x[0]):
        logger.info(u'  --Root: {}'.format(filenode_root))

        payload = {'alt': 'json', q=_build_query(parent_folders[filenode_root])}
        resp = requests.get(base_url, params=payload, headers=headers)

        items = resp.json())['items']
        for filenode in sorted(filenodes, key=lambda x: x[1]):
            logger.info(u'    --File: {}'.format(filenode))
            found = None
            for item in items:
                if item['title'] == filenode.name and (item['mime_type'] == 'application/vnd.google-apps.folder') == (filenode.kind == 'folder'):
                    found = item
                    break

            if filenode.kind == 'folder':
                parent_folders[filenode.path] = found.id

            filenode.path = id
            filenode.update()

            




if __name__ == '__main__':
    scripts_utils.add_file_logger(logger, __file__)
    init_app(set_backends=True, routes=False)
    main()
