from __future__ import annotations

from src.neural_queue.core.task.task_state import TaskState
from src.neural_queue.core.task.task_result import TaskResult
from src.neural_queue.core.task.task_priority import TaskPriority

import uuid
from dataclasses import dataclass, field
import datetime
from typing import Any, Callable, Dict, Optional
import time


@dataclass
class Task:
    """
    Class representing a task in the queue system.

    Attributes:
        func: the function to execute
        args: the positional arguments for the function
        kwargs: the keyword arguments for the function
        task_id: unique identifier of the task
        state: current state of the task
        priority: task priority
        created_at: timestamp when task was created
        started_at: timestamp when task was started
        completed_at: timestamp when task was completed
        result: result of task execution
    """
    func: Callable[..., Any]
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: TaskState = field(default=TaskState.PENDING)
    priority: TaskPriority = field(default=TaskPriority.NORMAL)
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    started_at: Optional[datetime.datetime] = field(default=None)
    completed_at: Optional[datetime.datetime] = field(default=None)
    result: Optional[TaskResult] = field(default=None)

    def __str__(self) -> str:
        status = f"[{self.state.value}]"
        func_name = self.func.__name__ if hasattr(self.func, "__name__") else self.func.__qualname__

        # format arguments if present
        args_str = f"args={self.args}" if self.args else ""
        kwargs_str = f"kwargs={self.kwargs}" if self.kwargs else ""
        args_kwargs = ", ".join(filter(None, [args_str, kwargs_str]))
        args_kwargs = f"({args_kwargs})" if args_kwargs else "()"

        # format timing info
        timing = f"created={self.created_at.isoformat()}"
        if self.started_at:
            timing += f", started={self.started_at.isoformat()}"
        if self.completed_at:
            timing += f", completed={self.completed_at.isoformat()}"

        # format result if present
        result_str = ""
        if self.result:
            if self.result.success:
                result_str = f" → {self.result.value}"
            else:
                result_str = f" → {self.result.error}"

        return f"Task {status} {func_name}{args_kwargs} ({self.task_id}, {self.priority.name} | {timing}{result_str}"

    def __repr__(self) -> str:
        attrs = [
            f"func={self.func.__name__ if hasattr(self.func, '__name__') else str(self.func)}",
            f"args={self.args!r}",
            f"kwargs={self.kwargs!r}",
            f"task_id={self.task_id!r}",
            f"state={self.state!r}",
            f"priority={self.priority!r}",
            f"created_at={self.created_at!r}",
            f"started_at={self.started_at!r}",
            f"completed_at={self.completed_at!r}",
            f"result={self.result!r}"
        ]
        return f"Task({', '.join(attrs)})"

    def __hash__(self) -> int:
        """Make Task hashable using its unique task_id"""
        return hash(self.task_id)

    def __eq__(self, other: Task) -> bool:
        """Tasks are equal if they have the same task_id"""
        if not isinstance(other, Task):
            return NotImplemented
        return self.task_id == other.task_id

    def __lt__(self, other: Task) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority.value > other.priority.value

    def execute(self) -> TaskResult:
        """Execute the task and return the result."""
        self.state = TaskState.RUNNING
        self.started_at = datetime.datetime.now(datetime.UTC)

        start_time = time.time()
        try:
            result = self.func(*self.args, **self.kwargs)
            execution_time = time.time() - start_time

            self.result = TaskResult(success=True,
                                     value=result,
                                     execution_time=execution_time
            )
            self.state = TaskState.COMPLETED
        except Exception as e:
            execution_time = time.time() - start_time
            self.result = TaskResult(success=False,
                                     error=str(e),
                                     execution_time=execution_time
            )
            self.state = TaskState.FAILED

        self.completed_at = datetime.datetime.now(datetime.UTC)
        return self.result

    def get_state(self) -> TaskState:
        """Return the state of the task."""
        return self.state

    def cancel(self) -> bool:
        """
        Cancel the task if it hasn't started executing.
        :return: True if the cancellation was successful, False otherwise.
        """
        if self.state in (TaskState.PENDING, TaskState.SCHEDULED):
            self.state = TaskState.CANCELLED
            return True
        return False
