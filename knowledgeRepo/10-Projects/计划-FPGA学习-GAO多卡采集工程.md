---
type: project
tags: [项目, FPGA, 学习计划, Vivado, Kintex-7, 多卡采集, Aurora, 以太网]
created: 2026-09-30
updated: 2026-09-30
status: active
start: 2026-09-30
due:
depends_on: "[[MOC-FPGA]]"
---

# 计划：FPGA 学习 — GAO 多卡采集工程

## 目标

**一句话**：以真实工程 `GAO_325T / prj_coloturm_325t`（Kintex-7 325T 多卡 ADC 采集）为教材，把 FPGA「读得懂、串得起、写得出」——从顶层框图到寄存器、数据通路、跨时钟域与多卡组包。

**定位**：

- 与 [[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]] 并行或穿插，不抢 L1 协议主线。
- 不以「重新实现整板」为目标，而是**吃透架构 + 精读关键 RTL + 动手小实验**。
- 资料源：`C:\Users\Admin\work\prj_colotrum\`（zip 与已解出 `_prj_full`）；学习手册见 `C:\Users\Admin\work\fpga\`（正点原子 ZYNQ/FPGA 指南）。

**成功标准（启动后打勾）**：

- [ ] G1：能默画「主卡 + 从卡」系统框图，并说清控制面 / 数据面、三个时钟域；
- [ ] G2：能对照 `user_regs` 说清软件如何配置触发 / 降噪 / 以太网 / 主从卡号；
- [ ] G3：能跟完一条数据：ADC → `data_process_top` → `pkg_data_to_eth` → UDP，并解释 `card_id` / timestamp / 3s 超时；
- [ ] G4：能解释 Aurora `type check`、轮询 Arbiter、异步 FIFO 为何存在；
- [ ] G5：完成一个可仿真的小实验（如简化 `pkg_data_to_eth` 状态机或 FIFO 跨时钟域）。

## 当前状态（2026-09-30）

| 项 | 状态 | 笔记 |
| --- | --- | --- |
| 工程定位与目录地图 | 已完成 | [[仓库-GAO_325T-工程总览]] |
| 系统框图（主从卡/时钟域） | 已完成 | [[图-GAO_325T-多卡采集系统框图.excalidraw]]、[[仓库-GAO_325T-系统架构与数据通路]] |
| 多卡组包 / 超时 | 概念已对齐，未精读状态机 | [[仓库-GAO_325T-系统架构与数据通路]] |
| user_regs 寄存器位域 | 目录已列，未逐位展开 | 见工程总览表 |
| DWT / 降噪流水线 | 只知模块名 | — |
| 仿真小实验 | 未开始 | — |

## 任务清单

- [x] T1 建立工程总览与目录地图
- [x] T2 用 Excalidraw 重画系统框图并写入架构笔记
- [ ] T3 精读 `pkg_data_to_eth.v` 状态机（等卡 / 3s 超时 / 组头）
- [ ] T4 精读 `aurora_recv_mux.v`（type check、code/data 分流）
- [ ] T5 精读 `user_regs.v` 位域，补一张寄存器速查
- [ ] T6 沿 `data_process_top` 画单卡数据通路（LPF → DWT → 触发 → 成包）
- [ ] T7 对照正点原子指南补 AXI / 约束 / 时序基础
- [ ] T8 选一个小模块做仿真或波形走读（G5）

## 阶段建议

| 阶段 | 内容 | 产出 |
| --- | --- | --- |
| F1 地图 | 框图 + 目录 + 主从角色 | 本计划已完成的两篇 |
| F2 控制面 | MB + `user_regs` + 寄存器位域 | 寄存器速查表 |
| F3 数据面 | `pkg_data_to_eth` + `aurora_recv_mux` | 状态机笔记 |
| F4 单卡算法 | `adc_top` / `adc_trig` / `dwt_*` | 数据通路图 |
| F5 实验 | 仿真或 ILA 波形走读 | 实验记录 |

## 相关笔记

- [[仓库-GAO_325T-工程总览]]
- [[仓库-GAO_325T-系统架构与数据通路]]
- [[图-GAO_325T-多卡采集系统框图.excalidraw]]
- [[MOC-FPGA]]

## 日志

- 2026-09-30：对照系统框图修正理解——**1 主卡 + ≤11 从卡**，非单板；建立项目、总览、架构笔记与 Excalidraw 框图。
