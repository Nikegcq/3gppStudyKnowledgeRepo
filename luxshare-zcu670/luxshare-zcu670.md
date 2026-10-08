---
type: moc
tags: [FPGA, RFSoC, ZCU670, 硬件, luxshare, O-RU]
layer: L1
created: 2026-10-08
updated: 2026-10-08
status: active
source: AMD/Xilinx 官网 + 本机工程（yocto/images、luxshare-n78-bsp-project、work/repo/radiosw 等）
---

# luxshare-zcu670

ZCU670（Zynq UltraScale+ RFSoC DFE，XCZU67DR）相关的硬件参数、处理器架构与工程落地笔记。面向 Luxshare N78 / O-RU 这条线。

## 笔记清单

| 笔记 | 一句话 |
| --- | --- |
| [[ZCU670-PL-PS-参数]] | 板载器件、PL 资源、PS 特性、板级 DDR/GTR/GTY/时钟 |
| [[概念-ZynqMP-PS-APU与RPU]] | PS 里的 APU / RPU / PMU 各是什么，RPU 的 TCM、lockstep、能干什么 |
| [[实践-ZCU670-Linux与RPU-AMP]] | Linux 与 RTOS 同时跑的两种启用方式、通信机制、资源划分与验证清单 |
| [[概念-高端radio软件架构-Linux与RTOS分工]] | 高端 radio 的四类软件架构、硬实时放哪里、怎么选 |

## 硬件速查

**XCZU67DR-2FSVE1156I**（ZU67DR DFE 器件，速度等级 -2，FSVE1156 封装，工业级）

| 侧 | 关键参数 |
| --- | --- |
| PL | 489K 逻辑单元、1,872 DSP、67.8 Mb 片上存储、8 路 GTY（≤28.21 Gb/s）、最大 I/O 158 |
| RF | 8× 14-bit 2.95 GSPS + 2× 14-bit 5.9 GSPS RF-ADC；8× 14-bit 10 GSPS RF-DAC；内含 DFE 硬核（DUC/DDC、CFR、DPD、通道滤波、FFT/iFFT、PRACH） |
| PS | 四核 Cortex-A53 ≤1.33 GHz（APU，Linux）+ 双核 Cortex-R5F ≤533 MHz（RPU，RTOS/裸机）+ 三冗余 MicroBlaze PMU |
| 板级 | PS DDR4 SODIMM 4 GB（J48）/ PL DDR4 4 GB 32-bit（Bank 64-65）/ PS-GTR Bank 505（USB3.0 + FMC+） |

明细见 [[ZCU670-PL-PS-参数]]。

## 相关主题入口

- 采样率与带宽（n78 → 122.88 Msps → RFSoC 直采 vs AD9361）：[[概念-射频采样率-RFSoC与AD9361]]
- 射频软件栈（RFIC 驱动 → JESD → libiio/iiod）：[[概念-物理层射频驱动全景]]
- AD9361 寄存器与驱动：[[资源-AD9361-寄存器文档]]、[[学习-Linux-驱动开发-AD9361-从零到通]]
- 主题地图：[[MOC-FPGA]]、[[MOC-射频]]、[[MOC-Linux]]、[[MOC-RTOS]]
- n78 频点计算：[[概念-NR频率栅格-NR-ARFCN与GSCN]]

## 本机工程现状（2026-10-08）

| 位置 | 内容 |
| --- | --- |
| `~/work/repo/yocto/images/` | BOOT.BIN、bootgen.bif、pmufw.elf、bl31.elf、u-boot.elf、system.bit、system.dtb、Image |
| `~/work/repo/luxshare-n78-bsp-project/` | PetaLinux BSP（OpenAMP / rpmsg 包全部未使能） |
| `~/work/repo/radiosw/` | Linux 用户态 radio 控制软件（C++ / CMake / gRPC / DFE / fronthaul / 故障处理） |
| `~/work/repo/mplane`、`rusw`、`oru-controller` | O-RAN M-plane（NETCONF / YANG / `oran-yang`）与 O-RU 控制 |
| `~/work/repo/FreeRTOS-Kernel` | FreeRTOS 官方内核源码（配 [[MOC-RTOS]] 学习线） |

## 待补

- RPU 实测：搭一个最小 exemplar（Linux remoteproc 加载 + IPI 回环），测中断延迟与抖动
- DFE 硬核配置（RFDC IP、通道 - tile - JESD 链路映射）
- ZCU670 时钟树与 TDD 时序图（Excalidraw）
- 前传（eCPRI / 7-2 split）与 M-plane 的软件栈分层
