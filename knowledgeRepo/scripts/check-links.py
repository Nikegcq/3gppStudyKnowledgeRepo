#!/usr/bin/env python3
"""检查 Obsidian 知识库中的 wiki 链接（[[目标]]）是否都能解析。"""

import pathlib
import re
import sys

VAULT = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".git", ".obsidian", "scripts", "90-Attachments"}
LINK_RE = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def note_files():
    for path in VAULT.rglob("*.md"):
        parts = path.relative_to(VAULT).parts
        if EXCLUDE_DIRS.intersection(parts):
            continue
        yield path


def resolve(target: str):
    """按 Obsidian 规则查找链接目标：忽略别名/标题，返回所有同名候选。"""
    stem = target.strip()
    if stem.lower().endswith(".md"):
        stem = stem[:-3]
    candidates = []
    for path in VAULT.rglob(f"{stem}.md"):
        parts = path.relative_to(VAULT).parts
        if not EXCLUDE_DIRS.intersection(parts):
            candidates.append(path)
    return candidates


def main():
    checked = 0
    missing = []
    ambiguous = []
    for note in note_files():
        try:
            text = note.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # 跳过代码块和行内代码，避免把示例写法当成真实链接
        text = CODE_FENCE_RE.sub("", text)
        text = INLINE_CODE_RE.sub("", text)
        for match in LINK_RE.finditer(text):
            checked += 1
            target = match.group(1)
            candidates = resolve(target)
            if not candidates:
                missing.append((target, note))
            elif len(candidates) > 1:
                ambiguous.append((target, note, len(candidates)))

    for target, note in missing:
        print(f"缺失链接: [[{target}]]（来自 {note.relative_to(VAULT)}）")
    for target, note, count in ambiguous:
        print(
            f"链接不唯一: [[{target}]]（来自 {note.relative_to(VAULT)}，"
            f"共有 {count} 个同名文件，建议带路径）"
        )

    if missing or ambiguous:
        sys.exit(1)
    print(f"共检查 {checked} 条链接，全部可解析 ✅")


if __name__ == "__main__":
    main()
