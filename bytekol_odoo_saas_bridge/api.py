import random
import string

import json
import logging
import traceback
from functools import wraps

import requests

import odoo
from odoo.exceptions import UserError
from odoo.http import request, Response as OdooResponse
_logger = logging.getLogger(__name__)


class TokenException(Exception):
    pass


def random_str(size=7, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def bk_api(purpose='api_general', log_traceback=True, custom_response=False, token_on='header', **api_kwargs):
    """ Make a route, (required database) to api, type of route should be 'http' to format data
    :param str purpose: purpose of token for check
    :param bool log_traceback: log traceback when Internal Server Error.
    :param str token_on: where to get token ['header', 'url_params']
    :param bool custom_response: return origin response on success
           bool one_time_token: delete token on verify success
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            assert token_on in ['header', 'url_params']

            response = OdooResponse(headers=[('Content-Type', 'application/json')], status=200)
            response_data = {
                'success': True
            }

            def _update_response_error(msg):
                response_data.update({
                    'success': False,
                    'error': msg
                })

            try:
                token = request.httprequest.headers.get('X-Authorization-Token')
                if token_on == 'url_params':
                    token = kwargs.get('token')

                bk_token = request.env['bk.token'].sudo().ensure_token_valid(token, purpose)
                request.update_env(user=bk_token.user_id.id)
                if api_kwargs.get('one_time_token'):
                    bk_token.sudo().unlink()

                json_data = request.httprequest.get_json() or {}
                kwargs.update(json_data)

                res = func(*args, **kwargs)
                if custom_response:
                    return res
                response_data['data'] = res
            except TokenException:
                _logger.error(traceback.format_exc())
                _update_response_error('Token Invalid (X-Authorization-Token).')
            except UserError as e:  # include ValidationError, CacheMiss, ...
                _update_response_error(str(e))
                response.status = 400
            except Exception as e:
                traceback_txt = traceback.format_exc()
                _logger.error(f'Error: {e}\n {traceback_txt}')

                msg_error = 'Internal Server Error.'
                if log_traceback:
                    traceback_code = random_str()
                    request.env['bk.traceback.log'].sudo().create({
                        'name': 'Api Error',
                        'traceback': traceback_txt,
                        'code': traceback_code,
                        'user_trigger_id': request.uid
                    })
                    msg_error += f' (Traceback code: {traceback_code})'

                _update_response_error(msg_error)
                response.status = 500

            response.data = json.dumps(response_data)
            return response

        return wrapper

    return decorator


def verify_request_from_server(server_base_url, token_on='header'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if any([ignore_host in server_base_url for ignore_host in ('localhost', '127.0.0.1', '0.0.0.0')]):
                _logger.warning(f'ignore verify_request_from_server with host: {server_base_url}')
                return func(*args, **kwargs)

            token = request.httprequest.headers.get('X-Authorization-Token')
            if token_on == 'url_params':
                token = kwargs.get('token')

            res = requests.post(server_base_url + '/verify_request', headers={
                'X-Authorization-Token': token
            }, verify=False)
            if not res.json().get('success'):
                return json.dumps({
                    'error': 'verify request failed.'
                })
            return func(*args, **kwargs)
        return wrapper
    return decorator


def verify_admin_password(func):
    """ Auto verify admin_passwd on a route.
        To call an api on route with verify_admin_password,
        it is required to enter the admin_passwd header in the request
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        admin_passwd = request.httprequest.headers.get('X-Admin-Passwd')
        passwd_valid = odoo.tools.config.verify_admin_password(admin_passwd)
        if not passwd_valid:
            response = OdooResponse(headers=[('Content-Type', 'application/json')], status=403)
            response.data = json.dumps({'error': 'admin_password invalid'})

        return func(*args, **kwargs)
    return wrapper
