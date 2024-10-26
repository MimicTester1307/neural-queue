from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class TaskResult:
    """Class representing the result of a task execution."""
    success: bool
    value: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None # possibly change Optional[float] to Optional[datetime]