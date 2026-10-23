#!/usr/bin/env python3
"""CRAP (Change Risk Anti-Patterns) report generator.

Читает cc.json (radon cc -j -O cc.json) и coverage.json (coverage json -o coverage.json)
и печатает отсортированную таблицу CRAP по функциям + Max/Avg.

Формула: CRAP = comp^2 * (1 - cov)^3 + comp
"""
import argparse
import json
import os
import sys


# ---------- ANSI ----------
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'


def crap_color(value: float) -> str:
    if value < 10:
        return C.GREEN
    if value < 30:
        return C.YELLOW
    return C.RED


def paint(text: str, code: str, enabled: bool) -> str:
    return f"{code}{text}{C.RESET}" if enabled else text


# ---------- IO ----------
def load_json(path: str, hint: str):
    try:
        with open(path) as f:
            return json.load(f)
    except OSError:
        print(f"Файл {path} не найден, выполни команды:\n")
        print(hint)
        sys.exit(1)


def resolve_coverage_key(filename: str, coverage_files: dict):
    if filename in coverage_files:
        return filename
    lookup = {os.path.basename(k): k for k in coverage_files}
    return lookup.get(os.path.basename(filename))


# ---------- rendering ----------
def render_console(rows: list, use_color: bool) -> None:
    if not rows:
        print("Нет данных для отчёта CRAP")
        return

    func_w = min(max(len("Function"), max(len(r["func"]) for r in rows)), 70)

    header = (
        f"{'#':>3}  {'Function':<{func_w}}  "
        f"{'CRAP':>8}  {'Comp':>5}  {'Cov%':>6}"
    )
    print(paint(header, C.BOLD, use_color))
    print("─" * len(header))

    for i, r in enumerate(rows, 1):
        name = r["func"]
        if len(name) > func_w:
            name = "…" + name[-(func_w - 1):]

        crap_s = paint(f"{r['crap']:>8.2f}", crap_color(r["crap"]), use_color)
        print(
            f"{i:>3}  {name:<{func_w}}  "
            f"{crap_s}  {r['comp']:>5}  {r['cov'] * 100:>5.0f}%"
        )


def render_markdown(rows: list) -> None:
    print("| # | Function | CRAP | Comp | Coverage |")
    print("|---:|---|---:|---:|---:|")
    for i, r in enumerate(rows, 1):
        print(
            f"| {i} | `{r['func']}` | {r['crap']:.2f} | "
            f"{r['comp']} | {r['cov'] * 100:.0f}% |"
        )


def render_json(rows: list) -> None:
    payload = {
        "functions": [
            {
                "function": r["func"],
                "crap": round(r["crap"], 2),
                "complexity": r["comp"],
                "coverage": round(r["cov"], 4),
            }
            for r in rows
        ],
        "stats": {
            "count": len(rows),
            "max_crap": round(max((r["crap"] for r in rows), default=0), 2),
            "avg_crap": round(
                sum(r["crap"] for r in rows) / len(rows), 2
            ) if rows else 0,
        },
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def print_stats(rows: list, use_color: bool) -> None:
    if not rows:
        print("\nНет данных для расчёта статистики CRAP")
        return

    values = [r["crap"] for r in rows]
    avg = sum(values) / len(values)
    mx = max(values)

    sep = "=" * 20
    print("\n" + sep)
    print(f"  Max CRAP : {paint(f'{mx:.2f}', crap_color(mx), use_color)}")
    print(f"  Avg CRAP : {paint(f'{avg:.2f}', crap_color(avg), use_color)}")
    print(f"  Functions: {len(values)}")
    print(sep)


# ---------- main ----------
def main() -> None:
    ap = argparse.ArgumentParser(description="CRAP report from cc.json + coverage.json")
    ap.add_argument("--cc", default="cc.json")
    ap.add_argument("--coverage", default="coverage.json")
    ap.add_argument("--format", choices=["console", "md", "json"], default="console")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument(
        "--threshold", type=float, default=None,
        help="exit 1, если Max CRAP превышает порог (для CI)",
    )
    args = ap.parse_args()

    use_color = sys.stdout.isatty() and not args.no_color

    cc_data = load_json(args.cc, "radon cc . -j -O cc.json\n")
    coverage_data = load_json(
        args.coverage,
        "coverage run --branch -m pytest\ncoverage json -o coverage.json\n",
    )

    coverage_files = coverage_data.get("files", {})
    rows = []

    for filename, methods in cc_data.items():
        if filename.startswith("test_") or filename.startswith("tests/") or "calc_crap.py" in filename:
            continue

        cov_key = resolve_coverage_key(filename, coverage_files)
        if cov_key is None:
            # сообщение только для console-режима, чтобы не портить md/json
            if args.format == "console":
                print(
                    f"Файл {filename} не найден в отчёте о покрытии. Пропускаю...",
                    file=sys.stderr,
                )
            continue

        cov = coverage_files[cov_key]["summary"]["percent_covered"] / 100

        for method in methods:
            comp = method["complexity"]
            crap = comp ** 2 * (1 - cov) ** 3 + comp
            rows.append({
                "func": f"{filename}::{method['name']}",
                "comp": comp,
                "cov": cov,
                "crap": crap,
            })

    rows.sort(key=lambda r: r["crap"], reverse=True)

    if args.format == "console":
        render_console(rows, use_color)
        print_stats(rows, use_color)
    elif args.format == "md":
        render_markdown(rows)
        print_stats(rows, use_color=False)
    else:
        render_json(rows)

    if args.threshold is not None and rows:
        if max(r["crap"] for r in rows) > args.threshold:
            sys.exit(1)


if __name__ == "__main__":
    main()