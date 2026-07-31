from __future__ import annotations

import atexit
from queue import Empty, SimpleQueue
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from collections.abc import Callable, Sequence
from typing import Any, Protocol


def bundled_path(filename: str) -> Path:
    """Return a bundled file path for source and PyInstaller runtimes."""
    base_directory = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_directory / filename


def find_free_loopback_port() -> int:
    """Ask the operating system for an available loopback TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temporary_socket:
        temporary_socket.bind(("127.0.0.1", 0))
        return int(temporary_socket.getsockname()[1])


def build_local_url(port: int) -> str:
    """Build the local-only URL shown by the desktop launcher."""
    return f"http://127.0.0.1:{port}"


def streamlit_child_args(app_path: Path, port: int) -> list[str]:
    """Build the Streamlit command without weakening its web protections."""
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
    ]


def wait_for_streamlit(port: int, timeout_seconds: float = 30.0) -> bool:
    """Wait until Streamlit reports that its loopback health endpoint is ready."""
    health_url = f"{build_local_url(port)}/_stcore/health"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=0.5) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.1)
    return False


def terminate_process(
    process: subprocess.Popen[bytes], timeout_seconds: float = 5.0
) -> bool:
    """Stop a child process, escalating only when it ignores termination."""
    if process.poll() is not None:
        return True
    try:
        process.terminate()
    except ProcessLookupError:
        return True
    try:
        process.wait(timeout=timeout_seconds)
        return True
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=timeout_seconds)
            return True
        except ProcessLookupError:
            return True
        except subprocess.TimeoutExpired:
            return False


def streamlit_cli_args(app_path: Path, port: int) -> list[str]:
    """Build the argv consumed by Streamlit's supported CLI entry point."""
    return ["streamlit", *streamlit_child_args(app_path, port)[3:]]


def streamlit_child_command(port: int) -> list[str]:
    """Build the process command that re-enters this executable in child mode."""
    command = [sys.executable]
    if not getattr(sys, "frozen", False):
        command.append(str(Path(__file__).resolve()))
    return [*command, "--streamlit-child", "--port", str(port)]


def invoke_streamlit_cli() -> int:
    """Run Streamlit through its supported Python CLI entry point."""
    from streamlit.web import cli as streamlit_cli

    return int(streamlit_cli.main() or 0)


class LauncherView(Protocol):
    """Small UI boundary used to keep lifecycle behavior testable without Tk."""

    def post(self, callback: Callable[[], None]) -> None: ...

    def set_status(self, status: str) -> None: ...

    def set_open_enabled(self, enabled: bool) -> None: ...

    def close(self) -> None: ...


class LauncherController:
    """Own the local Streamlit child process for the launcher window lifetime."""

    def __init__(
        self,
        view: LauncherView,
        *,
        popen: Callable[..., Any] = subprocess.Popen,
        wait_for_health: Callable[[int], bool] = wait_for_streamlit,
        browser_opener: Callable[[str], Any] = webbrowser.open,
        port_finder: Callable[[], int] = find_free_loopback_port,
        worker_factory: Callable[[Callable[[], None]], Any] | None = None,
        monitor_worker_factory: Callable[[Callable[[], None]], Any] | None = None,
        shutdown_worker_factory: Callable[[Callable[[], None]], Any] | None = None,
        register_exit: Callable[[Callable[[], None]], Any] = atexit.register,
    ) -> None:
        self.view = view
        self._popen = popen
        self._wait_for_health = wait_for_health
        self._browser_opener = browser_opener
        self._port_finder = port_finder
        self._worker_factory = worker_factory or self._background_worker
        self._monitor_worker_factory = monitor_worker_factory or self._background_worker
        self._shutdown_worker_factory = shutdown_worker_factory or self._background_worker
        self._lock = threading.RLock()
        self.child: Any | None = None
        self.port: int | None = None
        self.url: str | None = None
        self._ready = False
        self._closed = False
        register_exit(self.stop)

    @staticmethod
    def _background_worker(target: Callable[[], None]) -> threading.Thread:
        return threading.Thread(target=target, daemon=True)

    def _post_status(self, status: str) -> None:
        self._post_if_open(lambda: self.view.set_status(status))

    def _post_open_enabled(self, enabled: bool) -> None:
        self._post_if_open(lambda: self.view.set_open_enabled(enabled))

    def _post_if_open(self, callback: Callable[[], None]) -> None:
        with self._lock:
            if self._closed:
                return
        self.view.post(lambda: self._deliver_if_open(callback))

    def _deliver_if_open(self, callback: Callable[[], None]) -> None:
        with self._lock:
            if self._closed:
                return
        callback()

    def start(self) -> None:
        """Start one local child and begin non-blocking health polling."""
        with self._lock:
            if self._closed or (self.child is not None and self.child.poll() is None):
                return
            self._ready = False
            self._post_status("Starting")
            self._post_open_enabled(False)
            self.port = self._port_finder()
            self.url = build_local_url(self.port)
            try:
                self.child = self._popen(streamlit_child_command(self.port), shell=False)
            except OSError as exc:
                self.child = None
                self._post_status(f"Unable to start: {exc}. Please try again.")
                return
            child = self.child
            port = self.port

        worker = self._worker_factory(lambda: self._wait_until_ready(child, port))
        worker.start()

    def _wait_until_ready(self, child: Any, port: int) -> None:
        ready = self._wait_for_health(port)
        with self._lock:
            if self._closed:
                return
            active = not self._closed and child is self.child and child.poll() is None
            if ready and active:
                self._ready = True
                url = self.url
            else:
                self._ready = False
                url = None

        if url is not None:
            self._post_status("Ready")
            self._post_open_enabled(True)
            self._open_browser_if_ready(child, url)
            monitor = self._monitor_worker_factory(lambda: self._monitor_child(child))
            if monitor is not None:
                monitor.start()
            return

        self._stop_child(child)
        self._post_open_enabled(False)
        self._post_status("Unable to start: the local server did not respond. Please try again.")

    def _open_browser_if_ready(self, child: Any, url: str) -> None:
        with self._lock:
            if self._closed or not self._ready or child is not self.child or child.poll() is not None:
                return
            self._browser_opener(url)

    def _monitor_child(self, child: Any) -> None:
        while child.poll() is None:
            time.sleep(0.2)
        self.handle_child_exit(child)

    def handle_child_exit(self, child: Any) -> None:
        """Reflect an unexpected Streamlit exit without retaining a stale child."""
        with self._lock:
            if self._closed or child is not self.child:
                return
            self.child = None
            self._ready = False
        self._post_open_enabled(False)
        self._post_status("Unable to start: the local server stopped unexpectedly. Please try again.")

    def open_calculator(self) -> None:
        """Open the already-healthy loopback URL without starting another child."""
        with self._lock:
            child = self.child
            url = self.url
        if child is not None and url is not None:
            self._open_browser_if_ready(child, url)

    def _stop_child(self, child: Any) -> bool:
        stopped = terminate_process(child)
        if stopped:
            with self._lock:
                if child is self.child:
                    self.child = None
        return stopped

    def stop(self) -> bool:
        """Stop the owned child, retaining it when kill escalation times out."""
        with self._lock:
            child = self.child
            self._ready = False
        if child is None:
            return True
        return self._stop_child(child)

    def quit(self) -> None:
        """Handle both the Quit button and the window-manager close request."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.view.close()
        worker = self._shutdown_worker_factory(self.stop)
        worker.start()

    def window_closed(self) -> None:
        self.quit()


class TkLauncherView:
    """Compact Tkinter control window; controller work stays off the main loop."""

    def __init__(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        self.root = tk.Tk()
        self._dispatch_lock = threading.Lock()
        self._dispatch_queue: SimpleQueue[Callable[[], None]] = SimpleQueue()
        self._closed = False
        self.root.title("PROWRAP ISO 24817 Calculator")
        self.root.resizable(False, False)

        frame = ttk.Frame(self.root, padding=16)
        frame.grid()
        self._status = tk.StringVar(value="Starting")
        ttk.Label(frame, textvariable=self._status).grid(row=0, column=0, columnspan=2, sticky="w")
        self._open_button = ttk.Button(frame, text="Open Calculator", state=tk.DISABLED)
        self._open_button.grid(row=1, column=0, pady=(12, 8), padx=(0, 8))
        self._quit_button = ttk.Button(frame, text="Quit")
        self._quit_button.grid(row=1, column=1, pady=(12, 8))
        ttk.Label(frame, text="Calculation data remains local on this Mac.").grid(
            row=2, column=0, columnspan=2, sticky="w"
        )

        self.controller = LauncherController(self)
        self._open_button.configure(command=self.controller.open_calculator)
        self._quit_button.configure(command=self.controller.quit)
        self.root.protocol("WM_DELETE_WINDOW", self.controller.window_closed)
        self.root.after(20, self._drain_dispatch_queue)

    def post(self, callback: Callable[[], None]) -> None:
        with self._dispatch_lock:
            if self._closed:
                return
            self._dispatch_queue.put(callback)

    def _drain_dispatch_queue(self) -> None:
        with self._dispatch_lock:
            if self._closed:
                return
        while True:
            try:
                callback = self._dispatch_queue.get_nowait()
            except Empty:
                break
            with self._dispatch_lock:
                if self._closed:
                    return
            callback()
        with self._dispatch_lock:
            if not self._closed:
                self.root.after(20, self._drain_dispatch_queue)

    def set_status(self, status: str) -> None:
        self._status.set(status)

    def set_open_enabled(self, enabled: bool) -> None:
        self._open_button.configure(state=self._tk.NORMAL if enabled else self._tk.DISABLED)

    def close(self) -> None:
        with self._dispatch_lock:
            if self._closed:
                return
            self._closed = True
        self.root.destroy()

    def run(self) -> None:
        self.controller.start()
        self.root.mainloop()


def _child_port(arguments: Sequence[str]) -> int:
    if len(arguments) != 3 or arguments[1] != "--port":
        raise ValueError("--streamlit-child requires --port PORT")
    return int(arguments[2])


def run_launcher() -> int:
    TkLauncherView().run()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the normal Tk launcher or its private Streamlit child mode."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "--streamlit-child":
        try:
            port = _child_port(arguments)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
        sys.argv = streamlit_cli_args(bundled_path("PWR110Calculator.py"), port)
        return invoke_streamlit_cli()
    return run_launcher()


if __name__ == "__main__":
    raise SystemExit(main())
