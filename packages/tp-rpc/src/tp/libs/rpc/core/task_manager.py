from __future__ import annotations

import uuid
import enum
import threading
import traceback
from typing import Any, Optional
from collections.abc import Callable

from .events import Event, get_event_bus


class TaskStatus:
    """Enum-like container for task status values."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELED = "canceled"


class RemoteTask:
    """Represents a single remote task with execution metadata and result
    tracking.
    """

    def __init__(self, function: Callable, args: tuple, kwargs: dict):
        """Initialize a new RemoteTask.

        Args:
            function: The function to execute.
            args: Positional arguments for the function.
            kwargs: Keyword arguments for the function.
        """

        self.id = str(uuid.uuid4())
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.exception: Exception | None = None
        self.traceback: str | None = None
        self._cancelled = False
        self._progress: float = 0.0
        self._progress_message: str = ""
        self._event_bus = get_event_bus()

    def run(self):
        """Execute the task, tracking its status and capturing exceptions."""

        if self._cancelled:
            self.status = TaskStatus.CANCELED
            return

        self.status = TaskStatus.RUNNING
        try:
            # Inject progress reporting function into kwargs if not already present
            if "report_progress" not in self.kwargs:
                self.kwargs["report_progress"] = self.report_progress

            self.result = self.function(*self.args, **self.kwargs)
            self.status = TaskStatus.DONE
            # Final progress update
            self.report_progress(1.0, "Task completed")
        except Exception as e:
            self.exception = e
            self.traceback = traceback.format_exc()
            self.status = TaskStatus.FAILED
            # Report failure in progress
            self.report_progress(self._progress, f"Failed: {str(e)}")

    def cancel(self) -> bool:
        """Mark the task for cancellation if it hasn't started yet.

        Returns:
            True if successfully cancelled, False otherwise.
        """

        if self.status == TaskStatus.PENDING:
            self._cancelled = True
            return True
        return False

    def report_progress(self, progress: float, message: str = "") -> None:
        """Report the current progress of the task.

        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional message describing the current progress state
        """
        # Clamp progress between 0 and 1
        progress = max(0.0, min(1.0, progress))

        # Update internal state
        self._progress = progress
        self._progress_message = message

        # Publish progress event
        event_data = {
            "task_id": self.id,
            "progress": progress,
            "message": message,
            "function": self.function.__name__,
        }
        self._event_bus.publish(Event("task_progress", event_data))

    def get_progress(self) -> tuple[float, str]:
        """Get the current progress of the task.

        Returns:
            Tuple of (progress_value, progress_message)
        """
        return (self._progress, self._progress_message)


class RemoteTaskManager:
    """Manages remote task execution and lifecycle."""

    def __init__(self):
        """Initialize the task manager with a thread-safe task registry."""

        self._tasks: dict[str, RemoteTask] = {}
        self._lock = threading.Lock()
        self._event_bus = get_event_bus()

    def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit a new task for background execution.

        Args:
            func: The function to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Unique task ID.
        """

        task = RemoteTask(func, args, kwargs)
        self._tasks[task.id] = task

        # Publish task creation event
        self._event_bus.publish(
            Event("task_created", {"task_id": task.id, "function": func.__name__})
        )

        threading.Thread(target=self._execute, args=(task,), daemon=True).start()
        return task.id

    def _execute(self, task: RemoteTask):
        """Run a task in a thread-safe context.

        Args:
            task: The task to execute.
        """

        with self._lock:
            task.run()

        # Publish task completion event
        self._event_bus.publish(
            Event(
                "task_completed",
                {
                    "task_id": task.id,
                    "status": task.status,
                    "function": task.function.__name__,
                },
            )
        )

    def get_status(self, task_id: str) -> str:
        """Get the status of a task by ID.

        Args:
            task_id: Task identifier.

        Returns:
            Task status or 'unknown'.
        """

        task = self._tasks.get(task_id)
        return task.status if task else "unknown"

    def get_result(self, task_id: str) -> Any:
        """Retrieve the result of a completed task.

        Args:
            task_id: Task identifier.

        Returns:
            The result of the task.

        Raises:
            ValueError: If the task ID is invalid.
            RuntimeError: If the task is not completed.
            Exception: If the task raised an error.
        """

        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID '{task_id}' not found")
        if task.status == TaskStatus.DONE:
            return task.result
        elif task.status == TaskStatus.FAILED:
            raise task.exception
        else:
            raise RuntimeError(f"Task '{task_id}' not completed yet")

    def get_progress(self, task_id: str) -> tuple[float, str]:
        """Get the current progress of a task.

        Args:
            task_id: Task identifier.

        Returns:
            Tuple of (progress_value, progress_message)

        Raises:
            ValueError: If the task ID is invalid.
        """

        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task ID '{task_id}' not found")
        return task.get_progress()

    def cancel(self, task_id: str) -> bool:
        """Attempt to cancel a task if it hasn't started.

        Args:
            task_id: Task identifier.

        Returns:
            True if cancelled, False otherwise.
        """

        task = self._tasks.get(task_id)
        if task and task.cancel():
            # Publish task cancellation event
            self._event_bus.publish(
                Event(
                    "task_canceled",
                    {"task_id": task_id, "function": task.function.__name__},
                )
            )
            return True
        return False

    def list_tasks(self) -> list[dict]:
        """List summaries of all submitted tasks.

        Returns:
            A list of task summaries.
        """

        return [
            {
                "id": t.id,
                "status": t.status,
                "function": t.function.__name__,
                "progress": t._progress,
                "message": t._progress_message,
            }
            for t in self._tasks.values()
        ]

    def subscribe_to_progress(
        self, callback: Callable[[dict], None]
    ) -> Callable[[], None]:
        """Subscribe to task progress events.

        Args:
            callback: Function to call when progress is reported.
                     The callback receives a dictionary with task_id, progress,
                     message, and function keys.

        Returns:
            Unsubscribe function.
        """

        def event_handler(event: Event):
            callback(event.data)

        return self._event_bus.subscribe("task_progress", event_handler)


# Global task manager instance
_task_manager = RemoteTaskManager()


def get_task_manager() -> RemoteTaskManager:
    """Get the global task manager instance.

    Returns:
        The singleton RemoteTaskManager instance
    """

    return _task_manager
