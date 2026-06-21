import requests


def check_website(url: str) -> dict:
    try:
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
        )

        return {
            "url": url,
            "reachable": True,
            "status_code": response.status_code,
            "ok": 200 <= response.status_code < 400,
        }

    except Exception as exc:
        return {
            "url": url,
            "reachable": False,
            "status_code": None,
            "ok": False,
            "error": str(exc),
        }
