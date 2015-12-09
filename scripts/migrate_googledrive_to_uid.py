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


def update_node(current_node, gdrive_filenodes):
    if current_node is None:
        return


    node_settings = GoogleDriveNodeSettings.find_one(Q('owner', 'eq', current_node))
    access_token = node_settings.fetch_access_token()

    logger.info(u'--Node: {}  (token:{})'.format(current_node, access_token))

    merp = map(lambda x: [regex.sub('', x.path), x.path], gdrive_filenodes)
    ordered = sorted(list(merp), key=lambda x: x[0])
    for filenode_root, filenodes in groupby(ordered, lambda x: x[0]):
        logger.info(u'  --Root: {}'.format(filenode_root))
        for filenode in sorted(filenodes, key=lambda x: x[1]):
            logger.info(u'    --File: {}'.format(filenode))


if __name__ == '__main__':
    scripts_utils.add_file_logger(logger, __file__)
    init_app(set_backends=True, routes=False)
    main()
