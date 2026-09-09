# 通信行业个人知识库（Obsidian + Codex）

本地优先的个人知识库：**Obsidian** 负责读写笔记，**Codex CLI** 负责捕获、整理、检索与复盘。纯 Markdown + Git，不依赖云服务。

## 知识结构

按“领域页 + 主题地图 + 素材源”三层组织：

| 层 | 位置 | 内容 |
| --- | --- | --- |
| 领域页 | `20-Areas` | L1 物理层、L2 数据链路层、L3 网络层，长期维护 |
| 主题地图 | `30-Resources`（MOC-*.md） | FPGA、射频、C++ 与软件、O-RAN 开源 |
| 素材源 | `30-Resources/公众号收藏`、`30-Resources/开源仓库` | 公众号文章、仓库学习笔记 |
| 收件箱/日记/项目/归档 | `00-Inbox`、`50-Journal`、`10-Projects`、`40-Archive` | 流转与沉淀 |

主页入口：[Home.md](Home.md)

## 快速开始

1. Obsidian 中打开本目录（若尚未登记：设置 → 打开仓库 → 选 `knowledgeRepo`）。
2. 终端进入目录启动 Codex：`cd ~/study/knowledgeRepo && codex`，Codex 自动按 `AGENTS.md` 约定工作。
3. 常用指令：

```text
把这篇公众号文章收进知识库（粘贴链接或正文）
整理收件箱
基于公众号收藏，总结目前我对波束管理的理解
帮我学习 srsRAN 的调度器实现，先建仓库地图
查一下 MOC-O-RAN开源 下有哪些仓库笔记
检查失效链接 / 备份
```

## 素材输入

### 微信公众号文章（3 种方式）

1. **浏览器剪藏（最顺手）**：安装官方 Obsidian Web Clipper 浏览器扩展，把“保存位置”设为 `30-Resources/公众号收藏`，文章页点一下即可存成 Markdown。
2. **对话收藏（已自动化）**：把文章链接发给 Codex（一个或多个都行），
   Codex 会运行 `scripts/capture_wechat.py` 自动抓取正文、生成带原文链接的笔记，
   再补上文章要点和主题标签。也可以自己在终端跑：

   ```bash
   python3 scripts/capture_wechat.py "https://mp.weixin.qq.com/s/xxxx"
   python3 scripts/capture_wechat.py 文章1.html 文章2.html   # 批量导入历史 HTML
   ```

   加 `--images` 会把图片下载到 `90-Attachments/` 并改成本地引用
   （注意该目录默认不进 Git）。

3. **批量导入历史文章**：把之前存下的 HTML/网页文件放进一个临时目录，让 Codex 批量转换成 Markdown 并归入公众号收藏。

注意：文章收录时保留作者与原文链接，内容仅供个人学习。

### 开源仓库学习

候选仓库（先放地图，不复制源码进库）：

- **srsRAN Project**（5G NR 的 L1/L2/L3 开源实现，C++，GitHub: `srsran/srsRAN_Project`）
- **OpenAirInterface（OAI）**（RAN 与核心网开源工程，官方代码在 GitLab: `oai/openairinterface5g`）
- **O-RAN Software Community（O-RAN SC）**（O-CU-CP / O-CU-UP / O-DU 等官方工程，`gerrit.o-ran-sc.org`，GitHub 有 `o-ran-sc` 镜像组）
- **UERANSIM**（5G UE 与模拟 gNB，学习信令流程很好用，GitHub: `aligungr/UERANSIM`）

建议把代码克隆到库外统一目录，如 `~/study/opensource/`，库内只放学习笔记：

```text
cd ~/study/opensource
git clone https://github.com/srsran/srsRAN_Project.git
```

然后对 Codex 说“学习 `~/study/opensource/srsRAN_Project` 的调度器，先建仓库地图”，它会按开源仓库模板产出笔记并链接到 O-RAN MOC。

## 协议层入口

- L1：[[领域-L1物理层]]（3GPP TS 38.211/212/213/214 等）
- L2：[[领域-L2数据链路层]]（TS 38.321/322/323/300）
- L3：[[领域-L3网络层]]（TS 38.331/413/401）

## 备份与同步

首次使用初始化 Git（若还不是 git 仓库）：

```bash
git init -b main
git config user.name "你的名字"
git config user.email "you@example.com"
git add -A
git commit -m "init: 个人知识库"
```

之后每次备份：

```bash
bash scripts/backup.sh
```

推荐安装社区插件 Obsidian Git 做定时自动备份；也可以 `git remote add origin <地址>` 推到 GitHub/Gitee。

## 自定义

改目录命名或分类规则时，同步更新 `AGENTS.md`，Codex 会一直按新规则工作。
