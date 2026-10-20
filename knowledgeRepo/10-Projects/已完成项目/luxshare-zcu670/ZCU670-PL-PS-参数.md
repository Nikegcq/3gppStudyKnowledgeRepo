---
type: resource
tags: [FPGA, RFSoC, ZCU670, 硬件, luxshare]
layer: L1
created: 2026-10-08
updated: 2026-10-08
status: active
source: AMD/Xilinx 官网（ZCU670 产品页、UG1532 用户指南、Zynq UltraScale+ RFSoC 器件规格表）
---

# ZCU670 PL / PS 参数

## 一句话总结

ZCU670 板载 **XCZU67DR-2FSVE1156I**（Zynq UltraScale+ RFSoC **DFE** 系列）：PL 侧 489K 逻辑单元、1872 个 DSP、67.8 Mb 片上存储、8 路 GTY，并集成 8×2.95 GSPS + 2×5.9 GSPS RF-ADC 与 8×10 GSPS RF-DAC；PS 侧为四核 Cortex-A53（≤1.33 GHz）+ 双核 Cortex-R5F（≤533 MHz）。

## 1 器件型号

**XCZU67DR-2FSVE1156I**

| 字段 | 含义 |
| --- | --- |
| ZU67DR | Zynq UltraScale+ RFSoC DFE 器件 |
| -2 | 速度等级 2 |
| FSVE1156 | 封装（1156 球） |
| I | 工业级温度 |

## 2 PL（可编程逻辑）参数

| 项目 | 参数 |
| --- | --- |
| System Logic Cells | 489 K |
| DSP Slices | 1,872 |
| 片上存储（Block RAM + UltraRAM） | 67.8 Mb |
| GTY 收发器 | 8 路（最高 28.21 Gb/s） |
| 100G Ethernet MAC/PCS（含 RS-FEC） | 1 |
| 最大 I/O 引脚 | 158（器件系列表给 154） |
| RF-ADC | 8× 14-bit 2.95 GSPS + 2× 14-bit 5.9 GSPS |
| RF-DAC | 8× 14-bit 10 GSPS |
| DFE 硬核 IP | 通道滤波器、DUC/DDC、混频器、CFR、复数均衡器、PQ、重采样器、DPD |
| Low-PHY 硬核 IP | FFT/iFFT、PRACH |
| SD-FEC | 0（无） |
| PCIe | 无 Gen3x16 / Gen4x8 / CCIX |

RF 采样链支持 1x/2x/3x/4x/5x/6x/8x/10x/12x/16x/20x/24x/40x 抽取与内插，最大射频输入频率 7.125 GHz；10 GSPS DAC 需联系 AMD 销售确认支持。

## 3 PS（处理系统）参数

| 项目 | 参数 |
| --- | --- |
| 应用处理器（APU） | 四核 Arm Cortex-A53 MPCore，最高 1.33 GHz |
| 实时处理器（RPU） | 双核 Arm Cortex-R5F MPCore，最高 533 MHz |
| 片上存储器 | 256 KB OCM（带 ECC） |
| 外部存储接口 | DDR4 / DDR3 / DDR3L / LPDDR4 / LPDDR3、Quad-SPI、NAND、eMMC |
| 高速连接 | 4× PS-GTR、PCIe Gen1/2、SATA 3.1、DisplayPort 1.2a、USB 3.0、SGMII |
| 通用连接 | 214 PS I/O、UART、CAN、USB 2.0、I2C、SPI、32-bit GPIO、RTC、看门狗、TTC |
| GPU | 官方 DFE 器件规格表未列（带 GPU 的型号会单列 Mali-400 MP2） |

## 4 板级 PL / PS 接口（UG1532）

- **PS DDR4**：J48 SODIMM 插槽，64-bit 单 rank，随板配 Micron MTA4ATF51264HZ-2G6E1（4 GB，2666 MT/s 模组；ZU67DR 器件本身支持 2400 MT/s），挂在 DDRC Bank 504。
- **PL DDR4**：4× Micron MT40A1G8SA-075 = 4 GB、32-bit，接 PL Bank 64/65，0.6 V VTT 端接。
- **PS-GTR（Bank 505）**：lane 2 → USB 3.0（host only）；lane 0/1/3 → FMC+（J28）。
- **GTY 收发器**：8 路，主要通过 FMC+ / zSFP+ 引出。
- **时钟**：SI5381A 十路任意频率时钟发生器（U43）供 PS-GTR 参考时钟，另有 SI570 可编程用户时钟与用户 SMA 时钟输入。
- **整机**：+12 V DC 供电，工作温度 0–45 °C，存储 –25–+60 °C，板尺寸 12.225 × 10.675 英寸。

## 5 官方来源

- 板卡产品页（含器件规格表）：[ZCU670 Evaluation Kit](https://www.amd.com/en/products/adaptive-socs-and-fpgas/evaluation-boards/zcu670.html)
- 板级用户指南：[UG1532 ZCU670 Evaluation Board User Guide](https://docs.amd.com/r/en-US/ug1532-zcu670-eval-bd)
- 器件系列规格表：[Zynq UltraScale+ RFSoC](https://www.amd.com/en/products/adaptive-socs-and-fpgas/soc/zynq-ultrascale-plus-rfsoc.html)
- 产品简介 PDF：[zcu670-product-brief.pdf](https://www.amd.com/content/dam/amd/en/documents/products/adaptive-socs-and-fpgas/boards-kits/product-briefs/zcu670-product-brief.pdf)
- UG1532 中引用的补充文档：DS926（DC/AC 特性）、DS889（RFSoC Overview）、UG1085（TRM，PS 细节）、UG583（PCB 设计）、PG150（Memory IP）

## 6 待确认

- 最大 I/O 引脚数两处官方页面不一致（ZCU670 产品页 158 / RFSoC 器件系列表 154），如需精确值以板级 XDC 与 UG1532 为准。
- ZU67DR 的 PS 是否含 GPU：DFE 器件规格表未列，需查 DS889 或 UG1085 确认。

## 相关笔记

- [[概念-物理层射频驱动全景]]
