from __future__ import annotations

from queue import PriorityQueue, Empty, Full
from typing import Optional, Dict
from threading import Lock

from src.neural_queue.core.task.task import Task

class Queue:
    """
    A thread-safe queue implementation for tasks.

    Uses Python's built-in PriorityQueue for thread-safe priority ordering
    and a synchronized dictionary for O(1) task lookups.
    """
    def __init__(self, maxsize: int = 0):
        """
        Initialize the queue.

        Args:
            maxsize (int): Maximum number of tasks the queue can hold. 0 means unlimited.
        """
        self._tasks = PriorityQueue(maxsize=maxsize)
        self._task_lookup: Dict[str, Task] = {}
        self._lookup_lock = Lock() # Separate lock for the lookup dictionary

    def put(self, task: Task, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Add a task to the queue.

        Args:
            task (Task): Task to be added
            block (bool): If True, block if necessary until a free slot is available
            timeout (float): Maximum time to block (None means infinite)

        Returns:
            bool: True if task was added successfully, False if queue is full or duplicate

        Raises:
            ValueError: If task is None.
        """
        if task is None:
            raise ValueError("Cannot add None task to queue")

        with self._lookup_lock:
            if task.task_id in self._task_lookup:
                return False

            try:
                # PriorityQueue expects a tuple where first element determines priority
                # We negate priority value because heapq is min-heap, but we want higher priority first
                self._tasks.put((-task.priority.value, task), block=block, timeout=timeout)
                self._task_lookup[task.task_id] = task
                return True
            # catches queue.Full and timing out
            except (Full, TimeoutError):
                return False

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Task]:
        """
        Get the highest priority task from the queue.

        Args:
            block: If True, block if necessary until an item is available
            timeout: Maximum time to block (None means infinite)

        Returns:
            Task or None: The highest priority task, or None if queue is empty
        """
        try:
            _, task = self._tasks.get(block=block, timeout=timeout)
            with self._lookup_lock:
                del self._task_lookup[task.task_id]
            return task
        # catches queue.Empty and timing out
        except (Empty, TimeoutError):
            return None

    def peek(self) -> Optional[Task]:
        """
        Look at the highest priority task without removing it.

        Note: This operation is not atomic with respect to get/put.
        Returns:
            Task or None: The highest priority task, or None if queue is empty
        """
        with self._lookup_lock:
            if not self._task_lookup:
                return None
            # Return any task since we can't peek PriorityQueue
            return next(iter(self._task_lookup.values()))

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a task by its ID without removing it from the queue.

        Args:
            task_id: The ID of the task to be retrieved

        Returns:
            Task or None: The task if found,  None otherwise
        """
        with self._lookup_lock:
            return self._task_lookup.get(task_id)

    def remove_task(self, task_id: str) -> Optional[Task]:
        """
        Remove a specific task from the queue by its ID.

        Note: this operation requires creating a new queue, so it's expensive.
        Consider using cancel_task() instead if you don't need the task removed immediately.

        Args:
            task_id: The ID of the task to be removed

        Returns:
            Task or None: The task if found, None otherwise
        """
        with self._lookup_lock:
            if task_id not in self._task_lookup:
                return None

            task = self._task_lookup[task_id]
            del self._task_lookup[task_id]

            # create a new queue without the removed task
            new_queue = PriorityQueue(maxsize=self._tasks.maxsize)
            while True:
                try:
                    priority, current_task = self._tasks.get_nowait()
                    if current_task.task_id != task_id:
                        new_queue.put((priority, current_task))
                except Empty:
                    break

            self._tasks = new_queue
            return task

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if it hasn't been executing.
        The task remains in queue but will be ignored when retrieved.

        Args:
            task_id: ID of the task to cancel

        Returns:
            bool: True if task was cancelled successfully, False otherwise
        """
        with self._lookup_lock:
            task = self._task_lookup.get(task_id)
            if task and task.cancel():
                return True
            return False

    def size(self) -> int:
        """Return the current number of tasks in the queue."""
        return self._tasks.qsize()

    def clear(self) -> None:
        """Remove all tasks from the queue."""
        try:
            while True:
                self._tasks.get_nowait()
        except Empty:
                pass

        with self._lookup_lock:
            self._task_lookup.clear()

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self._tasks.empty()