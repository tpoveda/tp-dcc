import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor

from tp.libs.rpc.api.interface import launch_server, call_remote_function
from tp.libs.rpc.core.instances import cleanup_registry


@pytest.fixture
def test_server():
    """Start a test RPC server."""
    instance_name = launch_server(
        host="localhost", port=0, dcc_type="test", instance_name="load_test"
    )

    # Register test functions
    call_remote_function(
        dcc_type="test",
        instance_name="load_test",
        function_name="register_remote_function",
        name="echo",
        source_code="""
def echo(value):
    return value
        """,
    )

    call_remote_function(
        dcc_type="test",
        instance_name="load_test",
        function_name="register_remote_function",
        name="compute_intensive",
        source_code="""
import time

def compute_intensive(iterations):
    result = 0
    for i in range(iterations):
        result += i * i
    return result
        """,
    )

    yield instance_name

    # Clean up
    call_remote_function(
        dcc_type="test",
        instance_name="load_test",
        function_name="stop_rpc_server",
    )
    cleanup_registry()


def test_concurrent_calls(test_server):
    """Test many concurrent calls to the server."""
    num_calls = 100
    results = []
    errors = []

    def make_call(i):
        try:
            start_time = time.time()
            result = call_remote_function(
                dcc_type="test",
                instance_name="load_test",
                function_name="echo",
                value=f"test-{i}",
            )
            elapsed = time.time() - start_time
            results.append((result, elapsed))
            return result
        except Exception as e:
            errors.append(e)
            return None

    # Make concurrent calls
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_call, i) for i in range(num_calls)]
        for future in futures:
            future.result()  # Wait for completion

    # Check results
    assert len(results) == num_calls
    assert len(errors) == 0

    # Check that all calls returned the expected value
    for i, (result, _) in enumerate(results):
        assert result == f"test-{i}"

    # Calculate statistics
    response_times = [elapsed for _, elapsed in results]
    avg_time = sum(response_times) / len(response_times)
    max_time = max(response_times)
    min_time = min(response_times)

    # Log statistics
    print(f"Average response time: {avg_time:.3f}s")
    print(f"Min response time: {min_time:.3f}s")
    print(f"Max response time: {max_time:.3f}s")

    # No hard assertions on timing as it depends on the environment


def test_compute_intensive_task(test_server):
    """Test a compute-intensive task."""
    # Run a compute-intensive task
    start_time = time.time()
    result = call_remote_function(
        dcc_type="test",
        instance_name="load_test",
        function_name="compute_intensive",
        iterations=1000000,
    )
    elapsed = time.time() - start_time

    # Check the result
    assert isinstance(result, int)
    assert result > 0
