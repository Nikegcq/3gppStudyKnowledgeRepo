#!/usr/bin/env python3
"""知识库定期梳理审计：孤儿笔记、滞留 draft、悬空链接、Inbox 堆积、近重复。"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys
from collections import defaultdict

VAULT = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".git", ".obsidian", ".obsidian-mcp", "scripts", "90-Attachments", "__pycache__"}
SKIP_TYPES = {"journal", "template", "moc", "area", "project"}
INDEX_STEMS = {"Home"}
META_FILES = {"AGENTS.md", "README.md"}

LINK_RE = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
FM_FIELD_RE = re.compile(r"^([A-Za-z_][\w-]*)\s*:\s*(.+)$", re.MULTILINE)


def is_skipped(path: pathlib.Path) -> bool:
    return bool(EXCLUDE_DIRS.intersection(path.relative_to(VAULT).parts))


def note_files():
    for path in VAULT.rglob("*.md"):
        if is_skipped(path) or path.name in META_FILES:
            continue
        yield path


def strip_code(text: str) -> str:
    text = CODE_FENCE_RE.sub("", text)
    return INLINE_CODE_RE.sub("", text)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FM_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for key, raw in FM_FIELD_RE.findall(match.group(1)):
        value = raw.strip().strip("\"'")
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            fields[key] = inner
        else:
            fields[key] = value
    return fields


def parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(value[:10] if fmt != "%Y%m%d" else value[:8], fmt).date()
        except ValueError:
            continue
    return None


def stem_key(path: pathlib.Path) -> str:
    return path.stem


def resolve_stem(stem: str, by_stem: dict[str, list[pathlib.Path]]) -> list[pathlib.Path]:
    stem = stem.strip()
    if stem.lower().endswith(".md"):
        stem = stem[:-3]
    return by_stem.get(stem, [])


def title_tokens(stem: str) -> set[str]:
    """粗粒度分词：去掉常见前缀后按非字母数字切分，兼容中英混排。"""
    cleaned = re.sub(r"^(学习|概念|仓库|领域|公众号|MOC|笔记|项目)[-_]?", "", stem)
    parts = re.split(r"[-_/\s]+", cleaned)
    tokens: set[str] = set()
    for part in parts:
        if not part:
            continue
        tokens.add(part.lower())
        # 中文按 2-gram，便于近重复检测
        if re.search(r"[一-鿿]", part) and len(part) >= 2:
            for i in range(len(part) - 1):
                tokens.add(part[i : i + 2])
    return tokens


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


def collect_backlinks(
    notes: list[pathlib.Path], by_stem: dict[str, list[pathlib.Path]]
) -> dict[str, set[pathlib.Path]]:
    backlinks: dict[str, set[pathlib.Path]] = defaultdict(set)
    for note in notes:
        try:
            text = strip_code(note.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.lower().endswith(".md"):
                target = target[:-3]
            for cand in by_stem.get(target, []):
                backlinks[cand.stem].add(note)
    return backlinks


def collect_index_refs(notes: list[pathlib.Path]) -> set[str]:
    """Home / MOC / 领域页 中引用到的笔记 stem。"""
    refs: set[str] = set()
    for note in notes:
        name = note.name
        if not (
            note.stem in INDEX_STEMS
            or name.startswith("MOC-")
            or name.startswith("领域-")
            or note.parent.name == "20-Areas"
        ):
            continue
        try:
            text = strip_code(note.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.lower().endswith(".md"):
                target = target[:-3]
            refs.add(target)
        # 也记录索引页自身
        refs.add(note.stem)
    return refs


def is_content_note(path: pathlib.Path, fm: dict[str, str]) -> bool:
    ntype = (fm.get("type") or "").lower()
    if ntype in SKIP_TYPES:
        return False
    stem = path.stem
    if stem in INDEX_STEMS or stem.startswith("MOC-") or stem.startswith("领域-"):
        return False
    top = path.relative_to(VAULT).parts[0] if path.relative_to(VAULT).parts else ""
    if top in {"60-Templates", "40-Archive", "50-Journal", "10-Projects"}:
        return False
    return True


def section(title: str, items: list[str]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("_无_")
    else:
        lines.extend(f"- {item}" for item in items)
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="知识库梳理审计，输出 Markdown 报告")
    parser.add_argument(
        "--stale-days",
        type=int,
        default=30,
        help="status=draft 且 created 超过 N 天视为滞留（默认 30）",
    )
    parser.add_argument(
        "--similar-threshold",
        type=float,
        default=0.55,
        help="标题 token Jaccard 相似度阈值（默认 0.55）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="将报告写入文件（默认打印到 stdout）",
    )
    args = parser.parse_args()

    today = dt.date.today()
    notes = list(note_files())
    by_stem: dict[str, list[pathlib.Path]] = defaultdict(list)
    for path in notes:
        by_stem[path.stem].append(path)

    texts: dict[str, str] = {}
    metas: dict[str, dict[str, str]] = {}
    for path in notes:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = ""
        texts[path.stem] = text
        metas[path.stem] = parse_frontmatter(text)

    backlinks = collect_backlinks(notes, by_stem)
    index_refs = collect_index_refs(notes)

    inbox_dir = VAULT / "00-Inbox"
    inbox_files = (
        sorted(p for p in inbox_dir.glob("*.md") if p.is_file())
        if inbox_dir.is_dir()
        else []
    )

    broken: list[str] = []
    for path in notes:
        body = strip_code(texts[path.stem])
        for match in LINK_RE.finditer(body):
            target = match.group(1).strip()
            if not resolve_stem(target, by_stem):
                rel = path.relative_to(VAULT)
                broken.append(f"`{rel}` → `[[{target}]]`")

    content_notes = [p for p in notes if is_content_note(p, metas[p.stem])]

    orphans: list[str] = []
    for path in content_notes:
        stem = path.stem
        has_in = bool(backlinks.get(stem))
        has_index = stem in index_refs
        top = path.relative_to(VAULT).parts[0]
        # Inbox 里未分类笔记暂不算孤儿
        if top == "00-Inbox":
            continue
        if not has_in and not has_index:
            rel = path.relative_to(VAULT)
            ntype = metas[stem].get("type") or "-"
            orphans.append(f"`{rel}`（type={ntype}，无反链且未挂 Home/MOC/领域页）")

    stale: list[str] = []
    for path in content_notes:
        stem = path.stem
        fm = metas[stem]
        status = (fm.get("status") or "").lower()
        if status != "draft":
            continue
        created = parse_date(fm.get("created") or "")
        if created is None:
            created = dt.datetime.fromtimestamp(path.stat().st_mtime).date()
        age = (today - created).days
        if age >= args.stale_days:
            rel = path.relative_to(VAULT)
            stale.append(f"`{rel}`（draft 已 {age} 天，created={created.isoformat()}）")

    near_dupes: list[str] = []
    token_map = {p.stem: title_tokens(p.stem) for p in content_notes}
    stems = [p.stem for p in content_notes]
    seen_pairs: set[tuple[str, str]] = set()
    for i, a in enumerate(stems):
        for b in stems[i + 1 :]:
            score = jaccard(token_map[a], token_map[b])
            if score >= args.similar_threshold:
                pair = tuple(sorted((a, b)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                near_dupes.append(
                    f"`{by_stem[a][0].relative_to(VAULT)}` ≈ "
                    f"`{by_stem[b][0].relative_to(VAULT)}`（相似度 {score:.2f}）"
                )

    moc_missing: list[str] = []
    for path in content_notes:
        stem = path.stem
        top = path.relative_to(VAULT).parts[0]
        if top == "00-Inbox":
            continue
        if stem not in index_refs and not backlinks.get(stem):
            # 与孤儿重叠时只在孤儿段报告；这里单独列「有反链但无索引入口」
            continue
        if stem not in index_refs and backlinks.get(stem):
            rel = path.relative_to(VAULT)
            moc_missing.append(f"`{rel}`（有反链，但未出现在 Home/MOC/领域页）")

    report: list[str] = []
    report.append("# 知识库梳理审计报告")
    report.append("")
    report.append(f"- 生成日期：{today.isoformat()}")
    report.append(f"- 笔记总数：{len(notes)}（内容笔记 {len(content_notes)}）")
    report.append(f"- Inbox 堆积：{len(inbox_files)}")
    report.append(f"- draft 滞留阈值：{args.stale_days} 天")
    report.append("")
    report.append("## 处置约定")
    report.append("")
    report.append("- 不物理删除：合并或移入 `40-Archive`，确认无用再删。")
    report.append("- 处理后刷新相关笔记 `updated`，并同步 MOC / 领域页。")
    report.append("- 详细流程见 `AGENTS.md`「定期梳理」。")
    report.append("")

    report.extend(section(f"Inbox 堆积（{len(inbox_files)}）", [
        f"`{p.relative_to(VAULT)}`" for p in inbox_files
    ]))
    report.extend(section(f"悬空链接（{len(broken)}）", broken))
    report.extend(section(f"孤儿笔记（{len(orphans)}）", orphans))
    report.extend(section(f"滞留 draft（{len(stale)}）", stale))
    report.extend(section(f"索引未挂载（有反链）（{len(moc_missing)}）", moc_missing))
    report.extend(section(f"近重复候选（{len(near_dupes)}）", near_dupes))

    report.append("## 建议下一步")
    report.append("")
    if not any([inbox_files, broken, orphans, stale, moc_missing, near_dupes]):
        report.append("- 本周期无待处理项，保持现状即可。")
    else:
        if inbox_files:
            report.append("- 先清 Inbox：每条归入 Resources / Projects / Archive。")
        if broken:
            report.append("- 修复悬空链接：补建目标笔记，或改成已有笔记名。")
        if orphans:
            report.append("- 孤儿笔记：挂到 MOC/领域页；挂不上的进 `40-Archive`。")
        if stale:
            report.append("- 滞留 draft：补全为 active，或归档。")
        if moc_missing:
            report.append("- 把有反链的笔记补进对应 MOC，方便从主题地图进入。")
        if near_dupes:
            report.append("- 近重复：人工确认后合并，另一篇归档并加「见 [[主笔记]]」。")
    report.append("")

    text = "\n".join(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"报告已写入 {args.output}")
    else:
        print(text)

    issues = len(inbox_files) + len(broken) + len(orphans) + len(stale) + len(moc_missing) + len(near_dupes)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
