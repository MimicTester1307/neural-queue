from enum import Enum

class TaskPriority(Enum):
    """Represent the possible priority of a task."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3