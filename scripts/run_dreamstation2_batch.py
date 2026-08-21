"""Send a sequential batch of DreamStation 2 questions to the local /ask API.

The API's RequestLogContext writes one JSON record per request to
logs/app.jsonl, so this script is useful for producing realistic log data.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


QUESTIONS = [
    "How do I set up my DreamStation 2 for the first night?",
    "How should I clean the DreamStation 2 humidifier water tank?",
    "What does a red light on a DreamStation 2 indicate?",
    "How do I replace the filter in a DreamStation 2?",
]


def ask(base_url: str, question: str, timeout: float) -> dict:
    request = Request(
        f"{base_url.rstrip('/')}/ask",
        data=json.dumps({"question": question}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait after each completed request.",
    )
    args = parser.parse_args()

    for number, question in enumerate(QUESTIONS, start=1):
        print(f"[{number}/{len(QUESTIONS)}] {question}", flush=True)
        try:
            response = ask(args.base_url, question, args.timeout)
        except HTTPError as exc:
            print(f"  HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}")
        except URLError as exc:
            print(f"  Request failed: {exc.reason}")
        except TimeoutError:
            print(f"  Request timed out after {args.timeout:g} seconds")
        else:
            print(json.dumps(response, indent=2, ensure_ascii=False))

        if number < len(QUESTIONS):
            time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    sys.exit(main())
