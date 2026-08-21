"""
Grounding evaluation script for the Philips Product Knowledge AI Agent.

Runs a labeled eval set (tests/eval_set.json) through the live /ask endpoint
and reports:
  - Citation-presence rate (did in-scope answers come back with sources?)
  - Refusal rate (did out-of-scope questions correctly get refused?)
  - Precision@k (does the expected document appear in the returned sources?)

Also supports sweeping SIMILARITY_THRESHOLD across several values to help
justify the chosen threshold quantitatively, per the README's confidence
gating design.

ASSUMPTIONS (adjust to match your actual implementation):
  1. The server is already running (e.g. `uvicorn main:app --reload`) and
     reachable at BASE_URL. This script does not start/stop the server.
  2. POST /ask accepts {"question": "..."} and returns:
       {
         "answer": str,
         "confidence_score": float,
         "sources": [
           {"document": str, "page": int, "chunk_id": str,
            "similarity_score": float}
         ]
       }
     per the README's documented response shape. If your Answer/Citation
     agents use different field names, update `extract_sources()` below.
  3. A "refusal" is detected by empty `sources` AND/OR an `answer` field
     that is empty / matches known refusal phrasing. Update
     `is_refusal()` if your Validation Agent has an explicit
     `"refused": true` flag or a status code — that would be more robust
     than string matching and is the preferred fix if available.
  4. To sweep SIMILARITY_THRESHOLD, this script assumes the endpoint reads
     the threshold from environment/config at request time and that you
     can override it per-run (e.g. by restarting the server with a
     different .env value, or via an optional `?threshold=` query param
     if you add one). See run_threshold_sweep() for where to wire this in.

Usage:
    python tests/eval_grounding.py
    python tests/eval_grounding.py --base-url http://127.0.0.1:8000
    python tests/eval_grounding.py --sweep 0.60 0.65 0.70 0.75 0.80 0.85
    python tests/eval_grounding.py --eval-set tests/eval_set.json --out logs/eval_report.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("This script requires `requests`. Install with: pip install requests")
    sys.exit(1)


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_EVAL_SET = Path(__file__).parent / "eval_set.json"
ASK_ENDPOINT = "/ask"
REQUEST_TIMEOUT_S = 60

# Phrases that suggest a refusal when `sources` is ambiguous. Prefer an
# explicit "refused" flag from the API over this if you add one.
REFUSAL_PHRASES = [
    "don't have enough information",
    "cannot find this in",
    "not covered in the provided",
    "unable to answer",
    "no relevant information",
    "insufficient confidence",
]


@dataclass
class CaseResult:
    id: str
    question: str
    scope: str  # "in_scope" | "out_of_scope"
    expected_document: str | None
    expected_page: int | None
    confidence_score: float | None
    sources: list[dict[str, Any]] = field(default_factory=list)
    refused: bool = False
    error: str | None = None
    latency_s: float | None = None

    @property
    def cited(self) -> bool:
        return len(self.sources) > 0

    @property
    def hit_at_k(self) -> bool | None:
        """True if expected_document appears among returned sources.
        None if not applicable (out-of-scope case, or no expected doc)."""
        if self.scope != "in_scope" or not self.expected_document:
            return None
        return any(
            s.get("document") == self.expected_document for s in self.sources
        )


def load_eval_set(path: Path) -> dict[str, list[dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_comment", None)
    return data


def is_refusal(answer: str, sources: list[dict[str, Any]]) -> bool:
    """Heuristic refusal detector. Replace with an explicit API flag
    (e.g. response["refused"]) if/when the Validation Agent exposes one —
    that will be far more reliable than string matching."""
    if not sources:
        return True
    lowered = (answer or "").lower()
    return any(phrase in lowered for phrase in REFUSAL_PHRASES)


def extract_sources(response_json: dict[str, Any]) -> list[dict[str, Any]]:
    return response_json.get("sources", []) or []


def call_ask(base_url: str, question: str) -> tuple[dict[str, Any] | None, str | None, float]:
    """Returns (response_json, error, latency_seconds)."""
    start = time.time()
    try:
        resp = requests.post(
            f"{base_url}{ASK_ENDPOINT}",
            json={"question": question},
            timeout=REQUEST_TIMEOUT_S,
        )
        latency = time.time() - start
        resp.raise_for_status()
        return resp.json(), None, latency
    except requests.exceptions.RequestException as e:
        return None, str(e), time.time() - start


def run_case(base_url: str, scope: str, case: dict[str, Any]) -> CaseResult:
    result = CaseResult(
        id=case["id"],
        question=case["question"],
        scope=scope,
        expected_document=case.get("expected_document"),
        expected_page=case.get("expected_page"),
        confidence_score=None,
    )

    response_json, error, latency = call_ask(base_url, case["question"])
    result.latency_s = latency

    if error:
        result.error = error
        return result

    result.confidence_score = response_json.get("confidence_score")
    result.sources = extract_sources(response_json)
    result.refused = is_refusal(response_json.get("answer", ""), result.sources)
    return result


def run_eval(base_url: str, eval_set: dict[str, list[dict[str, Any]]]) -> list[CaseResult]:
    results: list[CaseResult] = []
    for scope in ("in_scope", "out_of_scope"):
        for case in eval_set.get(scope, []):
            print(f"  [{scope}] {case['id']}: {case['question'][:70]}...")
            results.append(run_case(base_url, scope, case))
    return results


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    in_scope = [r for r in results if r.scope == "in_scope"]
    out_scope = [r for r in results if r.scope == "out_of_scope"]
    errored = [r for r in results if r.error]

    usable_in_scope = [r for r in in_scope if not r.error]
    usable_out_scope = [r for r in out_scope if not r.error]

    citation_presence_rate = (
        sum(1 for r in usable_in_scope if r.cited) / len(usable_in_scope)
        if usable_in_scope else None
    )

    # Refusal rate is reported for BOTH pools:
    #  - out_of_scope refusal rate should be HIGH (ideally 1.0) — correct behavior
    #  - in_scope refusal rate should be LOW (ideally 0.0) — false refusals
    out_scope_refusal_rate = (
        sum(1 for r in usable_out_scope if r.refused) / len(usable_out_scope)
        if usable_out_scope else None
    )
    in_scope_refusal_rate = (
        sum(1 for r in usable_in_scope if r.refused) / len(usable_in_scope)
        if usable_in_scope else None
    )

    precision_cases = [r for r in usable_in_scope if r.hit_at_k is not None]
    precision_at_k = (
        sum(1 for r in precision_cases if r.hit_at_k) / len(precision_cases)
        if precision_cases else None
    )

    confidences = [
        r.confidence_score for r in usable_in_scope
        if isinstance(r.confidence_score, (int, float))
    ]

    return {
        "total_cases": len(results),
        "in_scope_count": len(in_scope),
        "out_of_scope_count": len(out_scope),
        "errored_count": len(errored),
        "citation_presence_rate": citation_presence_rate,
        "out_of_scope_refusal_rate": out_scope_refusal_rate,
        "in_scope_false_refusal_rate": in_scope_refusal_rate,
        "precision_at_k": precision_at_k,
        "avg_confidence_in_scope": statistics.mean(confidences) if confidences else None,
        "avg_latency_s": statistics.mean(
            r.latency_s for r in results if r.latency_s is not None
        ) if results else None,
    }


def format_pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def format_report(
    summary: dict[str, Any],
    results: list[CaseResult],
    eval_set_path: Path,
    base_url: str,
) -> str:
    lines = []
    lines.append("# Grounding Evaluation Report")
    lines.append("")
    lines.append(f"- **Generated:** {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- **Eval set:** `{eval_set_path}`")
    lines.append(f"- **Target:** `{base_url}{ASK_ENDPOINT}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value | Target |")
    lines.append("|---|---|---|")
    lines.append(f"| Citation-presence rate (in-scope) | {format_pct(summary['citation_presence_rate'])} | 100% |")
    lines.append(f"| Refusal rate (out-of-scope) | {format_pct(summary['out_of_scope_refusal_rate'])} | 100% |")
    lines.append(f"| False-refusal rate (in-scope) | {format_pct(summary['in_scope_false_refusal_rate'])} | 0% |")
    lines.append(f"| Precision@k (expected doc in sources) | {format_pct(summary['precision_at_k'])} | as high as possible |")
    avg_conf = summary["avg_confidence_in_scope"]
    lines.append(f"| Avg. confidence (in-scope) | {'n/a' if avg_conf is None else f'{avg_conf:.3f}'} | > SIMILARITY_THRESHOLD |")
    avg_lat = summary["avg_latency_s"]
    lines.append(f"| Avg. latency | {'n/a' if avg_lat is None else f'{avg_lat:.2f}s'} | — |")
    lines.append(f"| Errored requests | {summary['errored_count']} / {summary['total_cases']} | 0 |")
    lines.append("")

    lines.append("## Per-case detail")
    lines.append("")
    lines.append("| ID | Scope | Confidence | Cited? | Refused? | Doc Match | Question |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        if r.error:
            lines.append(f"| {r.id} | {r.scope} | ERROR | — | — | — | {r.question[:50]}... (`{r.error}`) |")
            continue
        conf = f"{r.confidence_score:.3f}" if isinstance(r.confidence_score, (int, float)) else "n/a"
        hit = r.hit_at_k
        hit_str = "—" if hit is None else ("✅" if hit else "❌")
        lines.append(
            f"| {r.id} | {r.scope} | {conf} | {'yes' if r.cited else 'no'} | "
            f"{'yes' if r.refused else 'no'} | {hit_str} | {r.question[:60]} |"
        )
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- `out_of_scope_refusal_rate` below 100% means the confidence gate is "
        "letting unsupported questions through — check whether SIMILARITY_THRESHOLD "
        "is too low, or whether irrelevant chunks are scoring above it."
    )
    lines.append(
        "- `in_scope_false_refusal_rate` above 0% means the gate is too strict — "
        "check chunking quality and whether the expected document was actually "
        "ingested before raising the threshold further."
    )
    lines.append(
        "- Precision@k failures with `cited=yes` indicate retrieval returned "
        "sources, just not the *expected* one — worth eyeballing whether the "
        "expected-document label is still correct as manuals get updated."
    )
    lines.append("")
    return "\n".join(lines)


def run_threshold_sweep(
    base_url: str,
    eval_set: dict[str, list[dict[str, Any]]],
    thresholds: list[float],
) -> str:
    """
    Sweeps SIMILARITY_THRESHOLD and reports refusal-rate vs. accuracy tradeoff
    at each value, to help justify the chosen threshold quantitatively.

    IMPORTANT: this script does NOT change the threshold for you. The /ask
    endpoint reads SIMILARITY_THRESHOLD from app/utils/config.py / .env at
    startup (per the README), so to actually sweep values you need to either:
      (a) restart the server between runs with a different .env value, or
      (b) add a temporary `?threshold=` override to the /ask route (and the
          Confidence Agent's gating check) for eval purposes only, then
          remove it before shipping.
    This function assumes (a): re-run this script once per threshold with
    the server restarted, and it will label each run in the combined report.
    For convenience it will just re-run against whatever threshold the
    server is CURRENTLY configured with, and record it under the requested
    label — you supply the thresholds list to label each pass correctly.
    """
    lines = ["# Threshold Sweep", "", (
        "Each row below corresponds to one `--sweep` value. Restart the "
        "server with SIMILARITY_THRESHOLD set to that value in .env before "
        "this script proceeds to the next one — it will prompt between runs."
    ), ""]
    lines.append("| Threshold | Citation Presence | OOS Refusal Rate | In-Scope False Refusal | Precision@k |")
    lines.append("|---|---|---|---|---|")

    for t in thresholds:
        input(
            f"\n>>> Set SIMILARITY_THRESHOLD={t} in .env, restart the server, "
            f"then press Enter to run this pass..."
        )
        print(f"Running eval pass for threshold={t} ...")
        results = run_eval(base_url, eval_set)
        summary = summarize(results)
        lines.append(
            f"| {t} | {format_pct(summary['citation_presence_rate'])} | "
            f"{format_pct(summary['out_of_scope_refusal_rate'])} | "
            f"{format_pct(summary['in_scope_false_refusal_rate'])} | "
            f"{format_pct(summary['precision_at_k'])} |"
        )

    lines.append("")
    lines.append(
        "Pick the threshold that maximizes OOS refusal rate and precision@k "
        "while keeping in-scope false-refusal rate near zero. Document the "
        "chosen value and this table in the README's Configuration section."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Grounding evaluation for /ask")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_SET)
    parser.add_argument("--out", type=Path, default=Path("logs/eval_report.md"))
    parser.add_argument(
        "--sweep",
        nargs="+",
        type=float,
        default=None,
        help="List of SIMILARITY_THRESHOLD values to sweep, e.g. --sweep 0.65 0.70 0.75 0.80",
    )
    args = parser.parse_args()

    eval_set = load_eval_set(args.eval_set)
    total_cases = len(eval_set.get("in_scope", [])) + len(eval_set.get("out_of_scope", []))
    if total_cases < 20:
        print(
            f"⚠️  Eval set has only {total_cases} cases. The task calls for "
            f"20–30 labeled pairs — fill out tests/eval_set.json before "
            f"treating results as representative.\n"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)

    if args.sweep:
        report = run_threshold_sweep(args.base_url, eval_set, args.sweep)
    else:
        print(f"Running {total_cases} cases against {args.base_url}{ASK_ENDPOINT} ...\n")
        results = run_eval(args.base_url, eval_set)
        summary = summarize(results)
        report = format_report(summary, results, args.eval_set, args.base_url)

        print("\n" + "=" * 60)
        print(f"Citation-presence rate:      {format_pct(summary['citation_presence_rate'])}")
        print(f"Out-of-scope refusal rate:   {format_pct(summary['out_of_scope_refusal_rate'])}")
        print(f"In-scope false-refusal rate: {format_pct(summary['in_scope_false_refusal_rate'])}")
        print(f"Precision@k:                 {format_pct(summary['precision_at_k'])}")
        print(f"Errored requests:            {summary['errored_count']} / {summary['total_cases']}")
        print("=" * 60)

    args.out.write_text(report, encoding="utf-8")
    print(f"\nReport written to {args.out}")


if __name__ == "__main__":
    main()