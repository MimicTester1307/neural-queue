import threading
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Full, Empty

from src.neural_queue.core.queue.queue import Queue
from src.neural_queue.core.task.task import Task
from src.neural_queue.core.task.task_priority import TaskPriority
from src.neural_queue.core.task.task_state import TaskState

def test_queue_init():
    queue = Queue(maxsize=10)
    assert queue.is_empty()
    assert queue._tasks.maxsize == 10

def test_queue_put():
    queue = Queue()
    mock_func = lambda: None
    task = Task(func=mock_func, priority=TaskPriority.NORMAL)

    assert queue.put(task) is True
    assert queue.size() == 1

    # Test duplicate task
    assert queue.put(task) is False
    assert queue.size() == 1

def test_queue_priority_ordering():
    queue = Queue()

    # simulate tasks of varying priorities
    def task_processor(): return "processed"
    def urgent_alert(): return "alert"
    def background_job(): return "completed"
    def system_health_check(): return "healthy"

    # mix of tasks that might come in during normal operation
    tasks = [
        # burst of background jobs coming in
        Task(func=background_job, priority=TaskPriority.LOW),
        Task(func=background_job, priority=TaskPriority.LOW),
        Task(func=background_job, priority=TaskPriority.LOW),
        Task(func=background_job, priority=TaskPriority.LOW),

        # critical system alert comes in
        Task(func=urgent_alert, priority=TaskPriority.CRITICAL),

        # more background jobs
        Task(func=background_job, priority=TaskPriority.LOW),

        # regular processing tasks
        Task(func=task_processor, priority=TaskPriority.NORMAL),
        Task(func=task_processor, priority=TaskPriority.NORMAL),

        # high priority health check
        Task(func=system_health_check, priority=TaskPriority.HIGH),

        # mixed priority tasks
        Task(func=task_processor, priority=TaskPriority.NORMAL),
        Task(func=urgent_alert, priority=TaskPriority.CRITICAL),
    ]

    # add tasks in order they arrived
    for task in tasks:
       assert queue.put(task, timeout=1)

    # verify tasks come out in priority order
    priorities_retrieved = []
    while not queue.is_empty():
        task = queue.get(timeout=1)
        assert task is not None
        priorities_retrieved.append(task.priority)

    # verify priority ordering
    for i in range(len(priorities_retrieved) - 1):
        # each task should have priority greater than or equal to the next task
        assert priorities_retrieved[i].value >= priorities_retrieved[i + 1].value

    # verify exact counts of each priority level
    # thought of using a Counter class here, but since we append just the
    # values to the `priorities_retrieved` list, Counter would just create a
    # dictionary of numbers and their counts, which is not clear enough.
    priority_counts = {
        TaskPriority.CRITICAL: priorities_retrieved.count(TaskPriority.CRITICAL),
        TaskPriority.HIGH: priorities_retrieved.count(TaskPriority.HIGH),
        TaskPriority.NORMAL: priorities_retrieved.count(TaskPriority.NORMAL),
        TaskPriority.LOW: priorities_retrieved.count(TaskPriority.LOW),
    }

    assert priority_counts[TaskPriority.CRITICAL] == 2  # Two urgent alerts
    assert priority_counts[TaskPriority.HIGH] == 1      # One health check
    assert priority_counts[TaskPriority.NORMAL] == 3    # Three processing tasks
    assert priority_counts[TaskPriority.LOW] == 5       # Five background jobs


def test_queue_priority_ordering_with_continuous_insertion():
    queue = Queue()
    mock_func = lambda: None

    # start with low priority tasks
    for _ in range(3):
        task = Task(func=mock_func, priority=TaskPriority.LOW)
        queue.put(task, timeout=1)

    # add a high priority task--should jump to front
    high_task = Task(func=mock_func, priority=TaskPriority.HIGH)
    queue.put(high_task, timeout=1)

    # verify high priority comes out first
    next_task = queue.get(timeout=1)
    assert next_task is not None
    assert next_task.priority == TaskPriority.HIGH

    # add a critical tas while low priority tasks still in queue
    critical_task = Task(func=mock_func, priority=TaskPriority.CRITICAL)
    queue.put(critical_task, timeout=1)

    # add more low priority tasks
    for _ in range(2):
        task = Task(func=mock_func, priority=TaskPriority.LOW)
        queue.put(task, timeout=1)

    # verify tasks come out in priority order
    next_task = queue.get(timeout=1)
    assert next_task is not None
    assert next_task.priority == TaskPriority.CRITICAL

    # remaining tasks should be low priority
    while not queue.is_empty():
        task = queue.get(timeout=1)
        assert task is not None
        assert task.priority == TaskPriority.LOW

def test_queue_priority_with_timing():
    queue = Queue()
    results = []

    def slow_task():
        time.sleep(0.1)
        return "slow"

    def fast_task():
        return "fast"

    # Add a mix of tasks with different priorities and execution times
    tasks = [
        Task(func=slow_task, priority=TaskPriority.LOW),
        Task(func=fast_task, priority=TaskPriority.CRITICAL),
        Task(func=slow_task, priority=TaskPriority.LOW),
        Task(func=fast_task, priority=TaskPriority.HIGH),
        Task(func=slow_task, priority=TaskPriority.NORMAL),
    ]

    # insert tasks with small delays to simulate real-world arrival
    for task in tasks:
        queue.put(task, timeout=1)
        time.sleep(0.01) # delay between insertions

    # process all tasks
    while not queue.is_empty():
        task = queue.get(timeout=1)
        assert task is not None
        result = task.execute()
        results.append((task.priority, result.value))

    # verify results maintain priority order regardless of execution time
    for i in range(len(results) - 1):
        assert results[i][0].value >= results[i + 1][0].value
