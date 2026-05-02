# -*- coding: utf-8 -*-
"""将 BACKUP/*.md 按日期聚合为 Zola content/ 每日页面"""
import os
import re
from collections import OrderedDict

BACKUP_DIR = "BACKUP"
OUTPUT_DIR = "output/content"


def repo_og_image(repo_name):
    """从 owner/repo 构造 GitHub OpenGraph 预览图 URL"""
    if "/" in repo_name:
        return f"https://opengraph.githubassets.com/1/{repo_name}"
    return ""


def parse_repo_md(filepath):
    """解析单个仓库 markdown 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    title = ""
    url = ""
    m = re.match(r"# \[(.+?)\]\((.+?)\)", content)
    if m:
        title = m.group(1)
        url = m.group(2)

    tags = []
    tag_match = re.search(r"## 标签\n\n(.+)", content)
    if tag_match:
        tags = re.findall(r"`([^`]+)`", tag_match.group(1))

    stats = ""
    stats_match = re.search(r"\n(⭐[^\n]+)\n", content)
    if stats_match:
        stats = stats_match.group(1)

    desc = ""
    desc_match = re.search(r"> ([^\n]+)", content)
    if desc_match:
        desc = desc_match.group(1)

    return title, url, tags, stats, desc


def read_file_content(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def main():
    if not os.path.exists(BACKUP_DIR):
        print("no BACKUP dir")
        return

    all_files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".md") and f != ".gitkeep"]
    )
    if not all_files:
        print("no .md files in BACKUP")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    date_groups = OrderedDict()       # date -> [repo_filenames]
    date_articles = OrderedDict()     # date -> article_filename or None

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

    with open(os.path.join(OUTPUT_DIR, "_index.md"), "w", encoding="utf-8") as f:
        f.write("+++\n")
        f.write('title = "index"\n')
        f.write('sort_by = "date"\n')
        f.write('paginate_by = 20\n')
        f.write("+++\n")

    for date in all_dates:
        article_file = date_articles.get(date)
        repo_files = date_groups.get(date, [])

        if article_file:
            filepath = os.path.join(BACKUP_DIR, article_file)
            body = read_file_content(filepath)
            title = f"{date} 每日精选"
            m = re.match(r"# (.+)", body)
            if m:
                title = m.group(1).strip()
            # 标签从仓库文件提取，不从 AI 文章全文提取（避免把代码片段当标签）
            tags = []
            for fname in repo_files:
                fp = os.path.join(BACKUP_DIR, fname)
                _, _, repo_tags, _, _ = parse_repo_md(fp)
                for t in repo_tags:
                    if t not in tags:
                        tags.append(t)
        elif repo_files:
            all_tags = OrderedDict()
            sections = []
            for filename in repo_files:
                filepath = os.path.join(BACKUP_DIR, filename)
                repo_title, url, tags, stats, desc = parse_repo_md(filepath)
                if not repo_title or not url:
                    continue
                for t in tags:
                    all_tags[t] = True

                og_url = repo_og_image(repo_title)
                section = f"## [{repo_title}]({url})\n\n"
                if og_url:
                    section += f'<p><img src="{og_url}" alt="{repo_title}" loading="lazy" style="max-width:100%;border-radius:8px;"></p>\n\n'
                if stats:
                    section += f"{stats}\n\n"
                if desc:
                    section += f"> {desc}\n\n"
                section += f"[查看仓库]({url})\n\n"
                sections.append(section)

            body = f"# {date} 每日精选\n\n"
            body += f"> 共收录 {len(repo_files)} 个仓库\n\n"
            body += "---\n\n".join(sections)
            tags = list(all_tags.keys())
            title = f"{date} 每日精选"
        else:
            continue

        escaped_title = title.replace('"', '\\"')
        frontmatter = "+++\n"
        frontmatter += f'title = "{escaped_title}"\n'
        frontmatter += f'date = "{date}"\n'
        if tags:
            frontmatter += "[taxonomies]\n"
            frontmatter += "tags = [" + ", ".join(f'"{t}"' for t in tags) + "]\n"
        frontmatter += "[extra]\n"
        frontmatter += "reactions = { thumbs_up = 0, thumbs_down = 0, laugh = 0, heart = 0, hooray = 0, confused = 0, rocket = 0, eyes = 0 }\n"
        frontmatter += "+++\n\n"

        zola_filename = f"{date}.md"
        zola_filepath = os.path.join(OUTPUT_DIR, zola_filename)

        with open(zola_filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter + body)

    article_count = len(date_articles)
    print(f"gen_zola: {len(all_files)} files -> {len(all_dates)} daily pages ({article_count} with AI article) -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
