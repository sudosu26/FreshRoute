"""Start FreshRoute's API and dashboard, then open the dashboard in a browser."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_URL = "http://localhost:8000/"
FRONTEND_URL = "http://localhost:5173/"
STARTUP_TIMEOUT_SECONDS = 60


def is_available(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2):
            return True
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_until_available(
    url: str, process: subprocess.Popen[bytes], service_name: str
) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(
                f"The {service_name} process exited with code {exit_code}."
            )
        if is_available(url):
            return
        time.sleep(0.5)
    raise RuntimeError(
        f"The {service_name} did not become available at {url} "
        f"within {STARTUP_TIMEOUT_SECONDS} seconds."
    )


def npm_executable() -> str:
    executable = shutil.which("npm.cmd") or shutil.which("npm")
    if executable is None:
        raise RuntimeError("npm was not found. Install Node.js and try again.")
    return executable


def stop_processes(processes: list[subprocess.Popen[bytes]]) -> None:
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
    for process in reversed(processes):
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    processes: list[subprocess.Popen[bytes]] = []
    try:
        if not is_available(BACKEND_URL):
            print("Starting FreshRoute API...")
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "main:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "8000",
                    ],
                    cwd=ROOT / "backend",
                )
            )
            wait_until_available(BACKEND_URL, processes[-1], "backend")
        else:
            print(f"Using the API already running at {BACKEND_URL}")

        frontend_dir = ROOT / "frontend"
        npm = npm_executable()
        if not (frontend_dir / "node_modules").is_dir():
            print("Installing frontend dependencies...")
            install = subprocess.run(
                [npm, "install"],
                cwd=frontend_dir,
                check=False,
            )
            if install.returncode != 0:
                raise RuntimeError(
                    f"Installing frontend dependencies failed "
                    f"with code {install.returncode}."
                )

        if not is_available(FRONTEND_URL):
            print("Starting FreshRoute dashboard...")
            processes.append(
                subprocess.Popen(
                    [npm, "run", "dev", "--", "--host", "0.0.0.0"],
                    cwd=frontend_dir,
                )
            )
            wait_until_available(FRONTEND_URL, processes[-1], "frontend")
        else:
            print(f"Using the dashboard already running at {FRONTEND_URL}")

        print(f"FreshRoute is ready: {FRONTEND_URL}")
        if not webbrowser.open_new_tab(FRONTEND_URL):
            print("Could not open a browser automatically; use the URL above.")
        print("Press Ctrl+C to stop services started by this launcher.")
        while processes:
            for process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    raise RuntimeError(
                        f"A FreshRoute service stopped unexpectedly "
                        f"(exit code {exit_code})."
                    )
            time.sleep(1)
        return 0
    except KeyboardInterrupt:
        print("\nStopping FreshRoute services...")
        return 0
    except (OSError, RuntimeError) as error:
        print(f"Could not launch FreshRoute: {error}", file=sys.stderr)
        return 1
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
