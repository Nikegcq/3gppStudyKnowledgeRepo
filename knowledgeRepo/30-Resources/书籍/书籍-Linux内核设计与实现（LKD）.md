---
type: resource
tags: [Linux, 内核, 书籍, LKD, Robert Love, 学习资源]
created: 2026-09-10
updated: 2026-09-10
status: active
source: Robert Love, Linux Kernel Development (3rd Edition), Addison-Wesley Professional, 2010
source_url: https://www.informit.com/store/linux-kernel-development-9780672329463
---

# 书籍：Linux 内核设计与实现（LKD，Robert Love）

## 一句话

《Linux Kernel Development》（社区常简称 **LKD**）是 Robert Love 写的一本“内核子系统导览书”：不教你写驱动，而是把 Linux 内核的主要子系统（进程、调度、系统调用、中断、同步、定时器、内存、VFS、块 I/O、模块、调试）讲成一条可读的主线。中文版为《Linux 内核设计与实现（原书第 3 版）》。

## 基本信息

### 中文版（原书第 3 版）

| 项 | 内容 |
| --- | --- |
| 书名 | Linux 内核设计与实现（原书第 3 版） |
| 原作名 | Linux Kernel Development |
| 作者 | [美] Robert Love |
| 译者 | 陈莉君、康华 |
| 出版社 | 机械工业出版社（华章） |
| 丛书 | 华章专业开发者丛书 |
| 出版时间 | 2011-04-30 |
| ISBN | 978-7-111-33829-1 |
| 页数 / 装帧 / 定价 | 352 页 / 平装 / 69.00 元 |
| 豆瓣 | 8.5 / 10（676 人评价，截至 2026-09-10） |
| 豆瓣页 | https://book.douban.com/subject/6097773/ |

### 英文原版

| 版次 | 出版社 | 出版时间 | ISBN-10 / ISBN-13 | 页数 |
| --- | --- | --- | --- | --- |
| 第 3 版 | Addison-Wesley Professional（Developer's Library） | 2010-06-22 | 0-672-32946-8 / 978-0-672-32946-3 | 480 |
| 第 2 版 | Novell Press | 2005-01-12 | 0-672-32720-1 / 978-0-672-32720-9 | — |

第 3 版电子书 ISBN-13：978-0-13-262956-0。官方产品页（含 Sample Pages，第 2 章 + 索引）：
https://www.informit.com/store/linux-kernel-development-9780672329463

## 内容覆盖

- 基于 **Linux 2.6.xx**，覆盖到当时较新的特性：CFS 调度器、可抢占内核、块 I/O 层、I/O 调度器等。
- 主题：进程管理与调度、系统调用、内核数据结构、中断与下半部、内核同步、定时器与时间管理、内存管理、虚拟文件系统（VFS）、块 I/O、进程地址空间、页缓存与回写、设备与模块、调试、可移植性、社区与补丁流程。

## 目录（第 3 版，中文版）

1. Linux 内核简介
2. 从内核出发
3. 进程管理
4. 进程调度
5. 系统调用
6. 内核数据结构
7. 中断和中断处理
8. 下半部和推后执行的工作
9. 内核同步介绍
10. 内核同步方法
11. 定时器和时间管理
12. 内存管理
13. 虚拟文件系统
14. 块 I/O 层
15. 进程地址空间
16. 页高速缓存和页回写
17. 设备与模块
18. 调试
19. 可移植性
20. 补丁、开发和社区

（另有译者序、序言、前言、作者简介。）

## 怎么配合本仓库的学习路径读

LKD 适合作为 **T 线“概念地图”**，与 [[学习-Linux-内核源码阅读与驱动学习法]] 的实践结合；不要把它当驱动开发书（驱动实战看 LDD3、内核文档和 [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]）。

| LKD 章节 | 对应执行版阶段 | 配套实践 |
| --- | --- | --- |
| 第 1–2 章 | 阶段 0 | 源码地图、模块 `insmod/rmmod`、内核编译（[[学习-Linux-阶段0-源码地图与调试环境]]） |
| 第 3–5 章 | 阶段 1 | 进程/系统调用：在 QEMU+GDB 里断 `vfs_read`、自己写的 `open/read` |
| 第 6 章 | 阶段 1 | 内核数据结构：链表、红黑树、kfifo，对照 `include/linux/` |
| 第 7–8 章 | 阶段 7 | 中断、下半部、workqueue；对照 `dma-axi-dmac` 的 IRQ 处理 |
| 第 9–10 章 | 阶段 7 | 同步原语；对照驱动里的 spinlock/mutex |
| 第 11 章 | 阶段 6–7 | 定时器与时间管理；对照 DMA/采样时间戳 |
| 第 12、15、16 章 | 阶段 6 | 内存、地址空间、页缓存；对照 `dma_alloc_coherent`、mmap |
| 第 13–14 章 | 阶段 6 | VFS、块 I/O；理解用户态 read/mmap 到缓冲区 |
| 第 17 章 | 阶段 3 | 设备与模块；衔接 AD9361 驱动与 IIO |
| 第 18 章 | 全阶段 | `printk`、oops、GDB/QEMU 调试方法 |
| 第 19–20 章 | 全程 | 可移植性、补丁与社区（参与上游时需要） |

推荐读法：

- 第一遍按 T 线顺序粗读：第 2、5、6、7、8、9、10、17、18 章，建立概念与 API 感觉。
- 第二遍按 P 线对照精读：读到某个子系统时，在本地 6.1 源码里找同名文件/函数（用 elixir + cscope + `rg`），并在 QEMU+GDB 里断一次。
- 不要逐行啃代码示例：书中代码是 2.6 时代，当前 6.1 在调度、内存、VFS、中断 API 上已有变化；以概念和设计思想为主，API 细节以本地源码和 docs.kernel.org 为准。

## 版本与时效性提醒

- LKD 第 3 版出版于 2010 年，覆盖 Linux 2.6.xx；本仓库的 P 线代码是 6.1（`f3da30df`），两者相隔十余年。
- 仍值得读的部分：内核总体结构、进程/调度思想、中断/下半部模型、同步原语、内存/VFS/块 I/O 的分层方式。
- 需要以新源码核对的部分：调度器实现（CFS → EEVDF）、内存管理细节、VFS 接口、中断与锁 API、设备模型与电源管理等。
- 阅读时建议同时开 elixir.bootlin.com（最新源码）与本地 `plutosdr-fw/linux`（实际行号），不要把 LKD 的旧 API 直接当现成答案。

## 获取与相关资源

- 官方英文版（Addison-Wesley / InformIT）：https://www.informit.com/store/linux-kernel-development-9780672329463
  - 官方 Sample Pages（含第 2 章 + 索引）在页面内下载。
- 本地官方试读（已下载，非全书）：[LKD-3rd-edition-sample-chapter2.pdf](90-Attachments/书籍/LKD-3rd-edition-sample-chapter2.pdf)
  - 路径：`90-Attachments/书籍/LKD-3rd-edition-sample-chapter2.pdf`
  - 来源：出版社 Sample Pages（第 2 章 + 索引），文件约 671 KB；`90-Attachments/*` 默认不入 Git。
- 正版电子书 / 在线阅读渠道：
  - InformIT / Pearson 官方商店：可购买 PDF/ePub 版（ISBN 978-0-672-32946-3；电子书 ISBN-13 978-0-13-262956-0）。
  - O'Reilly Learning：若你有个人订阅或学校/公司机构订阅，可在其平台阅读英文在线版（需登录）。
  - 中文版：机械工业出版社/华章官方渠道及主流正版电子书平台；豆瓣页可看馆藏/购买入口。
  - 图书馆：高校图书馆、公共图书馆的 O'Reilly/Safari 订阅或馆藏纸质书（豆瓣页含上海图书馆等馆藏链接）。
- 免费合法的替代学习资源（如果目标是学内核，而非必须读 LKD 全书）：
  - LDD3 官方在线版：https://lwn.net/Kernel/LDD3/ （驱动开发经典，可免费阅读）
  - Bootlin 内核/驱动培训材料：https://bootlin.com/docs/
  - 内核官方文档：https://docs.kernel.org/
  - linux-insides、linux-kernel-labs-zh 等（见 [[学习-Linux-内核源码阅读与驱动学习法]]）
- 中文版（机械工业出版社/华章）豆瓣页：https://book.douban.com/subject/6097773/
- 配套/延伸：
  - Linux Device Drivers, 3rd Edition（LDD3）——驱动实战（本仓库作为对照资料）。
  - Robert Love, Linux System Programming——用户态系统编程。
  - 本仓库：[[学习-Linux-学习路线]]、[[学习-Linux-内核源码阅读与驱动学习法]]、[[学习-Linux-阶段0-源码地图与调试环境]]。
- 说明：LKD 是仍受版权保护的商业出版物，本文不提供盗版全书 PDF；上面提供的是出版社公开的试读章节与正版获取渠道。

## 关联

- [[MOC-Linux]]
- [[学习-Linux-学习路线]]
- [[学习-Linux-内核源码阅读与驱动学习法]]
- [[学习-Linux-阶段0-源码地图与调试环境]]
