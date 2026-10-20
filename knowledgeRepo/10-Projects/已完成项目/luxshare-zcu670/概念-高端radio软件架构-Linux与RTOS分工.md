---
type: note
tags: [架构, RTOS, Linux, AMP, O-RU, gNB, radio, 实时, luxshare]
layer: L1
created: 2026-10-08
updated: 2026-10-08
status: active
source: 行业调研 + 本机工程证据（radiosw / mplane / rusw / PetaLinux BSP 配置）
---

# 概念：高端 radio 产品的软件架构（Linux 与 RTOS 怎么分）

## 一句话总结

**不是所有高端 radio 都"RTOS + Linux"。** 高端 radio 一定会在**硬件里划出一块硬实时域**，但那个域通常是 FPGA/ASIC/DFE，而不是 CPU；CPU 侧要不要再配一个 RTOS，取决于是否还有"硬件管不了、又必须确定性"的活儿。

## 1 四类架构并存

| 架构 | 典型使用者 | 硬实时放在哪 |
| --- | --- | --- |
| **A. Linux + FPGA/ASIC/DFE** | 大多数高性能 O-RU、RFSoC 平台、AMD ZCU670 DFE TRD（本机项目） | 全在 PL/ASIC 硬核里，CPU 不参与 |
| **B. Linux + RTOS（AMP）** | ZynqMP/RFSoC 上需要 CPU 侧确定性的设计、部分 O-RU/O-DU | RPU（R5F）跑 FreeRTOS/裸机，APU 跑 Linux |
| **C. 纯 RTOS / 裸机** | 大量 Split 7-2 的 RU、小基站、DSP modem、军用/卫星 SDR（VxWorks / FreeRTOS / ThreadX / Zephyr） | 直接在 CPU 上；启动毫秒级、无 Linux 攻击面 |
| **D. 纯 Linux（含 PREEMPT_RT）** | O-DU/O-CU、开源 gNB（srsRAN、OAI）、Intel FlexRAN 类 vRAN | 靠 PL/加速卡 + 实时内核调优（`isolcpus`、DPDK） |

变体：**同核 AMP**——用 Jailhouse/Xen 把 A53 四核切开，两核 Linux、两核裸机，车载/工业常见，ZynqMP 上 Jailhouse 是官方路径。

## 2 本机证据：一个真实 N78 O-RU 项目怎么分

| 位置 | 内容 | 说明 |
| --- | --- | --- |
| `~/work/repo/radiosw` | C++ / CMake / gRPC，含 `dfe`、`fronthual`、`faultHandler`、`carrierCtrl`、`CarrierCtrlServer`、`hal`、`drv` | **纯 Linux 用户态**的 radio 控制软件 |
| `~/work/repo/mplane`、`rusw`、`oru-controller`、`xmplane` | NETCONF / YANG / `oran-yang`、M-plane 服务 | 管理面天然属于 Linux |
| `~/work/repo/luxshare-n78-bsp-project/.../config` | `# CONFIG_SUBSYSTEM_ENABLE_OPENAMP_DTSI is not set` | **没有启用 OpenAMP** |
| 同上 `rootfs_config` | `openamp-fw-*`、`rpmsg-*` 全部 `is not set` | 没有 RPU 固件与测试工具 |
| `yocto/images/bootgen.bif` | 无 RPU 分区 | 纯 Linux + PL 启动 |

**结论：这个产品走的是 A 类架构**——硬实时交给 DFE/PL 硬核，CPU 只做控制面与管理面，完全没有引入第二个 OS。

## 3 怎么选（决策顺序）

1. 先问：有没有**非在 CPU 上做**、且抖动要求 **<10 µs** 的闭环？
   - 没有 → Linux 单系统；有 → 进入下一步
2. 能不能塞进 PL？能 → 放逻辑里（最省心）
3. 塞不进且在 CPU 上 → 启用 RPU（AMP）
4. 只有 50–100 µs 级要求 → Linux + PREEMPT_RT 就够

其他权重：

| 因素 | 倾向 Linux | 倾向 RTOS |
| --- | --- | --- |
| 实时性 | 几十 µs 抖动可接受 | 微秒级、抖动极小 |
| 启动时间 | 秒级可接受 | 毫秒级上电出射频 |
| 生态（NETCONF/gRPC/升级） | 强需求 | 用不上 |
| 成本/维护 | 一套工具链 | 可接受两套 |
| 认证（功能安全） | 一般不涉及 | lockstep RTOS 更易过 |

## 4 两个方向相反的趋势

- **混合架构变多**：ZynqMP/RFSoC/Versal 这类异构 SoC 让 AMP 成本骤降，以前要外挂 DSP 才有的实时通道，现在同一颗芯片里就有
- **但对 CPU 侧 RTOS 的需求在下降**：
  - DPD/CFR、DUC/DDC、eCPRI、TDD 时序越来越多硬化进 DFE/ASIC，硬实时压力从 CPU 搬走
  - PREEMPT_RT 已在 Linux 6.12 合入 mainline，"为了实时才上 RTOS"这条理由在弱化

## 5 对本项目的判断

- 现状（Linux + PL/DFE）不是"低端替代方案"，而是高性能 O-RU 的主流选择
- 只要 PL/DFE 承担了时隙时序与射频保护，就不要为了架构漂亮引入第二个 OS
- 真出现"CPU 侧硬实时"需求时，再按 [[实践-ZCU670-Linux与RPU-AMP]] 启用 RPU

## 相关笔记

- [[实践-ZCU670-Linux与RPU-AMP]]（AMP 的具体落地）
- [[概念-ZynqMP-PS-APU与RPU]]（RPU 能力边界）
- [[概念-物理层射频驱动全景]]（L1 软件栈分层）
- [[MOC-RTOS]]、[[MOC-O-RAN开源]]、[[MOC-射频]]
