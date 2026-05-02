# -*- coding: utf-8 -*-
"""从 BACKUP/*.md 按日期聚合生成每日 RSS"""
import os
import re
from collections import OrderedDict
from datetime import datetime

from feedgen.feed import FeedGenerator

BACKUP_DIR = "BACKUP"
RSS_FILENAME = "rss.xml"
RSS_TITLE = "GitHub Scout 每日精选"
RSS_DESC = "AI 精选 GitHub 热门仓库，每日更新"
SITE_URL = "https://2538514844.github.io/"


def parse_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    title = ""
    url = ""
    m = re.match(r"# \[(.+?)\]\((.+?)\)", content)
    if m:
        title = m.group(1)
        url = m.group(2)

    stats = ""
    stats_match = re.search(r"\n(⭐[^\n]+)\n", content)
    if stats_match:
        stats = stats_match.group(1)

    desc = ""
    desc_match = re.search(r"> ([^\n]+)", content)
    if desc_match:
        desc = desc_match.group(1)

    return title, url, stats, desc


def main():
    if not os.path.exists(BACKUP_DIR):
        print("gen_rss: no BACKUP dir")
        return

    md_files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".md") and f != ".gitkeep"]
    )
    if not md_files:
        print("gen_rss: no .md files in BACKUP")
        return

    date_groups = OrderedDict()
    for filename in md_files:
        date_match = re.match(r"\d+_(\d{4}-\d{2}-\d{2})", filename)
        date = date_match.group(1) if date_match else ""
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(filename)

    # 日期降序，最新在前
    date_groups = OrderedDict(
        sorted(date_groups.items(), key=lambda x: x[0], reverse=True)
    )

    fg = FeedGenerator()
    fg.id(SITE_URL)
    fg.title(RSS_TITLE)
    fg.description(RSS_DESC)
    fg.language("zh-CN")
    fg.author({"name": "GitHub Scout"})
    fg.link(href=SITE_URL + "rss.xml", rel="self", type="application/rss+xml")
    fg.link(href=SITE_URL)

    for date, files in date_groups.items():
        filepath = os.path.join(BACKUP_DIR, files[0])
        try:
            pub_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        except OSError:
            pub_time = datetime.strptime(date, "%Y-%m-%d")

        html_parts = [f"<h1>{date} 每日精选</h1>", f"<p>共收录 {len(files)} 个仓库</p>"]
        text_parts = [f"{date} 每日精选 — {len(files)} 个仓库"]

        for fname in files:
            fp = os.path.join(BACKUP_DIR, fname)
            title, url, stats, desc = parse_md(fp)
            html_parts.append(f'<h2><a href="{url}">{title}</a></h2>')
            if stats:
                html_parts.append(f"<p>{stats}</p>")
            if desc:
                html_parts.append(f"<blockquote>{desc}</blockquote>")
            html_parts.append(f'<p><a href="{url}">查看仓库</a></p>')
            text_parts.append(f"\n{title} — {desc}" if desc else f"\n{title}")

        page_url = f"{SITE_URL}{date}/"

        item = fg.add_entry(order="append")
        item.id(page_url)
        item.link(href=page_url)
        item.title(f"{date} 每日精选")
        item.description(" | ".join(text_parts[:6]) + ("..." if len(text_parts) > 6 else ""))
        item.content("\n".join(html_parts), type="CDATA")
        item.published(pub_time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    fg.rss_file(RSS_FILENAME)
    print(f"gen_rss: {len(date_groups)} days -> {RSS_FILENAME}")


if __name__ == "__main__":
    main()
