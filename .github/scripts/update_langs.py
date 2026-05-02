#!/usr/bin/env python3
import os
import re
import sys
import requests

USER = os.environ["GH_USER"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README = "README.md"
TOP_N = 6
WIDTH = 25
FILLED, PARTIAL, EMPTY = "█", "▒", "░"

headers = {"Accept": "application/vnd.github+json"}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

repos, page = [], 1
while True:
    r = requests.get(
        f"https://api.github.com/users/{USER}/repos",
        params={"per_page": 100, "page": page, "type": "owner"},
        headers=headers,
        timeout=30,
    )
    r.raise_for_status()
    chunk = r.json()
    if not chunk:
        break
    repos.extend(chunk)
    page += 1

repos = [r for r in repos if not r["fork"] and not r["archived"]]

totals = {}
for repo in repos:
    r = requests.get(repo["languages_url"], headers=headers, timeout=30)
    r.raise_for_status()
    for lang, b in r.json().items():
        totals[lang] = totals.get(lang, 0) + b

if not totals:
    sys.exit("no languages found")

items = sorted(totals.items(), key=lambda x: -x[1])[:TOP_N]
total = sum(b for _, b in items)
name_w = max(len(n) for n, _ in items)

lines = []
for name, b in items:
    pct = b / total * 100
    raw = pct / 100 * WIDTH
    full = int(raw)
    rem = raw - full
    partial = PARTIAL if rem >= 0.5 else ""
    empty = EMPTY * (WIDTH - full - len(partial))
    bar = FILLED * full + partial + empty
    lines.append(f"{name:<{name_w}}   {bar}   {pct:5.2f} %")

block = "```text\n" + "\n".join(lines) + "\n```"

with open(README, "r", encoding="utf-8") as f:
    content = f.read()

new = re.sub(
    r"<!-- LANGS:START -->.*?<!-- LANGS:END -->",
    f"<!-- LANGS:START -->\n{block}\n<!-- LANGS:END -->",
    content,
    flags=re.DOTALL,
)

with open(README, "w", encoding="utf-8") as f:
    f.write(new)
