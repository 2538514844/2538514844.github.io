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


def repo_og_image(repo_name):
    """从 owner/repo 构造 GitHub OpenGraph 预览图 URL"""
    if "/" in repo_name:
        return f"https://opengraph.githubassets.com/1/{repo_name}"
    return ""


def parse_repo_md(filepath):
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


def read_file_content(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def main():
    if not os.path.exists(BACKUP_DIR):
        print("gen_rss: no BACKUP dir")
        return

    all_files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".md") and f != ".gitkeep"]
    )
    if not all_files:
        print("gen_rss: no .md files in BACKUP")
        return

    date_groups = OrderedDict()
    date_articles = OrderedDict()

    for filename in all_files:
        if filename.startswith("article_"):
            m = re.match(r"article_(\d{4}-\d{2}-\d{2})", filename)
            date = m.group(1) if m else ""
            date_articles[date] = filename
            if date not in date_groups:
                date_groups[date] = []
        else:
            m = re.match(r"\d+_(\d{4}-\d{2}-\d{2})", filename)
            date = m.group(1) if m else ""
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(filename)

    all_dates = sorted(set(list(date_groups.keys()) + list(date_articles.keys())), reverse=True)

    fg = FeedGenerator()
    fg.id(SITE_URL)
    fg.title(RSS_TITLE)
    fg.description(RSS_DESC)
    fg.language("zh-CN")
    fg.author({"name": "GitHub Scout"})
    fg.link(href=SITE_URL + "rss.xml", rel="self", type="application/rss+xml")
    fg.link(href=SITE_URL)

    for date in all_dates:
        article_file = date_articles.get(date)
        repo_files = date_groups.get(date, [])

        try:
            pub_time = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            pub_time = datetime.now()

        page_url = f"{SITE_URL}{date}/"

        if article_file:
            filepath = os.path.join(BACKUP_DIR, article_file)
            article_html = read_file_content(filepath)

            desc = f"{date} 每日精选 — {len(repo_files)} 个仓库"
            names = []
            for fname in repo_files[:8]:
                t, _, _, _ = parse_repo_md(os.path.join(BACKUP_DIR, fname))
                if t:
                    names.append(t)
            if names:
                desc += ": " + ", ".join(names)

            item = fg.add_entry(order="append")
            item.id(page_url)
            item.link(href=page_url)
            item.title(f"{date} 每日精选")
            item.description(desc)
            item.content(article_html, type="CDATA")
            item.published(pub_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        elif repo_files:
            html_parts = [f"<h1>{date} 每日精选</h1>", f"<p>共收录 {len(repo_files)} 个仓库</p>"]
            text_parts = [f"{date} 每日精选 — {len(repo_files)} 个仓库"]

            for fname in repo_files:
                fp = os.path.join(BACKUP_DIR, fname)
                title, url, stats, desc = parse_repo_md(fp)
                if not title:
                    continue

                og_url = repo_og_image(title)
                html_parts.append(f'<h2><a href="{url}">{title}</a></h2>')
                if og_url:
                    html_parts.append(f'<p><img src="{og_url}" alt="{title}" loading="lazy" style="max-width:100%;border-radius:8px;"></p>')
                if stats:
                    html_parts.append(f"<p>{stats}</p>")
                if desc:
                    html_parts.append(f"<blockquote>{desc}</blockquote>")
                html_parts.append(f'<p><a href="{url}">查看仓库</a></p>')
                text_parts.append(f"\n{title} — {desc}" if desc else f"\n{title}")

            item = fg.add_entry(order="append")
            item.id(page_url)
            item.link(href=page_url)
            item.title(f"{date} 每日精选")
            item.description(" | ".join(text_parts[:6]) + ("..." if len(text_parts) > 6 else ""))
            item.content("\n".join(html_parts), type="CDATA")
            item.published(pub_time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    fg.rss_file(RSS_FILENAME)
    article_count = len(date_articles)
    print(f"gen_rss: {len(all_dates)} days ({article_count} with AI article) -> {RSS_FILENAME}")


if __name__ == "__main__":
    main()
