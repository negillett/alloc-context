from __future__ import annotations

import argparse
import json
import sys

from alloccontext.config import load_config
from alloccontext.store.db import connect
from alloccontext_operator.brief.runner import run_brief
from alloccontext_operator.deliver.alerts import check_alerts
from alloccontext_operator.review.monthly import run_monthly_review


def cmd_brief(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if not args.stdout and not args.email:
        args.stdout = True
    try:
        result = run_brief(
            config,
            scope=args.period,
            stdout=args.stdout,
            email=args.email,
        )
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    if not args.stdout:
        print(json.dumps(result, indent=2))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if not args.stdout and not args.email:
        args.stdout = True
    conn = connect(config.paths.db)
    try:
        result = run_monthly_review(
            conn,
            config,
            month=args.month,
            stdout=args.stdout,
            email=args.email,
            apply=args.apply,
        )
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    finally:
        conn.close()
    if not args.stdout:
        print(json.dumps(result, indent=2))
    return 0


def cmd_alerts(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    conn = connect(config.paths.db)
    result = check_alerts(
        conn,
        config,
        email=args.email,
        stdout=args.stdout or not args.email,
    )
    conn.close()
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="alloc-context-operator")
    parser.add_argument("--config", default=None, help="Path to config YAML")
    sub = parser.add_subparsers(dest="command", required=True)

    brief_p = sub.add_parser("brief", help="Build and deliver a market brief")
    brief_p.add_argument("period", choices=["daily", "weekly"])
    brief_p.add_argument("--stdout", action="store_true")
    brief_p.add_argument("--email", action="store_true", help="Send brief via email")
    brief_p.set_defaults(func=cmd_brief)

    review_p = sub.add_parser("review", help="Review forward watches and brief quality")
    review_sub = review_p.add_subparsers(dest="review_kind", required=True)
    monthly_p = review_sub.add_parser("monthly", help="Monthly forward-watch review")
    monthly_p.add_argument(
        "--month",
        default=None,
        help="YYYY-MM (default: previous calendar month)",
    )
    monthly_p.add_argument("--stdout", action="store_true")
    monthly_p.add_argument("--email", action="store_true")
    monthly_p.add_argument(
        "--apply",
        action="store_true",
        help="Persist LLM prediction scores to the database",
    )
    monthly_p.set_defaults(func=cmd_review)

    alerts_p = sub.add_parser("alerts", help="Evaluate threshold alerts")
    alerts_p.add_argument("--stdout", action="store_true")
    alerts_p.add_argument("--email", action="store_true")
    alerts_p.set_defaults(func=cmd_alerts)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
