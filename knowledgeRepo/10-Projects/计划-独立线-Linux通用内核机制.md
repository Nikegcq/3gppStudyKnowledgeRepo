---
type: project
tags: [项目, 学习计划, Linux, 内核, 驱动开发, QEMU, 设备树, DMA]
created: 2026-09-17
updated: 2026-09-18
status: planned
start: 
due: 
depends_on: "[[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]]"
---

# 计划：Linux 通用内核机制（独立线，不在 2026 Q4 八周内）

## 目标

**一句话**：把 Linux 内核「读得懂、写得出、调得动」的通用能力单独走完——模块/字符设备、VFS、QEMU+GDB、设备模型、DMA/中断并发——**不与 RFIC 使用或 L1 协议抢八周窗口**。

**定位**：

- 与 [[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]] **解耦**：Q4 只做「O-DU/L1 + RFIC 使用」；本计划在 Q4 结束后（或你主动插入时）再启动。
- 与 [[学习-Linux-学习路线]] 的关系：那篇是**长期详细路线**（T/P 线、阶段 0–8 全文）；本计划是**可执行排期壳**——只保留通用内核机制，去掉「必须服务 RFIC/P 线」的绑定。
- RFIC 计划执行期间若卡在机制问题（probe 顺序、DMA 路径、中断），**按需回查** [[学习-Linux-学习路线]] 对应小节即可，**不算本计划进度**。

**成功标准（启动后打勾）**：

- [ ] G1：能在 QEMU+GDB 断住 `start_kernel`、`do_initcalls`、自写 `open/read`，并解释用户态 `read()` → VFS → `file_operations` 路径；
- [ ] G2：能画出「DT node → device → bus match → driver.probe」通用链，并指出 SPI 与 platform 匹配差异；
- [ ] G3：对照一个 in-tree 简单驱动改写 lab_chardev；能读 `xilinx-xadc` 或同类 IIO 骨架（`iio_dev → channels → sysfs`）；
- [ ] G4：能独立写清 dmaengine consumer 最小流程（request → prep → issue → 回调），并解释 cyclic vs oneshot；
- [ ] G5：能讲清「中断上下文里只能做什么」，对比 threaded IRQ / workqueue / waitqueue 与裸 ISR。

## 当前状态（2026-09-17）

| 项 | 状态 | 笔记 |
| --- | --- | --- |
| T0 源码地图与工具 | 已完成 | [[学习-Linux-阶段0-源码地图与调试环境]] |
| T1 hello 模块闭环 | 已完成 | [[学习-Linux-阶段1-最小驱动闭环]] |
| T2 misc 字符设备 lab_chardev | 已完成 | [[学习-Linux-阶段1-最小驱动闭环]]、[[学习-Linux-阶段1-lab_chardev代码详解]] |
| T3 QEMU+GDB | 部分：`start_kernel` + `lab_read` 已断；`do_initcalls` 未做 | 同上；G1 未关 |
| T4 对照 in-tree 驱动 | 未开始 | — |
| T5 设备模型 | 未开始（AD9361 静态链已覆盖部分直觉） | [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]] |
| T6 子系统（IIO/DMA 机制向） | 未开始；Q4 计划只学「会用」不学机制 | — |
| 并发/中断专题 | 未开始 | — |

## 启动条件（满足任一即可排期）

1. 2026 Q4 计划 W8 收口后，自然接续；
2. 工作中被内核机制问题卡住超过 2 天，且 RFIC「会用」路径无法绕过；
3. 你明确说「开通用内核线」。

**建议窗口**：Q4 结束后连续 4–6 周、每周 2 次半天（约 8–12 h/周）；或穿插在下季度「每周五下午」。

## 阶段排期（启动后用，约 4–6 周）

| 阶段 | 内容 | 主读 | 产出 | 验收 |
| --- | --- | --- | --- | --- |
| K1 | 补完动态调试（关 G1） | QEMU+GDB；`init/main.c`、`do_initcalls`、自己的 `open/read` | 调试小抄 + 一次完整断点记录 | G1 |
| K2 | 设备模型（关 G2） | `drivers/base/{bus,dd,platform}.c`、`drivers/of/platform.c`；口试题：[[Linux驱动加载与匹配-面试问答]] | 「DT→match→probe」图；SPI vs platform 对照 | G2 + 面试题 1–11 口述通过 |
| K3 | 对照 in-tree 驱动（关 G3） | `drivers/char/` 一简单驱动；`xilinx-xadc.c` | lab_chardev 改写记录；IIO 骨架笔记 | G3 |
| K4 | dmaengine 机制（关 G4） | docs dma-api / dmaengine；`dma-axi-dmac.c` 只作 provider 样例 | 「概念-DMA与零拷贝」机制版；consumer 最小示例 | G4 |
| K5 | 中断与并发（关 G5） | `request_threaded_irq`、workqueue、spinlock/mutex；对照 [[MOC-RTOS]] | 中断时间线 + 「什么能在 ISR 做」清单 | G5 |
| K6 | 收口 | 与 RFIC/R 线、Pluto P 线对账 | 更新 [[学习-Linux-学习路线]] 勾选与 [[MOC-Linux]] 当前理解 | 本计划 status→done |

**K 线闸门**：每阶段一关；未过不进下一阶段。卡关 2 天 → 记 Journal + 换材料，不硬耗。

## 与其它计划的边界

| 计划 | 管什么 | 不管什么 |
| --- | --- | --- |
| Q4 双主线 | L1 协议 + **RFIC 会用**（R0–R4） | 内核机制深读、u-boot/FIT、QEMU 补完 |
| **本计划（K 线）** | **通用内核机制**（模块/VFS/设备模型/DMA/中断） | AD9361 调参、UG-570、3GPP 阶段 |
| [[学习-Linux-学习路线]] | 长期全文（含 Pluto P 线 u-boot→DMA→综合） | 不作为八周或本计划的进度表 |

u-boot / FIT / `pluto.its`：**不进 K 线必修**。若做板级启动再单开半天专题；需要时直接读 [[学习-Linux-学习路线]] 阶段 4。

## 任务清单（启动后勾选）

- [ ] K1.1 补 `do_initcalls` 断点
- [ ] K1.2 自写 `open/read` 完整栈记录 → **G1**
- [ ] K2.1 读 bus/dd/platform + of/platform
- [ ] K2.2 画通用匹配链 + SPI/platform 差异 → **G2**
- [ ] K2.3 口试 [[Linux驱动加载与匹配-面试问答]] 1–11（速记表能顺下来）
- [ ] K3.1 对照 `drivers/char/` 改 lab_chardev
- [ ] K3.2 读 xilinx-xadc IIO 骨架 → **G3**
- [ ] K4.1 dmaengine API 与 provider/consumer
- [ ] K4.2 最小 consumer 示例或精读记录 → **G4**
- [ ] K5.1 threaded IRQ / workqueue / 锁选型
- [ ] K5.2 中断时间线 + RTOS 对照 → **G5**
- [ ] K6 收口：勾选 [[学习-Linux-学习路线]]、更新 [[MOC-Linux]]、复盘 Journal

## 相关笔记

- 详细路线（主文档）：[[学习-Linux-学习路线]]
- 面试题（库根 `面试题/`）：[[Linux驱动加载与匹配-面试问答]]（1–11，对应 K2）
- 已有成果：[[学习-Linux-阶段0-源码地图与调试环境]]、[[学习-Linux-阶段1-最小驱动闭环]]、[[学习-Linux-阶段1-lab_chardev代码详解]]、[[学习-Linux-kernel-lab-QEMU使用流程]]、[[学习-Linux-内核源码阅读与驱动学习法]]
- 概念书：[[书籍-Linux内核设计与实现（LKD）]]
- 对照块：[[MOC-RTOS]]、[[学习-RTOS-学习路线]]
- 当前进行中（勿混进度）：[[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]]
- 入口：[[MOC-Linux]]、[[Home]]

## 日志

- 2026-09-17：自 Q4 双主线中拆出。通用内核机制（G1–G5 / K1–K6）不再占用八周窗口；Q4 主线 B 仅保留 RFIC 使用。启动条件与排期见上文。
- 2026-09-18：库根 `面试题/` 入口挂到 Home；[[Linux驱动加载与匹配-面试问答]] 题号为 **1–11**，并写入 K2 验收。
