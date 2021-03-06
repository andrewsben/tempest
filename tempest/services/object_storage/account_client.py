# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import urllib

from tempest.common import http
from tempest.common.rest_client import RestClient
from tempest import config
from tempest import exceptions

CONF = config.CONF


class AccountClient(RestClient):
    def __init__(self, auth_provider):
        super(AccountClient, self).__init__(auth_provider)
        self.service = CONF.object_storage.catalog_type
        self.format = 'json'

    def create_account(self, data=None,
                       params=None,
                       metadata={},
                       remove_metadata={},
                       metadata_prefix='X-Account-Meta-',
                       remove_metadata_prefix='X-Remove-Account-Meta-'):
        """Create an account."""
        url = ''
        if params:
            url += '?%s' % urllib.urlencode(params)

        headers = {}
        for key in metadata:
            headers[metadata_prefix + key] = metadata[key]
        for key in remove_metadata:
            headers[remove_metadata_prefix + key] = remove_metadata[key]

        resp, body = self.put(url, data, headers)
        return resp, body

    def delete_account(self, data=None, params=None):
        """Delete an account."""
        url = ''
        if params:
            if 'bulk-delete' in params:
                url += 'bulk-delete&'
            url = '?%s%s' % (url, urllib.urlencode(params))

        resp, body = self.delete(url, headers={}, body=data)
        return resp, body

    def list_account_metadata(self):
        """
        HEAD on the storage URL
        Returns all account metadata headers
        """
        resp, body = self.head('')
        return resp, body

    def create_account_metadata(self, metadata,
                                metadata_prefix='X-Account-Meta-'):
        """Creates an account metadata entry."""
        headers = {}
        for key in metadata:
            headers[metadata_prefix + key] = metadata[key]

        resp, body = self.post('', headers=headers, body=None)
        return resp, body

    def delete_account_metadata(self, metadata,
                                metadata_prefix='X-Remove-Account-Meta-'):
        """
        Deletes an account metadata entry.
        """

        headers = {}
        for item in metadata:
            headers[metadata_prefix + item] = 'x'
        resp, body = self.post('', headers=headers, body=None)
        return resp, body

    def list_account_containers(self, params=None):
        """
        GET on the (base) storage URL
        Given valid X-Auth-Token, returns a list of all containers for the
        account.

        Optional Arguments:
        limit=[integer value N]
            Limits the number of results to at most N values
            DEFAULT:  10,000

        marker=[string value X]
            Given string value X, return object names greater in value
            than the specified marker.
            DEFAULT: No Marker

        format=[string value, either 'json' or 'xml']
            Specify either json or xml to return the respective serialized
            response.
            DEFAULT:  Python-List returned in response body
        """

        if params:
            if 'format' not in params:
                params['format'] = self.format
        else:
            params = {'format': self.format}

        url = '?' + urllib.urlencode(params)
        resp, body = self.get(url)

        if params and params.get('format') == 'json':
            body = json.loads(body)
        return resp, body

    def list_extensions(self):
        self.skip_path()
        resp, body = self.get('info')
        self.reset_path()
        body = json.loads(body)
        return resp, body


class AccountClientCustomizedHeader(RestClient):

    # TODO(andreaf) This class is now redundant, to be removed in next patch

    def __init__(self, auth_provider):
        super(AccountClientCustomizedHeader, self).__init__(
            auth_provider)
        # Overwrites json-specific header encoding in RestClient
        self.service = CONF.object_storage.catalog_type
        self.format = 'json'

    def request(self, method, url, headers=None, body=None):
        """A simple HTTP request interface."""
        self.http_obj = http.ClosingHttp()
        if headers is None:
            headers = {}

        # Authorize the request
        req_url, req_headers, req_body = self.auth_provider.auth_request(
            method=method, url=url, headers=headers, body=body,
            filters=self.filters
        )
        self._log_request(method, req_url, headers, body)
        # use original body
        resp, resp_body = self.http_obj.request(req_url, method,
                                                headers=req_headers,
                                                body=req_body)
        self._log_response(resp, resp_body)

        if resp.status == 401 or resp.status == 403:
            raise exceptions.Unauthorized()

        return resp, resp_body

    def list_account_containers(self, params=None, metadata=None):
        """
        GET on the (base) storage URL
        Given a valid X-Auth-Token, returns a list of all containers for the
        account.

        Optional Arguments:
        limit=[integer value N]
            Limits the number of results to at most N values
            DEFAULT:  10,000

        marker=[string value X]
            Given string value X, return object names greater in value
            than the specified marker.
            DEFAULT: No Marker

        format=[string value, either 'json' or 'xml']
            Specify either json or xml to return the respective serialized
            response.
            DEFAULT:  Python-List returned in response body
        """

        url = '?format=%s' % self.format
        if params:
            url += '&%s' + urllib.urlencode(params)

        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        resp, body = self.get(url, headers=headers)
        return resp, body
