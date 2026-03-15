"""Vercel entrypoint.

Vercel's Python runtime expects a WSGI-compatible callable named `app`.
Streamlit isn't WSGI-native, so we proxy requests to a Streamlit server that
we start on-demand inside the serverless function environment.

Note: This is a best-effort adapter. For production-grade hosting, consider
Streamlit Community Cloud, Render, Fly.io, or a container-based Vercel setup.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

import requests


STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
STREAMLIT_APP = os.getenv("STREAMLIT_APP", "app.py")


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.1)
        return sock.connect_ex((host, port)) == 0


_streamlit_proc: subprocess.Popen[str] | None = None


def _ensure_streamlit_started() -> None:
    global _streamlit_proc

    if _port_open("127.0.0.1", STREAMLIT_PORT):
        return

    if _streamlit_proc is not None and _streamlit_proc.poll() is None:
        return

    # Fail fast with a clear error if Vercel's vendoring missed transitive deps.
    try:
        from blinker import Signal  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Missing runtime dependency needed by Streamlit. "
            "Ensure `blinker` is in requirements.txt. "
            f"Import error: {e!r}"
        ) from e

    env = os.environ.copy()
    env.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    env.setdefault("STREAMLIT_BROWSER_GATHERUSAGESTATS", "false")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        STREAMLIT_APP,
        "--server.headless",
        "true",
        "--server.port",
        str(STREAMLIT_PORT),
        "--server.address",
        "127.0.0.1",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
    ]

    _streamlit_proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait briefly for Streamlit to come up
    deadline = time.time() + 8
    while time.time() < deadline:
        if _port_open("127.0.0.1", STREAMLIT_PORT):
            return
        time.sleep(0.05)

    # If it didn't start, surface logs to help diagnose deployment failures.
    output = ""
    if _streamlit_proc and _streamlit_proc.stdout:
        try:
            output = _streamlit_proc.stdout.read()[:4000]
        except Exception:
            output = ""

    raise RuntimeError(
        "Streamlit failed to start in time. "
        "Partial output:\n" + (output or "<no output>")
    )


def _proxy(method: str, path: str, headers: dict, body: bytes | None) -> tuple[int, list[tuple[str, str]], bytes]:
    url = f"http://127.0.0.1:{STREAMLIT_PORT}{path}"

    # Remove hop-by-hop headers / ones that confuse upstream
    hop_by_hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "host",
        "content-length",
    }

    upstream_headers = {
        k: v for k, v in headers.items() if k.lower() not in hop_by_hop
    }

    resp = requests.request(
        method,
        url,
        headers=upstream_headers,
        data=body,
        allow_redirects=False,
        stream=True,
        timeout=25,
    )

    out_headers: list[tuple[str, str]] = []
    for k, v in resp.headers.items():
        if k.lower() in hop_by_hop:
            continue
        out_headers.append((k, v))

    return resp.status_code, out_headers, resp.content


def app(environ, start_response):
    """Minimal WSGI app that proxies to the local Streamlit server."""

    _ensure_streamlit_started()

    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")
    qs = environ.get("QUERY_STRING")
    if qs:
        path = f"{path}?{qs}"

    headers = {}
    for k, v in environ.items():
        if k.startswith("HTTP_"):
            header_name = k[5:].replace("_", "-")
            headers[header_name] = v
    if environ.get("CONTENT_TYPE"):
        headers["Content-Type"] = environ["CONTENT_TYPE"]

    body = None
    try:
        length = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError:
        length = 0
    if length > 0:
        body = environ["wsgi.input"].read(length)

    status_code, out_headers, content = _proxy(method, path, headers, body)

    status_line = f"{status_code} {'OK' if status_code < 400 else 'ERROR'}"
    start_response(status_line, out_headers)
    return [content]
