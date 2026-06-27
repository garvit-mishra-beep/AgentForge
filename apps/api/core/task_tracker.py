"""Background task tracking for graceful shutdown and monitoring."""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class TaskTracker:
    """Tracks asyncio background tasks for graceful shutdown and monitoring."""

    def __init__(self):
        self._tasks: set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()

    def create_task(
        self,
        coro: Coroutine[Any, Any, Any],
        name: str | None = None,
    ) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self, timeout: float = 30.0) -> None:
        self._shutdown_event.set()
        if not self._tasks:
            logger.info("No background tasks to cancel")
            return

        logger.info("Cancelling %d background tasks...", len(self._tasks))
        for task in list(self._tasks):
            task.cancel()

        done, pending = await asyncio.wait(
            self._tasks,
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED,
        )

        if pending:
            logger.warning(
                "%d tasks did not complete within %ss",
                len(pending), timeout,
            )
        else:
            logger.info("All background tasks completed")

        self._tasks.clear()

    @property
    def active_count(self) -> int:
        return len(self._tasks)

    def get_active_tasks(self) -> list[str]:
        return [t.get_name() for t in self._tasks if not t.done()]


# Global singleton for the application
tracker = TaskTracker()
