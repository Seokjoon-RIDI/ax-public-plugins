"""
Crawler template for web-crawl-script-builder skill.

Copy this file into `crawler/crawl_<site>.py` and fill in three site-specific
functions:
  - fetch_one(url, session) -> Response | dict
  - parse_one(response, url) -> dict
  - iter_inputs(input_path) -> Iterable[str]

Everything else (rate limit, retry, checkpointing, evidence dump, no-secrets
logging) is generic and should not need modification per site.

Run modes
---------
  # 10-row smoke test, with HTML evidence for first 3 rows
  uv run python crawl_<site>.py \
      --input input_urls.csv \
      --output outputs/sample_output.csv \
      --limit 10 --evidence 3

  # Full run with resume
  uv run python crawl_<site>.py \
      --input input_urls.csv \
      --output outputs/full.csv \
      --resume

Dependencies
------------
  uv pip install httpx tenacity pyyaml
  # add bs4 / lxml / selectolax / playwright as needed for the chosen strategy
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import random
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

import httpx
import yaml

# ---------------------------------------------------------------------------
# Logging — redact secrets so cookies/tokens never end up in stdout or log files
# ---------------------------------------------------------------------------

REDACT_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token"}


class SecretRedactingFormatter(logging.Formatter):
    """Strip values for sensitive header names if they appear in log records."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for h in REDACT_HEADERS:
            # case-insensitive replace of "<header>: <value>" up to next newline
            lower = msg.lower()
            i = 0
            while True:
                idx = lower.find(h + ":", i)
                if idx == -1:
                    break
                end = msg.find("\n", idx)
                if end == -1:
                    end = len(msg)
                msg = msg[:idx] + h + ": <REDACTED>" + msg[end:]
                lower = msg.lower()
                i = idx + len(h) + len(": <REDACTED>")
        return msg


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("crawler")
    logger.setLevel(logging.INFO)
    fmt = SecretRedactingFormatter("%(asctime)s | %(levelname)s | %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.handlers = [sh, fh]
    return logger


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class CrawlerConfig:
    rps: float = 1.0  # requests per second; default-polite
    timeout_s: float = 20.0
    max_retries: int = 5
    backoff_base_s: float = 1.0
    backoff_cap_s: float = 60.0
    user_agent: str = (
        "ax-team-crawler/0.1 (+contact: your-team@example.com) "
        "built with web-crawl-script-builder"
    )
    schema_required: list[str] = field(default_factory=list)
    schema_optional: list[str] = field(default_factory=list)


def load_config(path: Path) -> CrawlerConfig:
    if not path.exists():
        return CrawlerConfig()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return CrawlerConfig(
        rps=raw.get("rps", 1.0),
        timeout_s=raw.get("timeout_s", 20.0),
        max_retries=raw.get("max_retries", 5),
        backoff_base_s=raw.get("backoff_base_s", 1.0),
        backoff_cap_s=raw.get("backoff_cap_s", 60.0),
        user_agent=raw.get("user_agent", CrawlerConfig().user_agent),
        schema_required=list(raw.get("schema", {}).get("required", [])),
        schema_optional=list(raw.get("schema", {}).get("optional", [])),
    )


# ---------------------------------------------------------------------------
# Checkpoint — track which inputs have already been processed (success OR
# permanent failure) so --resume picks up where the last run left off.
# ---------------------------------------------------------------------------


def url_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


class Checkpoint:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.done: set[str] = set()
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    self.done.add(line)

    def has(self, url: str) -> bool:
        return url_key(url) in self.done

    def mark(self, url: str) -> None:
        k = url_key(url)
        if k in self.done:
            return
        self.done.add(k)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(k + "\n")


# ---------------------------------------------------------------------------
# Rate limit + retry/backoff
# ---------------------------------------------------------------------------


class RateLimiter:
    """Simple token-bucket-ish limiter sized for low RPS values."""

    def __init__(self, rps: float) -> None:
        self.min_interval = 1.0 / max(rps, 0.01)
        self._last_at = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delay = self._last_at + self.min_interval - now
        if delay > 0:
            time.sleep(delay)
        self._last_at = time.monotonic()


def backoff_delay(attempt: int, base: float, cap: float) -> float:
    """Exponential backoff with full jitter."""
    raw = min(cap, base * (2 ** attempt))
    return random.uniform(0, raw)


# ---------------------------------------------------------------------------
# Site-specific surface — FILL THESE IN
# ---------------------------------------------------------------------------


def iter_inputs(input_path: Path) -> Iterator[str]:
    """Yield URLs (or queries / IDs) from the input file.

    Default implementation: one URL per line in a CSV's first column.
    Replace if your input is structured differently.
    """
    with input_path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            val = row[0].strip()
            if val and not val.startswith("#"):
                yield val


def fetch_one(
    url: str,
    client: httpx.Client,
    cfg: CrawlerConfig,
) -> httpx.Response:
    """Site-specific fetch.

    Default: plain GET. Override if you need:
      - Browser rendering (call a Playwright helper here)
      - JSON API call with auth headers (read from os.environ)
      - Search-by-query instead of by-URL
    """
    return client.get(url, timeout=cfg.timeout_s)


def parse_one(response: httpx.Response, url: str) -> dict[str, Any]:
    """Site-specific parser.

    Returns a flat dict of {field_name: value}. Missing optional fields should
    be set to None (the schema validator will tolerate it). Missing required
    fields will be flagged as a parse failure for that row.

    Replace this stub with your actual selectors / JSON paths.
    """
    raise NotImplementedError(
        "parse_one is a stub. Implement field extraction per Phase 3 findings "
        "(see references/extraction_strategies.md)."
    )


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def validate(row: dict[str, Any], cfg: CrawlerConfig) -> tuple[bool, list[str]]:
    missing = [f for f in cfg.schema_required if not row.get(f)]
    return (not missing, missing)


# ---------------------------------------------------------------------------
# Evidence dump (HTML snapshot for the first N rows of a smoke test)
# ---------------------------------------------------------------------------


def dump_evidence(evidence_dir: Path, idx: int, url: str, response: httpx.Response) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    safe_idx = f"{idx:03d}"
    body_path = evidence_dir / f"{safe_idx}-{url_key(url)}.html"
    meta_path = evidence_dir / f"{safe_idx}-{url_key(url)}.meta.json"
    body_path.write_text(response.text, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "url": url,
                "status": response.status_code,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                # NOTE: response.headers is intentionally not included to avoid
                # ever persisting Set-Cookie or auth-related headers.
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


@dataclass
class RunStats:
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    rate_limited: int = 0
    skipped_resume: int = 0


def run(
    input_path: Path,
    output_path: Path,
    config_path: Path,
    failed_log_path: Path,
    checkpoint_path: Path,
    log_path: Path,
    evidence_dir: Path | None,
    evidence_n: int,
    limit: int | None,
    resume: bool,
) -> RunStats:
    cfg = load_config(config_path)
    log = setup_logger(log_path)
    rl = RateLimiter(cfg.rps)
    checkpoint = Checkpoint(checkpoint_path) if resume else None

    headers = {"User-Agent": cfg.user_agent}
    stats = RunStats()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    failed_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Stop signal handling — write checkpoint and exit cleanly on Ctrl-C
    stop = {"flag": False}

    def _handler(signum, frame):  # noqa: ARG001
        log.warning("Interrupt received; finishing current row and stopping.")
        stop["flag"] = True

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

    fieldnames: list[str] | None = None
    out_writer: csv.DictWriter | None = None
    out_file = output_path.open("a", encoding="utf-8", newline="")
    fail_file = failed_log_path.open("a", encoding="utf-8", newline="")
    fail_writer = csv.writer(fail_file)
    if failed_log_path.stat().st_size == 0:
        fail_writer.writerow(["url", "status", "reason"])

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        for idx, url in enumerate(iter_inputs(input_path)):
            if limit is not None and stats.attempted >= limit:
                break
            if checkpoint and checkpoint.has(url):
                stats.skipped_resume += 1
                continue
            if stop["flag"]:
                break
            stats.attempted += 1

            response = None
            for attempt in range(cfg.max_retries + 1):
                rl.wait()
                try:
                    response = fetch_one(url, client, cfg)
                except httpx.RequestError as e:
                    log.warning("fetch_error url=%s attempt=%d err=%s", url, attempt, e)
                    if attempt == cfg.max_retries:
                        fail_writer.writerow([url, "ERR", str(e)])
                        stats.failed += 1
                        if checkpoint:
                            checkpoint.mark(url)
                        response = None
                        break
                    time.sleep(backoff_delay(attempt, cfg.backoff_base_s, cfg.backoff_cap_s))
                    continue

                if response.status_code == 429:
                    stats.rate_limited += 1
                    retry_after = float(response.headers.get("Retry-After", "0") or 0)
                    delay = max(
                        retry_after,
                        backoff_delay(attempt, cfg.backoff_base_s, cfg.backoff_cap_s),
                    )
                    log.warning("rate_limited url=%s attempt=%d sleep=%.1fs", url, attempt, delay)
                    if attempt == cfg.max_retries:
                        fail_writer.writerow([url, 429, "rate_limited_after_retries"])
                        stats.failed += 1
                        if checkpoint:
                            checkpoint.mark(url)
                        break
                    time.sleep(delay)
                    continue

                if 500 <= response.status_code < 600:
                    if attempt == cfg.max_retries:
                        fail_writer.writerow([url, response.status_code, "server_5xx"])
                        stats.failed += 1
                        if checkpoint:
                            checkpoint.mark(url)
                        break
                    time.sleep(backoff_delay(attempt, cfg.backoff_base_s, cfg.backoff_cap_s))
                    continue

                if response.status_code >= 400:
                    fail_writer.writerow([url, response.status_code, "client_4xx"])
                    stats.failed += 1
                    if checkpoint:
                        checkpoint.mark(url)
                    response = None
                    break

                # 2xx — success
                break

            if response is None:
                continue

            # Evidence dump for the first N rows of a smoke test
            if evidence_dir is not None and stats.succeeded + stats.failed < evidence_n:
                try:
                    dump_evidence(evidence_dir, idx, url, response)
                except Exception as e:  # evidence is best-effort
                    log.warning("evidence_dump_failed url=%s err=%s", url, e)

            try:
                row = parse_one(response, url)
            except Exception as e:
                log.exception("parse_error url=%s", url)
                fail_writer.writerow([url, response.status_code, f"parse_error: {e}"])
                stats.failed += 1
                if checkpoint:
                    checkpoint.mark(url)
                continue

            ok, missing = validate(row, cfg)
            if not ok:
                log.warning("missing_required url=%s missing=%s", url, missing)
                fail_writer.writerow(
                    [url, response.status_code, f"missing_required: {missing}"]
                )
                stats.failed += 1
                if checkpoint:
                    checkpoint.mark(url)
                continue

            if out_writer is None:
                fieldnames = list(row.keys())
                # Append-mode: only write header if file is empty
                if output_path.stat().st_size == 0:
                    out_writer = csv.DictWriter(out_file, fieldnames=fieldnames)
                    out_writer.writeheader()
                else:
                    out_writer = csv.DictWriter(out_file, fieldnames=fieldnames)
            out_writer.writerow(row)
            out_file.flush()
            stats.succeeded += 1
            if checkpoint:
                checkpoint.mark(url)

    out_file.close()
    fail_file.close()

    log.info(
        "run_complete attempted=%d succeeded=%d failed=%d rate_limited=%d skipped_resume=%d",
        stats.attempted,
        stats.succeeded,
        stats.failed,
        stats.rate_limited,
        stats.skipped_resume,
    )
    return stats


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--config", default=Path("config.yaml"), type=Path)
    p.add_argument("--failed-log", default=Path("logs/failed_urls.csv"), type=Path)
    p.add_argument("--checkpoint", default=Path("logs/checkpoint.txt"), type=Path)
    p.add_argument("--log", default=Path("logs/run.log"), type=Path)
    p.add_argument("--evidence-dir", default=Path("evidence"), type=Path)
    p.add_argument(
        "--evidence",
        type=int,
        default=0,
        help="Dump HTML evidence for the first N successful rows (0 = off).",
    )
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()

    evidence_dir = args.evidence_dir if args.evidence > 0 else None

    stats = run(
        input_path=args.input,
        output_path=args.output,
        config_path=args.config,
        failed_log_path=args.failed_log,
        checkpoint_path=args.checkpoint,
        log_path=args.log,
        evidence_dir=evidence_dir,
        evidence_n=args.evidence,
        limit=args.limit,
        resume=args.resume,
    )
    return 0 if stats.failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
