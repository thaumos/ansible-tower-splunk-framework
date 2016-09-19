#!/usr/bin/env python

# Python
import json
import urlparse

# Requests
import requests

# Splunk SDK
from splunklib.modularinput import *

# Croniter for poll in cron
from croniter import croniter


class TowerAppScript(Script):

    def get_scheme(self):
        scheme = Scheme('Tower app')
        scheme.description = 'Streams events from Ansible Tower'
        scheme.use_external_validation = True
        scheme.use_single_instance = True
        scheme.streaming_mode = simple

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

        request_timeout_argument = Argument('request_timeout')
        request_timeout_argument.title = 'Request Timeout'
        request_timeout_argument.data_type = Argument.data_type_number
        request_timeout_argument.description = 'Request Timeout in seconds'
        request_timeout_argument.required_on_edit = False
        request_timeout_argument.required_on_create = False
        scheme.add_argument(request_timeout_argument)

        backoff_time_argument = Argument('backoff_time')
        backoff_time_argument.title = 'Backoff Time'
        backoff_time_argument.data_type = Argument.data_type_number
        backoff_time_argument.description = 'Time in seconds to wait for retry after error or timeout'
        backoff_time_argument.required_on_edit = False
        backoff_time_argument.required_on_create = False
        scheme.add_argument(backoff_time_argument)

        polling_interval_argument = Argument('polling_interval')
        polling_interval_argument.title = 'Polling Interval'
        polling_interval_argument.data_type = Argument.data_type_number
        polling_interval_argument.description = 'Interval time in seconds to poll the endpoint'
        polling_interval_argument.required_on_edit = False
        polling_interval_argument.required_on_create = False
        scheme.add_argument(polling_interval_argument)

        return scheme

    def validate_input(self, validation_definition):
        tower_host = validation_definition.parameters['tower_host']
        verify_ssl = False #validation_definition.parameters['verify_ssl']
        username = validation_definition.parameters['username']
        password = validation_definition.parameters['password']
        request_timeout = validation_definition.parameters['request_timeout']
        backoff_time = validation_definition.parameters['backoff_time']
        polling_interval = validation_definition.parameters['polling_interval']
        api_config_url = urlparse.urlunsplit(['https', tower_host, '/api/v1/config/', '', ''])
        response = requests.get(api_config_url, auth=(username, password), verify=bool(verify_ssl))
        response.raise_for_status()
        data = response.json()
        if not 'version' in data:
            raise ValueError('Does not appear to be a Tower server')

    def stream_events(self, inputs, ew):
        for input_name, input_item in inputs.inputs.iteritems():
            tower_host = input_item['tower_host']
            verify_ssl = False #input_item['verify_ssl']
            username = input_item['username']
            password = input_item['password']

# let's poll every minute here!
            request_timeout=int(config.get("request_timeout",30))

            backoff_time=int(config.get("backoff_time",10))

            sequential_stagger_time  = int(config.get("sequential_stagger_time",0))

            polling_interval_string = config.get("polling_interval","60")

            if polling_interval_string.isdigit():
                polling_type = 'interval'
                polling_interval=int(polling_interval_string)
            else:
                polling_type = 'cron'
                cron_start_date = datetime.now()
                cron_iter = croniter(polling_interval_string, cron_start_date)


            job_events_url = urlparse.urlunsplit(['https', tower_host, '/api/v1/job_events/', '', ''])

            response = requests.get(job_events_url, auth=(username, password), verify=bool(verify_ssl))
            response.raise_for_status()
            data = response.json()
            for result in data.get('results', []):
                event = Event()
                event.stanza = input_name
                event.data = json.dumps(result)
                ew.write_event(event)


if __name__ == '__main__':
    import sys
    sys.exit(TowerAppScript().run(sys.argv))
