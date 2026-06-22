import time
import logging
from typing import Optional, Type
from types import TracebackType

logger = logging.getLogger(__name__)

class ThresholdValidator:
    def __init__(self, target_seconds: float, process_identifier: str):
        self.target_seconds = target_seconds
        self.process_identifier = process_identifier
        self.start_time: float = 0.0
        self.execution_time: float = 0.0

    def __enter__(self) -> 'ThresholdValidator':
        self.start_time = time.perf_counter()
        return self

    def __exit__(
        self, 
        exc_type: Optional[Type[BaseException]], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType]
    ) -> None:
        self.execution_time = time.perf_counter() - self.start_time
        
        if exc_type is None:
            if self.execution_time > self.target_seconds:
                logger.warning(
                    "NFR_5.1_VIOLATION: [%s] Execution time %.4fs exceeded %.2fs threshold.",
                    self.process_identifier, self.execution_time, self.target_seconds
                )
            else:
                logger.info(
                    "NFR_5.1_COMPLIANCE: [%s] Execution completed in %.4fs.",
                    self.process_identifier, self.execution_time
                )
