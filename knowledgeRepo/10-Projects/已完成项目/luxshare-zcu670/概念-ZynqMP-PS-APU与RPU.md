---
type: note
tags: [ZynqMP, RPU, Cortex-R5F, APU, PS, 实时, RTOS, 硬件, luxshare]
layer: L1
created: 2026-10-08
updated: 2026-10-08
status: active
source: AMD UG1085 v2.5 第 4 章（Real-time Processing Unit）+ AMD RFSoC 器件规格表
---

# 概念：ZynqMP PS 里的 APU、RPU 与 PMU

## 一句话总结

**RPU = Real-time Processing Unit**，是 Zynq UltraScale+ PS 内部的双核 **Arm Cortex-R5F**；它和跑 Linux 的四核 Cortex-A53（APU）并列，靠 TCM 与 MPU 提供确定性实时能力，但**没有 MMU，跑不了 Linux**。

## 1 PS 里的三套处理器

| 单元 | 内核 | 定位 | 关键区别 |
| --- | --- | --- | --- |
| APU | 四核 Cortex-A53（ZU67DR-2 ≤1.33 GHz） | 应用处理，跑 Linux | 有 MMU、cache 层级深、延迟不确定 |
| **RPU** | **双核 Cortex-R5F（≤533 MHz）** | 实时处理，裸机 / FreeRTOS | **只有 MPU**、有 TCM、中断延迟低 |
| PMU | 三冗余 MicroBlaze | 平台管理：上电、复位、隔离、功耗 | **不是 RPU**，跑 PMU 固件，独立于用户软件 |

⚠️ 常见混淆：PMU 与 CSU 内部是 MicroBlaze；RPU 是 Cortex-R5F。三者别混。

## 2 RPU 硬件特性（UG1085 第 4 章）

- ARMv7-R 架构，32-bit，带 VFPv3 单/双精度浮点单元
- **MPU（内存保护单元），没有 MMU** → 结构上不能跑 Linux
- 每核 L1：32 KB I-cache + 32 KB D-cache，带 ECC
- **TCM（紧耦合内存）**：
  - split 模式：每核 ATCM 64 KB + BTCM 64 KB = **128 KB/核**
  - lockstep 模式：R5_0 独占 **128 KB ATCM + 128 KB BTCM = 256 KB**
  - ATCM 放中断/异常处理代码（避免 cache miss 延迟），BTCM 放密集数据
- 每核一个 64-bit AXI3 **master**（访问 DDR / 外设 / PL）+ 64-bit AXI3 **slave**（外部 DMA 直接写 TCM）
- 低中断延迟：专用外设端口直达中断控制器、不可屏蔽快速中断
- 可 **split**（两核各跑各的）或 **lockstep**（双核冗余锁步，用于功能安全）
- 另有 BIST、看门狗、性能监视单元

**TCM 是"实时"两个字的硬件基础**：访问延迟完全确定，不受 cache 命中和总线竞争影响。

## 3 RPU 用来干什么

1. **硬实时控制**：TDD 收发切换时序、RF 前端与衰减器/PA 使能、AGC 环路、DPD/CFR 参数在线更新
2. **PL 的实时管家**：读写 AXI 寄存器、控制 DMA、打时间戳、与 PL 里的 TDD / FIFO 逻辑握手
3. **开机与配置序列**：按严格时序初始化射频与时钟芯片（上电即跑，早于 Linux）
4. **功能安全**：lockstep 双核比对
5. **与 Linux 分工**：APU 跑管理面（配置下发、日志、协议栈），RPU 跑实时面，二者用 IPI + 共享内存 + rpmsg 通信

## 4 什么时候不该用 RPU

- 只需要 50–100 µs 级抖动 → Linux + PREEMPT_RT 足够
- 实时活儿能塞进 PL → 直接放逻辑里，比引入第二个 OS 更简单
- 只有配置面/管理面 → 留在 Linux

引入 RPU 的隐性成本：两套工具链与调试手段、两套升级路径、共享内存一致性、外设归属划分。

## 相关笔记

- [[实践-ZCU670-Linux与RPU-AMP]]（怎么把 RPU 真正跑起来）
- [[概念-高端radio软件架构-Linux与RTOS分工]]（什么时候需要第二个 OS）
- [[ZCU670-PL-PS-参数]]（ZU67DR 的 PS 参数出处）
- [[MOC-RTOS]]、[[MOC-Linux]]
