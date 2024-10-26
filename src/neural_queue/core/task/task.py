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

    def __lt__(self, other: Task) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority.value > other.priority.value
