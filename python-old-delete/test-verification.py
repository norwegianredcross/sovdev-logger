#!/usr/bin/env python3
"""
Simple verification test to capture console and file output.
"""

from sovdev_logger import (
    sovdev_initialize,
    sovdev_log,
    sovdev_flush,
    sovdev_generate_trace_id,
    SOVDEV_LOGLEVELS,
    create_peer_services
)

# Define peer services
PEER_SERVICES = create_peer_services({
    'TEST_SERVICE': 'SYS1234567'
})

def main():
    FUNCTIONNAME = 'main'

    # Initialize logger
    sovdev_initialize(
        'verification-test-service',
        '1.0.0',
        PEER_SERVICES.mappings
    )

    # Generate trace ID for this test
    trace_id = sovdev_generate_trace_id()

    # Test 1: Simple INFO log with input
    input_data = {'test_param': 'test_value'}
    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Test log message',
        PEER_SERVICES.TEST_SERVICE,
        input_json=input_data,
        trace_id=trace_id
    )

    # Test 2: INFO log with input and response
    response_data = {'result': 'success', 'status_code': 200}
    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Test log with response',
        PEER_SERVICES.TEST_SERVICE,
        input_json=input_data,
        response_json=response_data,
        trace_id=trace_id
    )

    # Test 3: ERROR log with exception
    try:
        raise ValueError('Test exception message')
    except Exception as e:
        sovdev_log(
            SOVDEV_LOGLEVELS.ERROR,
            FUNCTIONNAME,
            'Test error log',
            PEER_SERVICES.TEST_SERVICE,
            input_json=input_data,
            exception_object=e,
            trace_id=trace_id
        )

    # Flush logs
    sovdev_flush()

if __name__ == '__main__':
    main()
