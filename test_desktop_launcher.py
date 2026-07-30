import sys
import subprocess
import unittest
from collections.abc import Callable
from urllib import error
from pathlib import Path
from unittest import mock

from desktop_launcher import (
    build_local_url,
    bundled_path,
    find_free_loopback_port,
    LauncherController,
    main,
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
        self.terminate_calls = 0
        self.killed = False

    def poll(self) -> int | None:
        return self.exit_code

    def terminate(self) -> None:
        self.terminate_calls += 1
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float) -> int:
        outcome = self.wait_results.pop(0) if self.wait_results else 0
        if isinstance(outcome, BaseException):
            raise outcome
        self.exit_code = int(outcome)
        return self.exit_code


class ProcessThatExitsDuringTermination(ProcessDouble):
    def terminate(self) -> None:
        raise ProcessLookupError("child already exited")


class LauncherViewDouble:
    """Synchronous stand-in for the Tk view's main-loop dispatcher."""

    def __init__(self) -> None:
        self.statuses: list[str] = []
        self.open_enabled: list[bool] = []
        self.close_calls = 0

    def post(self, callback: Callable[[], None]) -> None:
        callback()

    def set_status(self, status: str) -> None:
        self.statuses.append(status)

    def set_open_enabled(self, enabled: bool) -> None:
        self.open_enabled.append(enabled)

    def close(self) -> None:
        self.close_calls += 1


class ImmediateWorker:
    def __init__(self, target: Callable[[], None]) -> None:
        self.target = target

    def start(self) -> None:
        self.target()


class DeferredWorker:
    def __init__(self, target: Callable[[], None]) -> None:
        self.target = target

    def start(self) -> None:
        pass


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

    def test_terminate_process_ignores_child_exit_race_during_termination(self):
        process = ProcessThatExitsDuringTermination(exit_code=None)

        terminate_process(process)

        self.assertFalse(process.killed)


class DesktopLauncherControllerTest(unittest.TestCase):
    def make_controller(
        self,
        *,
        process: ProcessDouble | None = None,
        healthy: bool = True,
        browser_opener: mock.Mock | None = None,
    ) -> tuple[LauncherController, LauncherViewDouble, mock.Mock]:
        view = LauncherViewDouble()
        popen = mock.Mock(return_value=process or ProcessDouble(exit_code=None))
        controller = LauncherController(
            view,
            popen=popen,
            wait_for_health=lambda _port: healthy,
            browser_opener=browser_opener or mock.Mock(),
            port_finder=lambda: 45678,
            worker_factory=ImmediateWorker,
            monitor_worker_factory=lambda _target: None,
        )
        return controller, view, popen

    def test_start_uses_frozen_executable_and_streamlit_child_sentinel(self):
        controller, _view, popen = self.make_controller()

        with (
            mock.patch.object(sys, "frozen", True, create=True),
            mock.patch.object(sys, "executable", "/Applications/PROWRAP Calculator"),
        ):
            controller.start()

        command = popen.call_args.args[0]
        self.assertEqual(command, ["/Applications/PROWRAP Calculator", "--streamlit-child", "--port", "45678"])
        self.assertFalse(popen.call_args.kwargs["shell"])

    def test_start_uses_source_script_for_source_mode_child(self):
        controller, _view, popen = self.make_controller()

        with (
            mock.patch.dict(sys.__dict__, {}, clear=False),
            mock.patch.object(sys, "executable", "/usr/bin/python3"),
        ):
            sys.__dict__.pop("frozen", None)
            controller.start()

        command = popen.call_args.args[0]
        self.assertEqual(
            command,
            ["/usr/bin/python3", str(Path(__file__).with_name("desktop_launcher.py")), "--streamlit-child", "--port", "45678"],
        )

    def test_healthy_start_marks_ready_then_opens_browser_once(self):
        browser_opener = mock.Mock()
        controller, view, _popen = self.make_controller(browser_opener=browser_opener)

        controller.start()

        self.assertEqual(view.statuses[-1], "Ready")
        self.assertTrue(view.open_enabled[-1])
        browser_opener.assert_called_once_with("http://127.0.0.1:45678")

    def test_open_calculator_reuses_healthy_server_without_second_child(self):
        browser_opener = mock.Mock()
        controller, _view, popen = self.make_controller(browser_opener=browser_opener)
        controller.start()

        controller.open_calculator()

        self.assertEqual(popen.call_count, 1)
        self.assertEqual(browser_opener.call_count, 2)

    def test_startup_timeout_reports_actionable_error_and_stops_child(self):
        process = ProcessDouble(exit_code=None)
        controller, view, _popen = self.make_controller(process=process, healthy=False)

        controller.start()

        self.assertIn("Unable to start", view.statuses[-1])
        self.assertIn("try again", view.statuses[-1])
        self.assertFalse(view.open_enabled[-1])
        self.assertTrue(process.terminated)

    def test_quit_and_window_close_stop_the_child_only_once(self):
        process = ProcessDouble(exit_code=None)
        controller, view, _popen = self.make_controller(process=process)
        controller.start()

        controller.quit()
        controller.window_closed()

        self.assertTrue(process.terminated)
        self.assertEqual(process.terminate_calls, 1)
        self.assertEqual(view.close_calls, 1)

    def test_unexpected_child_exit_disables_launcher_without_zombie(self):
        process = ProcessDouble(exit_code=None)
        controller, view, _popen = self.make_controller(process=process)
        controller.start()
        process.exit_code = 1

        controller.handle_child_exit(process)

        self.assertIn("stopped unexpectedly", view.statuses[-1])
        self.assertFalse(view.open_enabled[-1])
        self.assertIsNone(controller.child)

    def test_quit_suppresses_ui_updates_from_a_late_health_worker(self):
        view = LauncherViewDouble()
        worker: DeferredWorker | None = None

        def make_worker(target: Callable[[], None]) -> DeferredWorker:
            nonlocal worker
            worker = DeferredWorker(target)
            return worker

        controller = LauncherController(
            view,
            popen=mock.Mock(return_value=ProcessDouble(exit_code=None)),
            wait_for_health=lambda _port: False,
            port_finder=lambda: 45678,
            worker_factory=make_worker,
            monitor_worker_factory=lambda _target: None,
        )
        controller.start()
        controller.quit()
        statuses_after_quit = list(view.statuses)

        assert worker is not None
        worker.target()

        self.assertEqual(view.statuses, statuses_after_quit)


class DesktopLauncherEntryPointTest(unittest.TestCase):
    def test_child_mode_runs_streamlit_cli_with_local_options(self):
        original_argv = sys.argv
        streamlit_main = mock.Mock(return_value=0)
        try:
            with mock.patch("desktop_launcher.invoke_streamlit_cli", streamlit_main):
                result = main(["--streamlit-child", "--port", "45678"])

            self.assertEqual(result, 0)
            self.assertEqual(sys.argv[0], "streamlit")
            self.assertEqual(sys.argv[1:4], ["run", str(bundled_path("PWR110Calculator.py")), "--server.address=127.0.0.1"])
            self.assertIn("--server.port=45678", sys.argv)
            streamlit_main.assert_called_once()
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
