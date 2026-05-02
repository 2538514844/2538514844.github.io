# -*- coding: utf-8 -*-
"""将 BACKUP/*.md 按日期合并为 Zola content/ 每日聚合页面"""
import os
import re
from collections import OrderedDict

BACKUP_DIR = "BACKUP"
OUTPUT_DIR = "output/content"


def parse_md(filepath):
    """解析单个仓库 markdown 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    title = ""
    url = ""
    m = re.match(r"# \[(.+?)\]\((.+?)\)", content)
    if m:
        title = m.group(1)
        url = m.group(2)
    else:
        m = re.match(r"# (.+)", content)
        if m:
            title = m.group(1).strip()

    tags = []
    tag_match = re.search(r"## 标签\n\n(.+)", content)
    if tag_match:
        tags = re.findall(r"`([^`]+)`", tag_match.group(1))

    # 提取统计行 (⭐ 2629 | 🍴 540 | Python | 2026-04-29)
    stats = ""
    stats_match = re.search(r"\n(⭐[^\n]+)\n", content)
    if stats_match:
        stats = stats_match.group(1)

    # 提取描述
    desc = ""
    desc_match = re.search(r"> ([^\n]+)", content)
    if desc_match:
        desc = desc_match.group(1)

    return title, url, tags, stats, desc


def main():
    if not os.path.exists(BACKUP_DIR):
        print("no BACKUP dir")
        return

    md_files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".md") and f != ".gitkeep"]
    )
    if not md_files:
        print("no .md files in BACKUP")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 按日期分组
    date_groups = OrderedDict()
    for filename in md_files:
        date_match = re.match(r"\d+_(\d{4}-\d{2}-\d{2})", filename)
        date = date_match.group(1) if date_match else ""
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(filename)

    # 日期降序
    date_groups = OrderedDict(
        sorted(date_groups.items(), key=lambda x: x[0], reverse=True)
    )

    # 创建 _index.md（Zola section 入口）
    with open(os.path.join(OUTPUT_DIR, "_index.md"), "w", encoding="utf-8") as f:
        f.write("+++\n")
        f.write('title = "index"\n')
        f.write('sort_by = "date"\n')
        f.write('paginate_by = 20\n')
        f.write("+++\n")

    for date, files in date_groups.items():
        all_tags = OrderedDict()
        sections = []

        for filename in files:
            filepath = os.path.join(BACKUP_DIR, filename)
            title, url, tags, stats, desc = parse_md(filepath)
            for t in tags:
                all_tags[t] = True

            section = f"## [{title}]({url})\n\n"
            if stats:
                section += f"{stats}\n\n"
            if desc:
                section += f"> {desc}\n\n"
            section += f"[查看仓库]({url})\n\n"
            sections.append(section)

        body = f"# {date} 每日精选\n\n"
        body += f"> 共收录 {len(files)} 个仓库\n\n"
        body += "---\n\n".join(sections)

        unique_tags = list(all_tags.keys())

        escaped_date = date.replace('"', '\\"')
        frontmatter = "+++\n"
        frontmatter += f'title = "{date} 每日精选"\n'
        frontmatter += f'date = "{escaped_date}"\n'
        if unique_tags:
            frontmatter += "[taxonomies]\n"
            frontmatter += "tags = [" + ", ".join(f'"{t}"' for t in unique_tags) + "]\n"
        frontmatter += "[extra]\n"
        frontmatter += "reactions = { thumbs_up = 0, thumbs_down = 0, laugh = 0, heart = 0, hooray = 0, confused = 0, rocket = 0, eyes = 0 }\n"
        frontmatter += "+++\n\n"

        zola_filename = f"{escaped_date}.md"
        zola_filepath = os.path.join(OUTPUT_DIR, zola_filename)

        with open(zola_filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter + body)

    print(f"gen_zola: {len(md_files)} repos -> {len(date_groups)} daily pages -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
