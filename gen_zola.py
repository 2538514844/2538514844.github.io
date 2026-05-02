# -*- coding: utf-8 -*-
"""将 BACKUP/*.md 转为 Zola content/ 格式，替代 isite"""
import os
import re
import sys

BACKUP_DIR = "BACKUP"
OUTPUT_DIR = "output/content"


def parse_md(filepath):
    """解析 markdown 文件，提取标题、日期、内容"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    title = ""
    # 提取 # [title](url) 格式的标题
    m = re.match(r"# \[(.+?)\]\((.+?)\)", content)
    if m:
        title = m.group(1)
    else:
        m = re.match(r"# (.+)", content)
        if m:
            title = m.group(1).strip()

    # 从内容中提取标签
    tags = []
    tag_match = re.search(r"## 标签\n\n(.+)", content)
    if tag_match:
        tags = re.findall(r"`([^`]+)`", tag_match.group(1))

    # 从文件名提取日期
    filename = os.path.basename(filepath)
    date_match = re.match(r"(\d+)_(\d{4}-\d{2}-\d{2})", filename)
    date = date_match.group(2) if date_match else ""

    return title, date, tags, content


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

    for filename in md_files:
        filepath = os.path.join(BACKUP_DIR, filename)
        title, date, tags, content = parse_md(filepath)

        # Zola frontmatter
        frontmatter = "+++\n"
        frontmatter += f'title = "{title}"\n'
        if date:
            frontmatter += f'date = "{date}"\n'
        if tags:
            frontmatter += "[taxonomies]\n"
            frontmatter += "tags = [" + ", ".join(f'"{t}"' for t in tags) + "]\n"
        frontmatter += "+++\n\n"

        # Zola 页面文件名：用 title 做 slug
        slug = re.sub(r"[<>:\"/\\|?*# ]", "-", title).strip("-").lower()
        zola_filename = f"{date}_{slug}.md" if date else f"{slug}.md"
        zola_filepath = os.path.join(OUTPUT_DIR, zola_filename)

        with open(zola_filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter + content)

    print(f"gen_zola: {len(md_files)} files -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
