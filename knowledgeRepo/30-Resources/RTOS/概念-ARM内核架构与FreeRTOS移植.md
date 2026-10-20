---
type: resource
tags: [RTOS, ARM, 嵌入式, FreeRTOS, Cortex-M, Cortex-R, Cortex-A, 移植]
layer: 
created: 2026-10-12
updated: 2026-10-12
status: active
source: Arm 官网（arm.com）各内核产品页
source_url: https://www.arm.com/products/silicon-ip-cpu
---

# 概念：ARM 内核架构与 FreeRTOS 移植对应

## 一句话

FreeRTOS-Kernel 的 ARM 移植覆盖 **ARMv6-M → ARMv8.1-M、ARMv7-R/v8-R、ARMv7-A/v8-A** 全谱系；本文按 M / R / A 三类 profile 归纳每个内核的架构代际、对应 `portable/` 移植目录，以及 Arm 官方定义的目标应用场景。

## 背景 / 为什么重要

- 读 `portable/` 时目录名（`ARM_CM33_NTZ`、`ARM_CR82`、`ARM_AARCH64` …）信息密度很高，但新手不容易一眼看出「这是哪代架构、带不带 FPU/TrustZone、面向什么场景」。
- 弄清内核 → 架构 → 应用场景的对应关系，才能在选型（选哪颗芯片）和移植（改哪个 port）时快速定位。
- 本笔记整理自 Arm 官方产品页，是 [[仓库-FreeRTOS-Kernel-核心层API与原理]] 与 [[MOC-RTOS]] 的选型/移植补充。

## port 命名规则速查

| 片段 | 含义 |
| --- | --- |
| `CMxx` | Cortex-M 系列，数字即 core 型号 |
| `CRxx` | Cortex-R 系列 |
| `CAxx` | Cortex-A 系列 |
| `AARCH64` | ARMv8-A 的 64 位执行态（A64 指令集） |
| `F` | 带硬件 FPU（如 `CM4F`） |
| `MPU` | 带内存保护单元变体 |
| `NTZ` | Non-TrustZone，非安全侧（不带 TrustZone 隔离） |
| `SRE` | 通过 System Register 访问 GIC（而非内存映射） |
| `secure` / `non_secure` | 支持 TrustZone 的 M 系列，分别对应安全/非安全工程 |

## 一、Cortex-M 系列（MCU / IoT / 端侧）

官方定位从「最小最便宜」到「最高性能 + 安全 + 端侧 AI」一条线。

| Core（架构） | FreeRTOS port | Arm 官方目标场景（原文归纳） |
| --- | --- | --- |
| **M0**（ARMv6-M） | `ARM_CM0` | 最小的 32 位微处理器；适合简单、成本敏感的设备，以及尺寸关键的智能互联嵌入式应用 |
| **M0+**（ARMv6-M） | `ARM_CM0` | 最小、功耗最低的 Cortex-M；适合传感器、可穿戴和各类低功耗应用 |
| **M3**（ARMv7-M） | `ARM_CM3` / `ARM_CM3_MPU` | 在面积/性能/功耗间优化；适合微控制器、汽车系统、无线网络与传感 |
| **M4**（ARMv7E-M） | `ARM_CM4F` / `ARM_CM4_MPU` | 低成本高性能的「数字信号控制」处理器；兼顾控制与信号处理 |
| **M7**（ARMv7E-M） | `ARM_CM7` | 该家族性能最强，带 DSP 与灵活接口；适合汽车、医疗、传感器融合、IoT |
| **M23**（ARMv8-M Baseline） | `ARM_CM23` / `_NTZ` | 最小、功耗最低且带 TrustZone 的 MCU；适合需要软件隔离与安全的智能互联应用 |
| **M33**（ARMv8-M Mainline） | `ARM_CM33` / `_NTZ` | 面向嵌入式与 IoT 市场，提供高效的安全与数字信号控制 |
| **M35P**（ARMv8-M Mainline） | `ARM_CM35P` / `_NTZ` | 首款内置防篡改（tamper resistance）的 Armv8-M 处理器；为 IoT 产品带来物理层安全 |
| **M52**（ARMv8.1-M） | `ARM_CM52` / `_NTZ` | 能效最高的 Armv8.1-M，带 Helium 向量处理；适合需要 DSP/ML 的成本敏感设计，如可穿戴、MCU、传感器 |
| **M55**（ARMv8.1-M） | `ARM_CM55` / `_NTZ` | 面向「端侧 AI（endpoint AI）」，带高级安全 + Helium；高效 DSP/ML |
| **M85**（ARMv8.1-M） | `ARM_CM85` / `_NTZ` | 性能最强的 Cortex-M，带 Helium + TrustZone；为关键应用提供高性能、增强的安全性与功能安全 |

## 二、Cortex-R 系列（实时 / 功能安全 / 存储与汽车）

官方关键词：**deterministic real-time、functional safety、fault tolerance**。

| Core（架构） | FreeRTOS port | Arm 官方目标场景（原文归纳） |
| --- | --- | --- |
| **R4**（ARMv7-R） | `CCS/ARM_Cortex-R4` | 顶级能效、成本与容错；用于汽车、相机、磁盘驱动器等嵌入式 |
| **R5**（ARMv7-R） | `ARM_CR5` / `ARM_CRx_MPU` | R4 的升级，增强错误管理、功能安全与 SoC 集成；适合实时安全关键系统 |
| **R8**（ARMv7-R） | `ARM_CRx_No_GIC` 类 | 为 LTE、5G 和存储提供顶级性能；11 级流水线、四核一致性 |
| **R52**（ARMv8-R） | `ARM_CRx_MPU` / `ARM_CRx_No_GIC` 类 | 最强 Cortex-R 之一，实时性能 + 高级安全；支持恶劣环境与医疗中的自主机器人（ML + 视觉） |
| **R52+**（ARMv8-R） | 同上 | 在 R52 基础上增强集成与虚拟化，面向功能安全应用，保持软件兼容 |
| **R82**（ARMv8-R AArch64） | `ARM_CR82` | 支持最高 1TB DRAM，高性能存储：SSD、HDD、内置存储、计算存储 |
| **R82AE**（ARMv8-R AArch64） | `ARM_CR82` 家族 | 面向 SDV（软件定义汽车）的 64 位实时 CPU，带安全、Linux、虚拟化 |

## 三、Cortex-A 系列（应用处理器 / 富操作系统）

官方定位：**虚拟内存管理、复杂任务、低功耗高性能、可跑 Rich OS**。

| Core（架构） | FreeRTOS port | Arm 官方目标场景（原文归纳） |
| --- | --- | --- |
| **A5 / A9**（ARMv7-A） | `ARM_CA9` / `ARM_CA5_No_GIC` | Cortex-A 系列（含 A5）定位：在低功耗、紧凑形态下为复杂任务提供高性能，并带虚拟内存管理；A9 为该系列早期应用处理器（已退役，官网产品页不再单列） |
| **A53**（ARMv8-A AArch64） | `ARM_AARCH64` / `ARM_CA53_64_BIT` | 应用最广的低功耗 64 位处理器；在受限功耗下处理复杂任务与高性能，支持富操作系统与应用 |

## 四、经典 ARM7 / ARM9（ARMv4T / ARMv5TE）

Arm 官方已列为**传统内核（legacy）**，不再作为新产品推荐，历史上用于早期 MCU/SoC：

- ARM7TDMI：`ARM7_AT91FR40008`、`ARM7_AT91SAM7S`、`ARM7_LPC2000`、`ARM7_LPC23xx`、`ARM7_LPC21xx`、`AtmelSAM7S64`
- ARM9 / ARM926EJ-S：`AtmelSAM9XE`、`STR9xx`（ARM966E-S）

FreeRTOS 对它们的移植属于维护性支持。

## 五、第三方 / 多核特殊移植

- `ThirdParty/GCC/RP2040`：树莓派 RP2040 的 **双核 Cortex-M0+（ARMv6-M）SMP** 移植，依赖 pico-sdk 的 `pico_multicore` 做核间调度。
- `ThirdParty/GCC/ARM_TFM`：与 TrustZone for Armv8-M 配合的 TF-M 集成。

## 三类 profile 的官方分工

- **M 系列**：微控制器 —— 从「最小最便宜（M0/M0+）」到「安全隔离（M23/M33/M35P）」再到「端侧 AI + 功能安全（M52/M55/M85）」。
- **R 系列**：实时与功能安全 —— 汽车、存储、工业、机器人，强调确定性、容错与安全认证。
- **A 系列**：应用处理器 —— 跑 Linux/Android 等富 OS，带 MMU 与虚拟内存，性能优先。

## 标准或资料引用

- Arm 官方产品总览：<https://www.arm.com/products/silicon-ip-cpu>
- Cortex-M：`https://www.arm.com/products/silicon-ip-cpu/cortex-m/cortex-m0`（`.../cortex-m23`、`.../cortex-m55` 等同理）
- Cortex-R：`https://www.arm.com/products/silicon-ip-cpu/cortex-r/cortex-r52`（`.../cortex-r82`、`.../cortex-r5` 等）
- Cortex-A：`https://www.arm.com/products/silicon-ip-cpu/cortex-a/cortex-a53`（`.../cortex-a5` 等）
- 注：`developer.arm.com` 有反爬（返回 403），故场景描述取自 arm.com 官方 CPU 产品页。
- 源码载体：FreeRTOS-Kernel `portable/` 目录（本地 `/home/congqiang/work/repo/FreeRTOS-Kernel`）。

## 与工作的关联

- 选型：ZynqMP（Cortex-A53 APU + Cortex-R5F RPU）正好横跨本笔记的 A 系列与 R 系列，见 [[概念-ZynqMP-PS-APU与RPU]]、[[实践-ZCU670-Linux与RPU-AMP]]。
- 移植：读 `portable/` 源码前先在此确认目标内核的架构代际与特性（FPU/MPU/TrustZone）。

## 待深入 / 疑问

- 各 port 的完整工具链矩阵（GCC / IAR / RVDS / ARMClang / CCS）尚未整理成表。
- Armv8-M 的 secure / non_secure 两套工程在 `portable/ARMv8M` 下的组织方式与实际编译流程待走读。

## 关联

- 主题入口：[[MOC-RTOS]]
- 代码走读：[[仓库-FreeRTOS-Kernel-核心层API与原理]]
- 学习路径：[[学习-RTOS-学习路线]]
- 平行对照：[[MOC-Linux]]
