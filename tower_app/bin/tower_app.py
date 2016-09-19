#!/usr/bin/env python

# Python
import base64
import collections
import json
import os
import urllib
import urlparse

# Requests
import requests

# Splunk SDK
from splunklib.modularinput import *


class InputState(collections.MutableMapping):
    """
    Dictionary-like object to persist state for a given Splunk input.
    """

    def __init__(self, metadata, input_name):
        self._filename = os.path.join(
            metadata.get('checkpoint_dir', ''),
            '{}.json'.format(base64.urlsafe_b64encode(input_name)),
        )

    def _load(self):
        if os.path.exists(self._filename):
            return json.loads(open(self._filename, 'r').read() or '{}')
        return {}

    def _store(self, data):
        json.dump(data, open(self._filename, 'w'))

    def __iter__(self):
        return iter(self._load())
    
    def __len__(self):
        return len(self._load())

    def __getitem__(self, key):
        return self._load()[key]
    
    def __setitem__(self, key, value):
        data = self._load()
        data[key] = value
        self._store(data)

    def __delitem__(self, key):
        data = self._load()
        del data[key]
        self._store(data)


class TowerAppScript(Script):

    def get_scheme(self):
        scheme = Scheme('Tower app')
        scheme.description = 'Streams events from Ansible Tower'
        scheme.use_external_validation = True
        scheme.use_single_instance = True

        tower_host_argument = Argument('tower_host')
        tower_host_argument.title = 'Tower Host'
        tower_host_argument.data_type = Argument.data_type_string
        tower_host_argument.description = 'Host (and optional port) of Tower server.'
        tower_host_argument.required_on_create = True
        scheme.add_argument(tower_host_argument)

        verify_ssl_argument = Argument('verify_ssl')
        verify_ssl_argument.title = 'Verify SSL?'
        verify_ssl_argument.data_type = Argument.data_type_boolean
        verify_ssl_argument.description = 'Verify SSL cert on Tower server.'
        scheme.add_argument(verify_ssl_argument)

        username_argument = Argument('username')
        username_argument.title = 'Username'
        username_argument.data_type = Argument.data_type_string
        username_argument.description = 'Username to access Tower server.'
        username_argument.required_on_create = True
        scheme.add_argument(username_argument)

        password_argument = Argument('password')
        password_argument.title = 'Password'
        password_argument.data_type = Argument.data_type_string
        password_argument.description = 'Password to access Tower server.'
        password_argument.required_on_create = True
        scheme.add_argument(password_argument)

        event_type_argument = Argument('event_type')
        event_type_argument.title = 'Event Type'
        event_type_argument.data_type = Argument.data_type_string
        event_type_argument.description = 'Type of event to receive from the server (job_event, activity_stream).'
        scheme.add_argument(event_type_argument)

        extra_query_params_argument = Argument('extra_query_params')
        extra_query_params_argument.title = 'Extra Query Params'
        extra_query_params_argument.data_type = Argument.data_type_string
        extra_query_params_argument.description = 'Additional url-encoded parameters to pass to the API endpoint.'
        scheme.add_argument(extra_query_params_argument)

        log_level_argument = Argument('log_level')
        log_level_argument.title = 'Log Level'
        log_level_argument.data_type = Argument.data_type_string
        log_level_argument.description = 'Level of logging by this modular input (debug, info, warning, error).'
        scheme.add_argument(log_level_argument)

        return scheme

    def _get_session(self, params):
        session = requests.session()
        session.auth = (params['username'], params['password'])
        session.verify = bool(False and params['verify_ssl'])
        return session

    def validate_input(self, validation_definition):
        event_type = validation_definition.parameters.get('event_type', '')
        if event_type not in {'job_events', 'activity_stream'}:
            raise ValueError('Unsupported event type: {}'.format(event_type))
        extra_query_params = validation_definition.parameters.get('extra_query_params', '')
        # FIXME: Validate!
        log_level = validation_definition.parameters.get('log_level', 'WARNING')
        if log_level.upper() not in {'DEBUG', 'INFO', 'WARNING', 'ERROR'}:
            raise ValueError('Invalid log level: {}'.format(log_level))
        session = self._get_session(validation_definition.parameters)
        tower_host = validation_definition.parameters['tower_host']
        url = urlparse.urlunsplit(['https', tower_host, '/api/v1/config/', '', ''])
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        if not 'version' in data:
            raise ValueError('Does not appear to be a Tower server')

    def stream_tower_events(self, input_name, input_params, input_state, ew):
        session = self._get_session(input_params)
        tower_host = input_params['tower_host']
        event_type = input_params.get('event_type', 'job_events')
        extra_query_params = input_params.get('extra_query_params', '')
        log_level = input_params.get('log_level', 'WARNING')
        last_id_key = '{}_last_id'.format(event_type)
        last_id = input_state.get(last_id_key, 0)

        while True:
            qs = urllib.urlencode(dict(order_by='id', id__gt=last_id))
            # FIXME: Include extra_query_params
            url = urlparse.urlunsplit(['https', tower_host, '/api/v1/{}/'.format(event_type), qs, ''])
            response = session.get(url)
            if log_level.upper() in {'DEBUG'}:
                ew.log(ew.DEBUG, '[{}] GET {} -> {}'.format(input_name, url, response.status_code))
            response.raise_for_status()
            data = response.json()
            if not data.get('results', []):
                break
            for result in data.get('results', []):
                event = Event()
                event.stanza = input_name
                event.data = json.dumps(result)
                ew.write_event(event)
                last_id = max(last_id, result.get('id', 0))
            input_state[last_id_key] = last_id

    def stream_events(self, inputs, ew):
        for input_name, input_params in inputs.inputs.iteritems():
            try:
                input_state = InputState(inputs.metadata, input_name)
                self.stream_tower_events(input_name, input_params, input_state, ew)
            except Exception as e:
                ew.log(ew.ERROR, '[{}] Error streaming events: {}'.format(input_name, e))


if __name__ == '__main__':
    import sys
    sys.exit(TowerAppScript().run(sys.argv))
