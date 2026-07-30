import sys
import subprocess
import unittest
from urllib import error
from pathlib import Path
from unittest import mock

from desktop_launcher import (
    build_local_url,
    bundled_path,
    find_free_loopback_port,
    streamlit_child_args,
    terminate_process,
    wait_for_streamlit,
)


class TemporaryLoopbackSocket:
    def __init__(self, port: int) -> None:
        self.port = port
        self.bound_address: tuple[str, int] | None = None
        self.closed = False

    def __enter__(self) -> "TemporaryLoopbackSocket":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.closed = True

    def bind(self, address: tuple[str, int]) -> None:
        self.bound_address = address

    def getsockname(self) -> tuple[str, int]:
        return ("127.0.0.1", self.port)


class ProcessDouble:
    def __init__(self, exit_code: int | None, wait_results: list[object] | None = None) -> None:
        self.exit_code = exit_code
        self.wait_results = list(wait_results or [])
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.exit_code

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float) -> int:
        outcome = self.wait_results.pop(0) if self.wait_results else 0
        if isinstance(outcome, BaseException):
            raise outcome
        self.exit_code = int(outcome)
        return self.exit_code


class DesktopLauncherPathAndArgumentsTest(unittest.TestCase):
    def test_build_local_url_uses_loopback_address_and_port(self):
        self.assertEqual(build_local_url(8765), "http://127.0.0.1:8765")

    def test_find_free_loopback_port_returns_released_nonprivileged_port(self):
        temporary_socket = TemporaryLoopbackSocket(port=51234)
        with mock.patch("desktop_launcher.socket.socket", return_value=temporary_socket):
            port = find_free_loopback_port()

        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 1024)
        self.assertLessEqual(port, 65535)
        self.assertEqual(temporary_socket.bound_address, ("127.0.0.1", 0))
        self.assertTrue(temporary_socket.closed)

    def test_bundled_path_uses_source_directory_outside_frozen_runtime(self):
        with mock.patch.dict(sys.__dict__, {}, clear=False):
            sys.__dict__.pop("_MEIPASS", None)

            path = bundled_path("PWR110Calculator.py")

        self.assertEqual(path, Path(__file__).resolve().parent / "PWR110Calculator.py")

    def test_bundled_path_uses_pyinstaller_bundle_directory_when_frozen(self):
        bundle_directory = Path("/tmp/protap-bundle")
        with mock.patch.object(sys, "_MEIPASS", str(bundle_directory), create=True):
            path = bundled_path("PWR110Calculator.py")

        self.assertEqual(path, bundle_directory / "PWR110Calculator.py")

    def test_streamlit_child_args_preserve_local_security_defaults(self):
        app_path = Path("/Applications/PROTAP/PWR110Calculator.py")

        arguments = streamlit_child_args(app_path, 8765)

        self.assertIn(str(app_path), arguments)
        self.assertIn("--server.address=127.0.0.1", arguments)
        self.assertIn("--server.port=8765", arguments)
        self.assertIn("--server.headless=true", arguments)
        self.assertIn("--browser.gatherUsageStats=false", arguments)
        self.assertIn("--server.fileWatcherType=none", arguments)
        self.assertNotIn("--server.enableCORS=false", arguments)
        self.assertNotIn("--server.enableXsrfProtection=false", arguments)


class DesktopLauncherLifecycleTest(unittest.TestCase):
    def test_wait_for_streamlit_returns_true_when_health_endpoint_is_ready(self):
        response = mock.MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        with (
            mock.patch("desktop_launcher.urllib.request.urlopen", return_value=response) as urlopen,
            mock.patch("desktop_launcher.time.monotonic", return_value=10.0),
        ):
            ready = wait_for_streamlit(8765)

        self.assertTrue(ready)
        self.assertEqual(urlopen.call_args.args[0], "http://127.0.0.1:8765/_stcore/health")

    def test_wait_for_streamlit_retries_a_failed_health_request(self):
        response = mock.MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        with (
            mock.patch(
                "desktop_launcher.urllib.request.urlopen",
                side_effect=[error.URLError("not ready"), response],
            ) as urlopen,
            mock.patch("desktop_launcher.time.monotonic", return_value=10.0),
            mock.patch("desktop_launcher.time.sleep"),
        ):
            ready = wait_for_streamlit(8765)

        self.assertTrue(ready)
        self.assertEqual(urlopen.call_count, 2)

    def test_wait_for_streamlit_returns_false_when_deadline_passes(self):
        with (
            mock.patch(
                "desktop_launcher.urllib.request.urlopen",
                side_effect=error.URLError("not ready"),
            ),
            mock.patch("desktop_launcher.time.monotonic", side_effect=[0.0, 0.0, 1.0]),
            mock.patch("desktop_launcher.time.sleep"),
        ):
            ready = wait_for_streamlit(8765, timeout_seconds=0.5)

        self.assertFalse(ready)

    def test_terminate_process_stops_a_running_child_cleanly(self):
        process = ProcessDouble(exit_code=None)

        terminate_process(process, timeout_seconds=0.5)

        self.assertTrue(process.terminated)
        self.assertFalse(process.killed)
        self.assertEqual(process.exit_code, 0)

    def test_terminate_process_skips_an_already_exited_child(self):
        process = ProcessDouble(exit_code=0)

        terminate_process(process)

        self.assertFalse(process.terminated)
        self.assertFalse(process.killed)

    def test_terminate_process_kills_child_that_does_not_exit_after_termination(self):
        process = ProcessDouble(
            exit_code=None,
            wait_results=[subprocess.TimeoutExpired(["streamlit"], 0.5), 0],
        )

        terminate_process(process, timeout_seconds=0.5)

        self.assertTrue(process.terminated)
        self.assertTrue(process.killed)
        self.assertEqual(process.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
