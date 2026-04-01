"""Tests for TaskEntry and TaskLog."""

from datetime import datetime
import pytest

from passport.task_log import TaskEntry, TaskLog


def test_create_task_entry():
    """Test creating a task entry."""
    entry = TaskEntry(
        task_id="task-123",
        description="Implement feature X",
        completed_at="2026-01-01",
        skill_used="python",
        outcome="success",
        feedback="good"
    )

    assert entry.task_id == "task-123"
    assert entry.outcome == "success"
    assert entry.feedback == "good"


def test_task_entry_serialization():
    """Test task entry to_dict and from_dict."""
    entry1 = TaskEntry(
        task_id="task-123",
        description="Test task",
        completed_at="2026-01-01",
        skill_used="python",
        outcome="success",
        feedback="good"
    )

    data = entry1.to_dict()
    entry2 = TaskEntry.from_dict(data)

    assert entry2.task_id == entry1.task_id
    assert entry2.description == entry1.description
    assert entry2.outcome == entry1.outcome


def test_task_log_add():
    """Test adding task entries to log."""
    log = TaskLog()

    entry = TaskEntry(
        task_id="task-123",
        description="Test",
        completed_at="2026-01-01",
        skill_used="python",
        outcome="success"
    )

    log.add(entry)

    assert len(log.entries) == 1


def test_task_log_get_by_outcome():
    """Test filtering tasks by outcome."""
    log = TaskLog()

    log.add(TaskEntry("t1", "Test 1", "2026-01-01", "python", "success"))
    log.add(TaskEntry("t2", "Test 2", "2026-01-01", "python", "success"))
    log.add(TaskEntry("t3", "Test 3", "2026-01-01", "python", "failure"))
    log.add(TaskEntry("t4", "Test 4", "2026-01-01", "python", "partial"))

    successes = log.get_by_outcome("success")
    failures = log.get_by_outcome("failure")

    assert len(successes) == 2
    assert len(failures) == 1


def test_task_log_get_by_skill():
    """Test filtering tasks by skill."""
    log = TaskLog()

    log.add(TaskEntry("t1", "Test 1", "2026-01-01", "python", "success"))
    log.add(TaskEntry("t2", "Test 2", "2026-01-01", "python", "success"))
    log.add(TaskEntry("t3", "Test 3", "2026-01-01", "javascript", "success"))

    python_tasks = log.get_by_skill("python")
    js_tasks = log.get_by_skill("javascript")

    assert len(python_tasks) == 2
    assert len(js_tasks) == 1


def test_task_log_success_rate():
    """Test calculating success rate."""
    log = TaskLog()

    # 3 successes, 1 failure = 75% success rate
    log.add(TaskEntry("t1", "Test 1", "2026-01-01", "python", "success"))
    log.add(TaskEntry("t2", "Test 2", "2026-01-01", "python", "success"))
    log.add(TaskEntry("t3", "Test 3", "2026-01-01", "python", "success"))
    log.add(TaskEntry("t4", "Test 4", "2026-01-01", "python", "failure"))

    rate = log.get_success_rate()

    assert rate == 0.75


def test_task_log_success_rate_empty():
    """Test success rate with no tasks."""
    log = TaskLog()

    rate = log.get_success_rate()

    assert rate == 0.5  # Default when no data


def test_task_log_stats():
    """Test getting task log statistics."""
    log = TaskLog()

    log.add(TaskEntry("t1", "Test 1", "2026-01-01", "python", "success", "good"))
    log.add(TaskEntry("t2", "Test 2", "2026-01-01", "python", "success", "good"))
    log.add(TaskEntry("t3", "Test 3", "2026-01-01", "javascript", "failure", "bad"))
    log.add(TaskEntry("t4", "Test 4", "2026-01-01", "python", "partial", "meh"))

    stats = log.get_stats()

    assert stats["total"] == 4
    assert stats["success"] == 2
    assert stats["failure"] == 1
    assert stats["partial"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["feedback"]["good"] == 2
    assert stats["feedback"]["bad"] == 1
    assert stats["feedback"]["meh"] == 1
    assert stats["skill_usage"]["python"] == 3
    assert stats["skill_usage"]["javascript"] == 1


def test_task_log_to_list():
    """Test converting task log to list."""
    log = TaskLog()

    log.add(TaskEntry("t1", "Test", "2026-01-01", "python", "success"))

    task_list = log.to_list()

    assert len(task_list) == 1
    assert isinstance(task_list[0], dict)
    assert task_list[0]["task_id"] == "t1"
