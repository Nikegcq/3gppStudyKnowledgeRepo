#!/usr/bin/env python3
"""微信公众号文章抓取 -> Obsidian 笔记。

用法：
    python3 scripts/capture_wechat.py <链接或本地 HTML 文件> [更多来源...]
    python3 scripts/capture_wechat.py <链接> --images
    python3 scripts/capture_wechat.py <链接> --output-dir /tmp/test

- 来源可以是 mp.weixin.qq.com 链接，也可以是本地已保存的 HTML 文件
  （后者用于批量导入历史文章）。
- 默认不下载图片，笔记中保留原文图片 URL；加 --images 会把图片下载到
  90-Attachments/ 并改为本地引用（注意该目录默认不进 Git）。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List, Optional


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
VAULT = SCRIPT_DIR.parent
DEFAULT_OUTPUT = VAULT / "30-Resources" / "公众号收藏"
ATTACHMENTS = VAULT / "90-Attachments"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
WECHAT_REFERER = "https://mp.weixin.qq.com/"


def fetch_text(source: str) -> str:
    """抓取链接或读取本地 HTML 文件，返回解码后的文本。"""
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(
            source,
            headers={"User-Agent": UA, "Referer": WECHAT_REFERER},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    else:
        raw = pathlib.Path(source).read_bytes()

    match = re.search(rb"charset=[\"']?([\w-]+)", raw[:4096], re.I)
    encoding = match.group(1).decode("ascii", "ignore") if match else "utf-8"
    try:
        return raw.decode(encoding, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


class MetaCollector(HTMLParser):
    """收集页面中 <meta property/name=... content=...>。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.metas: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "meta":
            return
        data = {k.lower(): v for k, v in attrs}
        key = data.get("property") or data.get("name")
        content = data.get("content")
        if key and content:
            self.metas[key.lower()] = content


def js_var(page: str, name: str) -> str:
    """读取页面里形如 var name = "..." 的公众号变量。"""
    for pattern in (
        rf'var\s+{name}\s*=\s*"([^"]*)"\s*;',
        rf"var\s+{name}\s*=\s*'([^']*)'\s*;",
        rf'{name}\s*=\s*"([^"]*)"\s*;',
    ):
        found = re.search(pattern, page, re.S)
        if found:
            return html.unescape(found.group(1)).strip()
    return ""


def element_text(page: str, element_id: str, max_len: int = 300) -> str:
    """取出 id=element_id 的元素文本（去掉内层标签）。"""
    pattern = (
        rf'<[^>]+id=["\']{re.escape(element_id)}["\'][^>]*>'
        rf"([\s\S]{{0,{max_len}}}?)</(?:a|span|em|h1|h2|h3|p)>"
    )
    found = re.search(pattern, page, re.I)
    if not found:
        return ""
    text = re.sub(r"<[^>]+>", "", found.group(1))
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def extract_content(page: str) -> str:
    """截取 <div id="js_content"> 包裹的正文 HTML。"""
    start = re.search(r'<div[^>]*id=["\']js_content["\'][^>]*>', page, re.S)
    if not start:
        return ""
    depth = 1
    scanner = re.compile(r"<!--.*?-->|</?div\b[^>]*>", re.S)
    for token in scanner.finditer(page, start.end()):
        piece = token.group(0)
        if piece.startswith("<!--"):
            continue
        if piece.startswith("</"):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return page[start.start() : token.end()]
    return ""


class HTMLToMarkdown(HTMLParser):
    """极简 HTML -> Markdown 转换，专为公众号正文优化。"""

    HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: List[str] = [""]
        self.skip_depth = 0
        self.heading_buf: List[str] = []
        self.heading_level = 0
        self.in_code = False
        self.in_li = False

    def new_block(self) -> None:
        if self.blocks[-1] != "":
            self.blocks.append("")

    def handle_starttag(self, tag: str, attrs) -> None:
        attr = {k.lower(): v for k, v in attrs}
        if tag in ("script", "style"):
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "img":
            src = attr.get("data-src") or attr.get("data-original") or attr.get("src") or ""
            alt = html.unescape(attr.get("alt") or "")
            if src:
                self.new_block()
                self.blocks[-1] += f"![{alt}]({html.unescape(src)})"
                self.new_block()
            return
        if tag in self.HEADINGS:
            self.heading_level = self.HEADINGS[tag]
            self.heading_buf = []
            return
        if tag == "li":
            self.new_block()
            self.blocks[-1] += "- "
            self.in_li = True
            return
        if tag == "br":
            self.new_block()
            return
        if tag == "pre":
            self.in_code = True
            self.new_block()
            return
        if tag in ("p", "div", "section", "blockquote", "ul", "ol", "table", "tr"):
            self.new_block()
        if tag == "hr":
            self.new_block()
            self.blocks[-1] += "---"
            self.new_block()

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            if self.skip_depth:
                self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in self.HEADINGS and self.heading_level:
            text = "".join(self.heading_buf).strip()
            if text:
                self.new_block()
                self.blocks[-1] += "#" * self.heading_level + " " + text
                self.new_block()
            self.heading_level = 0
            self.heading_buf = []
            return
        if tag == "li":
            self.in_li = False
            self.new_block()
            return
        if tag == "pre":
            self.in_code = False
            self.new_block()
            return
        if tag in ("p", "div", "section", "blockquote", "ul", "ol", "table", "tr"):
            self.new_block()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.heading_level:
            self.heading_buf.append(data)
            return
        text = data if self.in_code else re.sub(r"[ \t\r\f\v]+", " ", data)
        if text == "":
            return
        if self.in_li and self.blocks[-1].endswith("- "):
            self.blocks[-1] += text.lstrip()
        elif self.in_code:
            self.blocks[-1] += text
        else:
            self.blocks[-1] += text


def to_markdown(content_html: str) -> str:
    parser = HTMLToMarkdown()
    parser.feed(content_html)
    blocks = [b.strip() for b in parser.blocks if b.strip()]
    if not blocks:
        return ""
    text = blocks[0]
    for block in blocks[1:]:
        last_line = text.splitlines()[-1]
        if block.startswith("- ") and last_line.startswith("- "):
            text += "\n" + block
        else:
            text += "\n\n" + block
    return text


def yaml_str(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def sanitize_filename(title: str) -> str:
    name = re.sub(r"[\r\n\t]+", " ", title)
    name = re.sub(r'[\\/:*?"<>|]+', "-", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:48] or "未命名"


def unique_path(directory: pathlib.Path, stem: str) -> pathlib.Path:
    path = directory / f"{stem}.md"
    counter = 2
    while path.exists():
        path = directory / f"{stem}-{counter}.md"
        counter += 1
    return path


def download_image(url: str, directory: pathlib.Path) -> Optional[str]:
    """下载图片到附件目录，返回 Obsidian 本地引用名；失败返回 None。"""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": UA, "Referer": WECHAT_REFERER},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            blob = resp.read()
        if not blob:
            return None
        ctype = resp.headers.get_content_type()
        ext = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }.get(ctype, pathlib.Path(urllib.parse.urlparse(url).path).suffix or ".jpg")
        digest = hashlib.md5(blob).hexdigest()[:12]
        filename = f"wechat-{digest}{ext}"
        (directory / filename).write_bytes(blob)
        return filename
    except Exception as exc:  # 单张失败不影响整篇收藏
        print(f"  图片下载失败，保留原链接: {exc}", file=sys.stderr)
        return None


def build_note(page: str, source: str, output_dir: pathlib.Path, images: bool) -> pathlib.Path:
    metas = MetaCollector()
    metas.feed(page[:200_000])
    meta = metas.metas

    title = (
        element_text(page, "activity-name")
        or meta.get("og:title")
        or js_var(page, "msg_title")
        or "未命名文章"
    )
    account = (
        meta.get("og:article:author")
        or element_text(page, "js_name")
        or js_var(page, "nickname")
    )
    author = element_text(page, "js_author_name", max_len=80)
    published = ""
    ct = js_var(page, "ct")
    if ct.isdigit():
        published = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(ct)))
    else:
        published = meta.get("article:published_time", "")[:16]

    content_html = extract_content(page)
    if not content_html:
        print("  未找到正文容器 js_content，请改用粘贴正文的方式。", file=sys.stderr)
    body = to_markdown(content_html)

    if images:
        attachment_dir = ATTACHMENTS
        attachment_dir.mkdir(parents=True, exist_ok=True)

        def replace_image(match: re.Match) -> str:
            url = match.group(1)
            name = download_image(url, attachment_dir)
            return f"![[{name}]]" if name else match.group(0)

        body = re.sub(r"!\[[^\]]*\]\((https?://[^)\s]+)\)", replace_image, body)

    date_for_name = published[:10] if published else time.strftime("%Y-%m-%d")
    stem = f"公众号-{date_for_name}-{sanitize_filename(title)}"
    path = unique_path(output_dir, stem)

    url_value = source if source.startswith("http") else ""
    frontmatter = "\n".join(
        [
            "---",
            "type: resource",
            "tags: [公众号]",
            f"account: {yaml_str(account)}",
            f"author: {yaml_str(author)}",
            f"published: {yaml_str(published)}",
            f"created: {time.strftime('%Y-%m-%d')}",
            f"updated: {time.strftime('%Y-%m-%d')}",
            "status: active",
            f"url: {yaml_str(url_value)}",
            "---",
        ]
    )
    source_line = f"来源：**{account or '未知公众号'}**（微信公众号）"
    if url_value:
        source_line += f" · [原文链接]({url_value})"
    if published:
        source_line += f" · 发布于：{published}"

    note = "\n\n".join(
        [
            f"# {title}",
            f"> {source_line}",
            "## 文章要点",
            "（待 Codex 阅读后填写：3-5 条核心观点）",
            "## 正文 / 摘录",
            body if body else "（未能自动提取正文，请粘贴原文）",
            "## 我的批注与关联",
            "",
            "## 行动",
            "",
            "- [ ] ",
        ]
    )
    path.write_text(note + "\n", encoding="utf-8")
    try:
        display = path.relative_to(VAULT)
    except ValueError:
        display = path
    print(f"  已生成: {display}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="公众号文章 -> Obsidian 笔记")
    parser.add_argument("sources", nargs="+", help="mp.weixin.qq.com 链接或本地 HTML 文件")
    parser.add_argument("--images", action="store_true", help="下载图片到 90-Attachments 并本地引用")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="笔记输出目录")
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for source in args.sources:
        print(f"处理: {source}")
        try:
            page = fetch_text(source)
            build_note(page, source, output_dir, args.images)
        except Exception as exc:
            failures += 1
            print(f"  失败: {exc}", file=sys.stderr)

    if failures:
        print(f"完成，但有 {failures} 个来源失败。", file=sys.stderr)
        return 1
    print("完成 ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
