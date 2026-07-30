from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


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
) -> None:
    """Stop a child process, escalating only when it ignores termination."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout_seconds)
