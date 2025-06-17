from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest

from tp.libs.rpc.core.task_manager import TaskStatus, RemoteTask, RemoteTaskManager


def test_remote_task_init():
    # Test initialization
    def test_func(a, b):
        return a + b

    task = RemoteTask(test_func, (1, 2), {"c": 3})

    assert task.function == test_func
    assert task.args == (1, 2)
    assert task.kwargs == {"c": 3}
    assert task.status == TaskStatus.PENDING
    assert task.result is None
    assert task.exception is None
    assert task.traceback is None
    assert task._cancelled is False


def test_remote_task_run_success():
    # Test successful execution
    def test_func(a, b):
        return a + b

    task = RemoteTask(test_func, (1, 2), {})
    task.run()

    assert task.status == TaskStatus.DONE
    assert task.result == 3
    assert task.exception is None


def test_remote_task_run_error():
    # Test execution with error
    def test_func():
        raise ValueError("Test error")

    task = RemoteTask(test_func, (), {})
    task.run()

    assert task.status == TaskStatus.FAILED
    assert isinstance(task.exception, ValueError)
    assert "Test error" in str(task.exception)
    assert task.traceback is not None


def test_remote_task_run_cancelled():
    # Test execution when cancelled
    def test_func():
        return "result"

    task = RemoteTask(test_func, (), {})
    task._cancelled = True
    task.run()

    assert task.status == TaskStatus.CANCELED
    assert task.result is None


def test_remote_task_cancel():
    # Test cancellation
    task = RemoteTask(lambda: None, (), {})

    # Cancel when pending
    assert task.cancel() is True
    assert task._cancelled is True

    # Change status and try to cancel again
    task._cancelled = False
    task.status = TaskStatus.RUNNING
    assert task.cancel() is False
    assert task._cancelled is False


def test_task_manager_init():
    # Test initialization
    manager = RemoteTaskManager()

    assert isinstance(manager._tasks, dict)
    assert len(manager._tasks) == 0
    assert isinstance(manager._lock, threading.Lock)


def test_task_manager_submit():
    # Test task submission
    def test_func():
        time.sleep(0.1)
        return "result"

    manager = RemoteTaskManager()

    # Mock the thread to avoid actual execution
    with patch("threading.Thread") as mock_thread:
        task_id = manager.submit(test_func)

        assert isinstance(task_id, str)
        assert task_id in manager._tasks
        assert manager._tasks[task_id].function == test_func
        mock_thread.assert_called_once()


def test_task_manager_execute():
    # Test task execution
    def test_func():
        return "result"

    manager = RemoteTaskManager()
    task = RemoteTask(test_func, (), {})

    manager._execute(task)

    assert task.status == TaskStatus.DONE
    assert task.result == "result"


def test_task_manager_get_status():
    # Test getting task status
    manager = RemoteTaskManager()

    # Create a task
    def test_func():
        return "result"

    task_id = manager.submit(test_func)

    # Test with existing task
    assert manager.get_status(task_id) == TaskStatus.PENDING

    # Test with non-existent task
    assert manager.get_status("non-existent") == "unknown"


def test_task_manager_get_result():
    # Test getting task result
    manager = RemoteTaskManager()

    # Create a completed task
    task = RemoteTask(lambda: "result", (), {})
    task.status = TaskStatus.DONE
    task.result = "result"
    manager._tasks[task.id] = task

    # Test with completed task
    assert manager.get_result(task.id) == "result"

    # Test with failed task
    failed_task = RemoteTask(lambda: None, (), {})
    failed_task.status = TaskStatus.FAILED
    failed_task.exception = ValueError("Test error")
    manager._tasks[failed_task.id] = failed_task

    with pytest.raises(ValueError, match="Test error"):
        manager.get_result(failed_task.id)

    # Test with pending task
    pending_task = RemoteTask(lambda: None, (), {})
    manager._tasks[pending_task.id] = pending_task

    with pytest.raises(RuntimeError, match="not completed yet"):
        manager.get_result(pending_task.id)

    # Test with non-existent task
    with pytest.raises(ValueError, match="not found"):
        manager.get_result("non-existent")


def test_task_manager_cancel():
    # Test task cancellation
    manager = RemoteTaskManager()

    # Create a task
    task = RemoteTask(lambda: None, (), {})
    manager._tasks[task.id] = task

    # Test cancelling existing task
    assert manager.cancel(task.id) is True

    # Test cancelling non-existent task
    assert manager.cancel("non-existent") is False


def test_task_manager_list_tasks():
    """Test listing tasks."""
    manager = RemoteTaskManager()

    # Create some tasks
    def test_func1():
        return "result1"

    def test_func2():
        return "result2"

    task1 = RemoteTask(test_func1, (), {})
    task2 = RemoteTask(test_func2, (), {})

    manager._tasks[task1.id] = task1
    manager._tasks[task2.id] = task2

    # List tasks
    tasks = manager.list_tasks()

    assert len(tasks) == 2

    # Check task details
    task1_info = next(t for t in tasks if t["function"] == "test_func1")
    task2_info = next(t for t in tasks if t["function"] == "test_func2")

    assert task1_info["id"] == task1.id
    assert task1_info["status"] == TaskStatus.PENDING

    assert task2_info["id"] == task2.id
    assert task2_info["status"] == TaskStatus.PENDING
