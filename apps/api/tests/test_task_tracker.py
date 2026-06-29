"""Tests for TaskTracker background task management."""

import asyncio

import pytest

from core.task_tracker import TaskTracker


@pytest.mark.asyncio
async def test_tracker_tracks_tasks():
    tracker = TaskTracker()

    async def dummy():
        pass

    task = tracker.create_task(dummy(), name="test-task")
    assert tracker.active_count == 1
    assert "test-task" in tracker.get_active_tasks()

    await task
    assert tracker.active_count == 0


@pytest.mark.asyncio
async def test_tracker_shutdown_cancels_tasks():
    tracker = TaskTracker()

    async def long_running():
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            pass

    tracker.create_task(long_running(), name="long-task-1")
    tracker.create_task(long_running(), name="long-task-2")

    assert tracker.active_count == 2

    await tracker.shutdown(timeout=5.0)
    assert tracker.active_count == 0


@pytest.mark.asyncio
async def test_tracker_shutdown_no_tasks():
    tracker = TaskTracker()
    await tracker.shutdown(timeout=1.0)
    assert tracker.active_count == 0


@pytest.mark.asyncio
async def test_tracker_multiple_tasks():
    tracker = TaskTracker()

    results = []

    async def worker(n):
        results.append(n)

    tasks = [tracker.create_task(worker(i), name=f"worker-{i}") for i in range(5)]
    assert tracker.active_count == 5

    await asyncio.gather(*tasks)
    assert tracker.active_count == 0
    assert len(results) == 5
    assert sorted(results) == [0, 1, 2, 3, 4]
