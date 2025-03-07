import logging
import threading

import pytest

from truss.util.log_utils import LogInterceptor


@pytest.fixture
def log_interceptor():
    return LogInterceptor()


def test_emit_with_formatter(log_interceptor):
    formatter = logging.Formatter("%(message)s")
    log_interceptor._formatter = formatter

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )

    with log_interceptor:
        log_interceptor.emit(record)

    assert log_interceptor.get_logs() == ["test message"]


def test_emit_without_formatter(log_interceptor):
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )

    with log_interceptor:
        log_interceptor.emit(record)

    assert len(log_interceptor.get_logs()) == 1
    assert "test message" in log_interceptor.get_logs()[0]


def test_emit_multiple_threads():
    def thread_func():
        interceptor = LogInterceptor()
        with interceptor:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="thread message",
                args=(),
                exc_info=None,
            )
            interceptor.emit(record)
            assert interceptor.get_logs()[0].endswith("thread message")

    threads = [threading.Thread(target=thread_func) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def test_get_logs_empty(log_interceptor):
    assert log_interceptor.get_logs() == []


def test_get_logs_multiple_messages(log_interceptor):
    formatter = logging.Formatter("%(message)s")
    log_interceptor._formatter = formatter

    records = [
        logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"message {i}",
            args=(),
            exc_info=None,
        )
        for i in range(3)
    ]

    with log_interceptor:
        for record in records:
            log_interceptor.emit(record)

    assert log_interceptor.get_logs() == ["message 0", "message 1", "message 2"]


def test_thread_isolation():
    def thread_func(msg):
        interceptor = LogInterceptor()
        with interceptor:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=msg,
                args=(),
                exc_info=None,
            )
            interceptor.emit(record)
            assert len(interceptor.get_logs()) == 1
            assert interceptor.get_logs()[0].endswith(msg)

    t1 = threading.Thread(target=thread_func, args=("message 1",))
    t2 = threading.Thread(target=thread_func, args=("message 2",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()


def test_nested_interceptors():
    outer = LogInterceptor()
    inner = LogInterceptor()

    with outer:
        with inner:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="test message",
                args=(),
                exc_info=None,
            )
            inner.emit(record)
            assert len(inner.get_logs()) == 1
            assert len(outer.get_logs()) == 0

        assert len(outer.get_logs()) == 0


def test_restore_handlers():
    original_handlers = logging.root.handlers[:]
    interceptor = LogInterceptor()

    with interceptor:
        logging.info("test")
        assert logging.root.handlers == [interceptor]

    assert logging.root.handlers == original_handlers


def test_multiple_interceptors_sequential():
    interceptor1 = LogInterceptor()
    interceptor2 = LogInterceptor()

    with interceptor1:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="message 1",
            args=(),
            exc_info=None,
        )
        interceptor1.emit(record)
        assert len(interceptor1.get_logs()) == 1
        assert "message 1" in interceptor1.get_logs()[0]

    with interceptor2:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="message 2",
            args=(),
            exc_info=None,
        )
        interceptor2.emit(record)
        assert len(interceptor2.get_logs()) == 1
        assert "message 2" in interceptor2.get_logs()[0]
