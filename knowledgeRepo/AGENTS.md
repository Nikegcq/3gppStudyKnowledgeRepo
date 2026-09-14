# knowledgeRepo 使用约定（给 Codex）

这是用户的个人 Obsidian 知识库。主题：**通信行业（5G/6G 无线接入）**。核心关注 L1/L2/L3 协议栈知识，以及 FPGA、射频（RF）、C++ 等实现技术；通过 O-RAN（O-CU/O-DU）等开源仓库学习代码；微信公众号好文章是重要的持续输入。

你在本仓库的职责：帮助用户**捕获、整理、连接、回顾**这些知识。默认用中文写作。

## 目录结构

- `00-Inbox`：未分类的新笔记，新捕获默认放这里
- `10-Projects`：项目（有目标、有截止时间）
- `20-Areas`：领域页，按协议层划分（L1 / L2 / L3）
- `30-Resources`：资源与常青笔记
  - 根目录放主题地图：`MOC-FPGA.md`、`MOC-射频.md`、`MOC-C++与软件.md`、`MOC-O-RAN开源.md`
  - `公众号收藏/`：微信公众号文章（`公众号-YYYYMMDD-主题.md`）
  - `开源仓库/`：开源仓库学习笔记（`仓库-仓库名-主题.md`）
- `40-Archive`：归档
- `50-Journal`：日记，`YYYY-MM-DD.md`
- `60-Templates`：模板
- `90-Attachments`：附件
- `scripts`：`backup.sh`、`check-links.py`、`audit.py`
- `Home.md`：首页导航

## 主题地图（分类骨架）

| 内容 | 入口 | 典型标签 |
| --- | --- | --- |
| L1 物理层（PHY） | [[领域-L1物理层]] | `L1`、`物理层` |
| L2（MAC/RLC/PDCP/SDAP） | [[领域-L2数据链路层]] | `L2` |
| L3（RRC 及接口信令） | [[领域-L3网络层]] | `L3`、`RRC` |
| FPGA 设计与基带实现 | [[MOC-FPGA]] | `FPGA` |
| 射频与模拟前端 | [[MOC-射频]] | `RF`、`射频` |
| C++ 与软件工程 | [[MOC-C++与软件]] | `C++` |
| O-RAN / O-CU / O-DU 开源 | [[MOC-O-RAN开源]] | `O-RAN`、`O-CU`、`O-DU` |
| 公众号文章 | `30-Resources/公众号收藏` | `公众号` + 主题标签 |

## 笔记规范

- 正文笔记以 YAML frontmatter 开头：`type`、`tags`、`created`、`updated`、`status`（另有 `source`/`url`/`layer`/`repo` 等按需添加），参考对应模板。
- `type`：`note` / `inbox` / `journal` / `project` / `area` / `resource` / `moc`
- 文件名：领域页 `领域-xxx.md`，地图 `MOC-xxx.md`，公众号 `公众号-YYYYMMDD-主题.md`，仓库笔记 `仓库-仓库名-主题.md`，日记 `YYYY-MM-DD.md`。
- 链接用 `[[笔记名]]`，不带 `.md`；目标不存在就本轮补建或说明，避免悬空链接。
- 附件先移入 `90-Attachments` 再引用 `![[文件名]]`。
- 由你新建的笔记，frontmatter 写实际日期，不留 `{{date}}` 占位符。
- 引用 3GPP 规范统一写成：`3GPP TS 38.214 §5.2`（规范号 + 小节）。
- 编辑用户笔记时保留原结构与文风，只改相关段落，并刷新 `updated`。

## 工作流

### 捕获公众号文章

1. 用户给一个或多个链接（`mp.weixin.qq.com`）或本地 HTML 文件：运行
   `python3 scripts/capture_wechat.py <来源> [更多来源...]`。
   抓取需要网络时，向用户请求授权后执行。
2. 脚本会在 `30-Resources/公众号收藏/` 生成 `公众号-YYYYMMDD-主题.md`，
   自动保留：公众号名、作者、发布时间、**原文 URL**、正文（转成 Markdown）。
3. 随后阅读生成的文章，补全「文章要点」（3-5 条核心观点），打上主题标签
   （如 `L1`、`FPGA`），并链接到相关领域页或 MOC；同步刷新 `updated`。
4. 脚本抓取失败（需登录 / 风控拦截）时，请用户粘贴标题 + 正文，
   手动按 `60-Templates/公众号文章模板.md` 建笔记。
5. 图片默认保留原文 URL；如需离线图片可加 `--images`（下载到
   `90-Attachments/`，该目录默认不进 Git，入库前先确认是否要放开忽略）。

### 捕获技术碎片

- 短碎片：追加到今日 `50-Journal/YYYY-MM-DD.md` 的「随手捕获」。
- 可展开的话题：按上面的分类骨架，直接归入对应领域 / 主题，或先进 `00-Inbox`。

### 学习开源仓库（O-RAN / O-CU / O-DU 等）

1. 用户给出仓库（如 srsRAN、OpenAirInterface、O-RAN SC 的 O-CU/O-DU 工程）。
2. 若本地没有代码：建议克隆到库外目录 `~/study/opensource/<仓库名>`，克隆需要网络授权时提示用户。
3. 先产出「仓库地图」笔记：`30-Resources/开源仓库/仓库-仓库名.md`，记录仓库地址、本地路径、用 3-5 句话概括、目录/模块划分、构建运行方式。**不要把源码复制进库**。
4. 之后按模块/主题走读，每篇命名 `仓库-仓库名-模块.md`，与概念笔记、3GPP 章节双向链接。
5. 结合标准学习：代码里看到的关键流程，标注对应 `3GPP TS` 或 O-RAN 规范章节。

### 整理收件箱

- 按分类骨架判断归属；公众号文章即使讲协议知识也统一进 `公众号收藏`，用标签和链接挂到主题下。
- 重命名、补全 frontmatter、更新 `Home.md` 和相关 MOC。

### 问答与回顾

- 用户问“我收集过的 L1/FPGA/公众号 XX”时，先在领域页、MOC、公众号收藏中检索，回答时标注来源笔记。
- 定期回顾：总结某主题下新增了哪些内容、哪些疑问还没解决，可提议补一篇综合笔记。

### 备份与检查

- 备份：`bash scripts/backup.sh`
- 改动过链接时：`python3 scripts/check-links.py`
- 结构审计：`python3 scripts/audit.py`（或 `python scripts/audit.py`）

### 定期梳理

清理不是「删得多」，而是让每条笔记都有**入口、归属、状态**。多余信息分三类：

| 类型 | 表现 | 处置 |
| --- | --- | --- |
| 重复 | 同一概念写了两篇 | 合并，保留一篇；另一篇 Archive + 「见 [[主笔记]]」 |
| 孤岛 | 无反链，MOC/领域页也没挂 | 挂上入口；挂不上则 Archive |
| 过时 | `status: draft` 超期、链接失效 | 补全为 active，或 Archive |

**不直接物理删除**：先移入 `40-Archive`，确认无用再删。

#### 节奏

- **每周（10–15 分钟）**：清空 `00-Inbox`（每条三选一：归入 Resources / Projects / Archive）；扫 Journal 可展开碎片；跑 `check-links.py`。
- **每月（30–60 分钟）**：跑 `python3 scripts/audit.py -o 40-Archive/audit-YYYY-MM.md`，得到待处理列表后再批量改，用户确认处置。
- **每季（1–2 小时）**：选一个主题（如 SSB）做收敛——散落笔记收成 1 篇综述 + 若干细节；淘汰过时实现 → Archive；更新领域页/MOC「当前理解」。

#### 判定规则

- 有反链且近 90 天仍相关 → 保留。
- 有反链但内容空/过时 → 补全或降级为索引。
- 无反链且无 MOC 挂载 → 挂上；挂不上 → `40-Archive`。
- 两篇高度相似 → 合并，另一篇 Archive 并加「见 [[主笔记]]」。
- 纯过程笔记（旧 Journal）→ 默认 Archive，有价值摘录抽走。

#### 状态流转

```text
Inbox → Active（分类归入）
Active → Review（超期未动 / 主题收敛）
Review → Active（补全挂链）或 Archive（过时/被合并）
Archive → Active（又需要）或 确认后删除
```

#### 命令入口

- 审计报告：`python3 scripts/audit.py`（stdout）或 `-o <路径>` 写文件
- 可调参数：`--stale-days 30`、`--similar-threshold 0.55`
- 对 AI 说「跑月度梳理」时：先跑 audit，列出报告要点，**用户确认后再改库**；处置默认合并或 Archive，不物理删除；处理完刷新 `updated` 并同步 MOC。

## 边界

- 不删除、不大改用户笔记，除非明确要求。
- 不修改 `.obsidian/*`、`README.md`、`AGENTS.md`，除非明确要求。
- 大规模重构前先给方案并说明影响，得到确认再执行。
