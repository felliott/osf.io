# -*- coding: utf-8 -*-
import logging
from rest_framework import status as http_status

from django.utils import timezone
from django.core.exceptions import ValidationError
from flask import request
# from json import decode_json

from framework import sentry
from framework.auth import utils as auth_utils
from framework.auth import cas
from framework.auth import logout as osf_logout
from framework.auth.decorators import collect_auth
from framework.auth.decorators import must_be_logged_in
from framework.auth.decorators import must_be_confirmed
from framework.exceptions import HTTPError, PermissionsError
from framework.flask import redirect  # VOL-aware redirect
from framework.status import push_status_message
from framework.utils import throttle_period_expired

from osf import features
from osf.exceptions import BlockedEmailError
from osf.utils.requests import string_type_request_headers
from website import settings
from website import language
from website.profile import utils as profile_utils
from website.util import api_v2_url, web_url_for, paths
from website.util.sanitize import escape_html


logger = logging.getLogger(__name__)

def log_pageview():
    """Update the logged-in user's profile."""

    data = request.get_json()
    logger.info('@@Logging a pageview: {}')
    logger.info(data)

    return {}
