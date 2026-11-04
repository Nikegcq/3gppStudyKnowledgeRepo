---
type: moc
tags: [FPGA, 硬件]
created: 2026-09-03
updated: 2026-09-30
status: active
---

# MOC：FPGA

FPGA 设计在通信（尤其是 L1 物理层）中的应用地图。

## 基础知识

- 时序与资源：时钟域、时序收敛、资源估算
- 语言：Verilog / SystemVerilog / VHDL
  - [[学习-Verilog-Top.v顶层语法精读]]：参数、端口、实例化、IOBUF、常量
  - [[概念-Verilog-wire-reg-assign]]：类型、assign、阻塞/非阻塞、锁存器
  - [[概念-AXI-Stream握手与SystemVerilog]]：tvalid/tready 握手、always_comb/ff、interface
- 调试与验证：仿真、片上逻辑分析、UVM 基础

## 通信基带应用

- 数字中频：DDC / DUC、滤波
- 信号处理：FFT、FIR、同步、信道估计
- 信道编解码：LDPC / Polar / Turbo
- 高速接口：AXI、PCIe、以太网、JESD204B

## 工具链

- Xilinx Vivado / Vitis
- Intel Quartus
- 开放工具链（如开源仿真/综合工具）

## 实战工程（GAO 多卡采集）

以 Kintex-7 325T 真实工程为教材的学习线：

- 项目：[[计划-FPGA学习-GAO多卡采集工程]]
- 工程地图：[[仓库-GAO_325T-工程总览]]
- 架构与数据通路：[[仓库-GAO_325T-系统架构与数据通路]]
- 系统框图：[[图-GAO_325T-多卡采集系统框图.excalidraw]]
- 语法精读（Top.v）：[[学习-Verilog-Top.v顶层语法精读]]

## 相关

- [[领域-L1物理层]]
- [[MOC-射频]]（ADC/DAC 之后的数字侧）

