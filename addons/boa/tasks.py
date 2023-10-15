import asyncio
import logging
from urllib import request
from urllib.error import HTTPError, URLError

from asgiref.sync import async_to_sync, sync_to_async
from boaapi.boa_client import BoaClient, BoaException
from boaapi.status import CompilerStatus, ExecutionStatus

from addons.boa import settings as boa_settings
from framework import sentry
from framework.celery_tasks import app as celery_app
from osf.models import OSFUser
from osf.utils.fields import ensure_str, ensure_bytes
from website import settings as osf_settings

logger = logging.getLogger(__name__)


@celery_app.task(name='addons.boa.tasks.submit_to_boa')
def submit_to_boa(host, username, password, user_guid, query_dataset,
                  query_file_name, query_download_url, output_upload_url):
    """
    Note:
    * All the parameters must be verified by the caller.
    * Both the ``query_download_url`` and ``output_upload_url`` must be WB URL since it generates
      fewer requests between OSF and WB and has authentication passed via the headers.
    * Running asyncio in celery is tricky. See the following link for the solution we've chosen:
      * https://stackoverflow.com/questions/39815771/how-to-combine-celery-with-asyncio
    """
    async_to_sync(submit_to_boa_async)(host, username, password, user_guid, query_dataset,
                                       query_file_name, query_download_url, output_upload_url)


async def submit_to_boa_async(host, username, password, user_guid, query_dataset,
                              query_file_name, query_download_url, output_upload_url):
    """
    Note:
    * Due to django's incompatibility issue with asyncio, must use ``sync_to_async()`` when necessary
    * See notes in ``submit_to_boa()``
    * TODO: should we add ``node_guid`` to be included in emails to users?
    """

    logger.debug('>>>>>>>> Task begins')
    user = await sync_to_async(OSFUser.objects.get)(guids___id=user_guid)
    cookie_value = (await sync_to_async(user.get_or_create_cookie)()).decode()

    logger.debug(f'Downloading Boa query file: '
                f'name=[{query_file_name}], user=[{user_guid}], url=[{query_download_url}] ...')
    download_request = request.Request(query_download_url)
    download_request.add_header('Cookie', f'{osf_settings.COOKIE_NAME}={cookie_value}')
    try:
        boa_query = ensure_str(request.urlopen(download_request).read())
    except (ValueError, HTTPError, URLError):
        message = f'Failed to download Boa query file: ' \
                  f'name=[{query_file_name}], user=[{user_guid}], url=[{query_download_url}]!'
        logger.error(message)
        sentry.log_message(message)
        sentry.log_exception()
        # TODO: send error email
        return
    logger.info('Boa query successfully downloaded.')
    logger.debug(f'Boa query:\n########\n{boa_query}\n########')

    logger.debug('Boa client opened.')
    client = BoaClient(endpoint=host)
    logger.debug(f'Checking Boa credentials: boa_username=[{username}], boa_host=[{host}] ...')
    try:
        client.login(username, password)
    except BoaException:
        message = f'Boa login failed: boa_username=[{username}], boa_host=[{host}]!'
        logger.error(message)
        sentry.log_message(message)
        sentry.log_exception()
        client.close()
        # TODO: send error email
        return
    logger.info('Boa login completed.')

    logger.debug(f'Retrieving Boa dataset: dataset=[{query_dataset}] ...')
    try:
        dataset = client.get_dataset(query_dataset)
    except BoaException:
        message = f'Failed to retrieve or verify the target Boa dataset: dataset=[{query_dataset}]!'
        logger.error(message)
        sentry.log_message(message)
        sentry.log_exception()
        client.close()
        # TODO: send error email
        return
    logger.info('Boa dataset retrieved.')

    logger.debug(f'Submitting the query to Boa API: boa_host=[{host}], dataset=[{query_dataset}] ...')
    try:
        boa_job = client.query(boa_query, dataset)
    except BoaException:
        message = f'Failed to submit the query to Boa API: : boa_host=[{host}], dataset=[{query_dataset}]!'
        logger.error(message)
        sentry.log_message(message)
        sentry.log_exception()
        client.close()
        # TODO: send error email
        return
    logger.info('Query successfully submitted.')
    logger.debug(f'Waiting for job to finish: job_id = [{str(boa_job.id)}] ...')
    while boa_job.is_running():
        logger.debug(f'Boa job still running, waiting 10s: job_id = [{str(boa_job.id)}] ...')
        boa_job.refresh()
        await asyncio.sleep(10)
    if boa_job.compiler_status is CompilerStatus.ERROR:
        message = f'Boa job failed with compile error: job_id = [{str(boa_job.id)}]!'
        logger.error(message)
        sentry.log_message(message)
        sentry.log_exception()
        client.close()
        # TODO: send error email
        return
    elif boa_job.compiler_status is ExecutionStatus.ERROR:
        message = f'Boa job failed with execution error: job_id = [{str(boa_job.id)}]!'
        logger.error(message)
        sentry.log_message(message)
        sentry.log_exception()
        client.close()
        # TODO: send error email
        return
    else:
        boa_job_output = boa_job.output()
        logger.info('Boa job finished.')
        logger.debug(f'Boa job output: job_id = [{str(boa_job.id)}]\n########\n{boa_job_output}\n########')
        client.close()
        logger.debug('Boa client closed.')

    output_file_name = query_file_name.replace('.boa', boa_settings.OUTPUT_FILE_SUFFIX)
    logger.debug(f'Uploading Boa query output to OSF: name=[{output_file_name}], upload_url=[{output_upload_url}] ...')
    try:
        # TODO: let the caller v1 view provide the base upload URL without query params (e.g. ``?kind=file``)
        upload_request = request.Request(f'{output_upload_url}&name={output_file_name}')
        upload_request.method = 'PUT'
        upload_request.data = ensure_bytes(boa_job_output)
        upload_request.add_header('Cookie', f'{osf_settings.COOKIE_NAME}={cookie_value}')
        request.urlopen(upload_request)
    except (ValueError, HTTPError, URLError):
        message = f'Failed to upload query output file to OSF: ' \
                  f'name=[{output_file_name}], user=[{user_guid}], url=[{output_upload_url}]!'
        logger.error(message)
        sentry.log_message(message)
        sentry.log_exception()
        # TODO: send error email
        return

    logger.info('Successfully uploaded query output to OSF.')
    logger.debug('Task ends <<<<<<<<')
    # TODO: send success email
    return
