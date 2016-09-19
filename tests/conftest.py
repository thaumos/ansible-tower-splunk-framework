# Python
import os
import StringIO
import subprocess
import sys

# Splunk SDK
from splunklib.modularinput.event_writer import EventWriter

# PyTest
import pytest

# Tower App
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tower_app', 'bin'))
from tower_app import TowerAppScript


@pytest.fixture(scope='session')
def tower_cli_config():
    # Use tower-cli config to get connection options.
    config = {}
    try:
        tower_cli_config = subprocess.check_output(['tower-cli', 'config'])
        for line in tower_cli_config.splitlines():
            line = line.split('#')[0].strip()
            if ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                config[key] = value
    except subprocess.CalledProcessError as e:
        sys.stderr.write('Error reading tower-cli config: {}\n'.format(e))
    return config


@pytest.fixture()
def input_stream(tower_cli_config, tmpdir):
    config = {
        'host': 'localhost',
        'verify_ssl': 'False',
        'username': 'admin',
        'password': 'admin',
    }
    config.update(tower_cli_config)
    params = {
        'tower_host': config['host'],
        'verify_ssl': 1 if config['verify_ssl'].lower() in ('true', '1') else 0,
        'username': config['username'],
        'password': config['password'],
        'event_type': 'job_events',
        'log_level': 'debug',
    }
    # Note: Doesn't escape anything that might screw up the XML.
    params_xml = '\n'.join(['<param name="{}">{}</param>'.format(k, v)
                            for k, v in params.items()])

    return StringIO.StringIO('''<?xml version="1.0" encoding="utf-8"?>
        <input xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <server_host>whatever</server_host>
            <server_uri>https://127.0.0.1:8089</server_uri>
            <checkpoint_dir>{0}</checkpoint_dir>
            <session_key>1234567890</session_key>
            <configuration>
                <stanza name="tower_app://test">
                {1}
                </stanza>
            </configuration>
        </input>'''.format(tmpdir, params_xml))


@pytest.fixture()
def output_stream():
    return StringIO.StringIO()


@pytest.fixture()
def error_stream():
    return StringIO.StringIO()


@pytest.fixture()
def event_writer(output_stream, error_stream):
    return EventWriter(output_stream, error_stream)


@pytest.fixture()
def tower_app_script():
    return TowerAppScript()
