#!/usr/bin/env py.test


def test_tower_app(tower_app_script, event_writer, input_stream):
    result = tower_app_script.run_script([__file__], event_writer, input_stream)
    assert result == 0
    output_value = event_writer._out.getvalue()
    error_value = event_writer._err.getvalue()
    #print error_value
    #assert False
