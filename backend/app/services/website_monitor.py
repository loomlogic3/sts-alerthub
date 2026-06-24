import time

import requests


def check_website(url: str) -> dict:
    start_time = time.perf_counter()

    try:
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
        )

        response_time_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "url": url,
            "reachable": True,
            "status_code": response.status_code,
            "ok": 200 <= response.status_code < 400,
            "response_time_ms": response_time_ms,
        }

    except Exception as exc:
        response_time_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "url": url,
            "reachable": False,
            "status_code": None,
            "ok": False,
            "response_time_ms": response_time_ms,
            "error": str(exc),
        }
