#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "尚未初始化 git，先执行：git init -b main"
  exit 1
fi

git add -A

if git diff --cached --quiet; then
  echo "没有可提交的变更"
  exit 0
fi

git commit -m "backup: $(date '+%Y-%m-%d %H:%M')"

if git remote | grep -q .; then
  git push
  echo "已推送到远程"
else
  echo "已本地提交（未配置远程，跳过推送）"
fi

