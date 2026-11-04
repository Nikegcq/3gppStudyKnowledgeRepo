---
type: resource
tags: [FPGA, Verilog, 语法, GAO_325T, 顶层模块]
layer: L1
created: 2026-09-30
updated: 2026-09-30
status: active
source: GAO_325T Top.v
repo: /home/nick/work/fpgaPro/prj_colotrum/prj_coloturm_325t/GAO_325T.srcs/sources_1/new/Top.v
---

# 学习：Verilog 顶层语法 — Top.v 精读

## 一句话

`Top.v` 是参数化 ANSI 风格 Verilog 顶层：用 `#(parameter)` 做可配置，用 `input/output/inout` + 位宽表达式描述芯片管脚，用子模块实例化把 MicroBlaze、以太网、ADC、Aurora 拼成整机。

## 背景 / 为什么重要

读 FPGA 工程的第一站永远是顶层。看懂 `Top.v` 就能画出系统框图、知道管脚怎么接、参数怎么改、数据怎么流。本文以 GAO_325T 真实工程为教材拆语法。

相关：[[仓库-GAO_325T-工程总览]]、[[仓库-GAO_325T-系统架构与数据通路]]

## 关键概念与流程

### 1. 文件头编译指令

```verilog
`timescale 1ns / 1ps
`include "version_date.v"
```

| 语法 | 含义 |
|------|------|
| `` `timescale 1ns / 1ps `` | 时间单位 1ns，仿真精度 1ps |
| `` `include "..." `` | 文本级包含，常放版本宏 |
| 反引号 `` ` `` | 编译指令前缀，不是信号名 |

### 2. 模块声明 + 参数化端口

```verilog
module Top #(
    parameter ADC_N = 8,          /* adc chip number */
    parameter GT_CHANNEL_N = 3,
    parameter SLAVE_CARD_N = 11
)(
    input           CLK_IN1_clk_n,
    output [14:0]   DDR3_addr,
    inout  [31:0]   DDR3_dq,
    ...
);
```

**参数列表 `#(parameter ...)`**

- ANSI 风格参数，实例化时可用 `#(.ADC_N(4))` 覆盖
- 参数是编译期常量，用于位宽、数量等可配置项

**位宽 `[msb : lsb]`**

| 写法 | 含义 |
|------|------|
| `[14 : 0]` | 15 位，0 是最低位 |
| `[0 : 0]` | 1 位向量（Xilinx MIG 接口习惯） |
| `[GT_CHANNEL_N - 1 : 0]` | 参数化位宽 = 3 |
| `[GT_CHANNEL_N * GT_LANE_N - 1 : 0]` | 表达式位宽 = 3×4 = 12 |
| `[ADC_N * ADC_LANE - 1 : 0]` | 8×8 = 64 |

**端口方向**

| 关键字 | 含义 |
|--------|------|
| `input` | 输入 |
| `output` | 输出 |
| `inout` | 双向（DDR3 `dq`、QSPI flash、MDIO） |

### 3. `localparam` 本地参数

```verilog
localparam C_NUM_REG    = 64;
localparam C_SLV_DWIDTH = 32;
```

| | `parameter` | `localparam` |
|--|-------------|--------------|
| 实例化可覆盖 | 能 | **不能** |
| 用途 | 对外可配 | 模块内部常量 |

### 4. 子模块实例化

```verilog
MB_Ctrl MB_Ctrl_i (
  .CLK_IN1_clk_n (CLK_IN1_clk_n),
  .SPI_0_0_io0_i (1'b0),      // 接常量
  .SPI_0_0_io0_t (),          // 悬空
  ...
);

eth_top #(
    .TIME_20MS (20_000_000),  // 数字下划线分隔
    .IP_TYPE   (16'h0800)
) eth_top_inst ( ... );
```

| 写法 | 含义 |
|------|------|
| `.port(sig)` | 命名关联（推荐，可乱序） |
| `.port()` | 悬空 |
| `.port(1'b0)` | 接常量 |
| `.port(~eth_arp_req[0])` | 接表达式 |
| `#( .P(v) )` | 参数覆盖 |

### 5. FPGA 原语 `IOBUF`

```verilog
IOBUF flash_spi_io0_iobuf (
    .I  (flash_spi_io0_o),   // 内部 → 管脚
    .IO (qspi_flash_mosi),   // 双向管脚
    .O  (flash_spi_io0_i),   // 管脚 → 内部
    .T  (flash_spi_io0_t)    // 1=高阻，0=输出使能
);
```

用在 QSPI Flash 的 4 根双向线（`mosi/miso/wp/hold`）上。`inout` 端口必须配 `IOBUF`（或等价三态）才能真正双向。

### 6. 位拼接与重复

```verilog
assign adc_reset_o = {(ADC_N + 1){w_adc_reset}};  // 重复
.board_mac ({eth_board_mac_high[15:0], eth_board_mac_low})  // 拼接
```

| 语法 | 含义 |
|------|------|
| `{N{expr}}` | 重复 N 次 |
| `{a, b, c}` | 拼接，左高右低 |
| `base +: width` | 升序索引切片（多通道总线常用） |

### 7. 常量字面量

格式：**`<位宽>'<进制><数字>`**

| 例子 | 含义 |
|------|------|
| `1'b0` / `1'b1` | 1 位二进制 |
| `4'hf` | 4 位十六进制 |
| `16'h0800` | 16 位 |
| `20_000_000` | 十进制，下划线仅可读性 |

进制字符：`b` 二进制、`o` 八进制、`d` 十进制、`h` 十六进制。

### 8. 顶层架构一览

| 区域 | 作用 |
|------|------|
| `MB_Ctrl` | MicroBlaze + DDR3 + UART + SPI，时钟/复位源 |
| `user_regs` | 软件可读写配置/状态寄存器 |
| `user_gpio` | 拨码开关、板级主从、ADC 复位 |
| `eth_top` | UDP/ARP，与 MB、Aurora、数据处理互通 |
| `data_process_top` | ADC 采集、DAC、去噪、组包 |
| `LMK04828_*` | 两片时钟芯片 SPI 配置（级联） |
| `aurora_top` + `aurora_recv_mux` | 多从卡高速串行链路 |
| `ila_fb_addr` | 在线逻辑分析仪探针 |

### 9. 命名约定（工程习惯）

| 模式 | 含义 |
|------|------|
| `w_` | wire |
| `_n` / `_p` | 差分负/正 |
| `_i` / `_o` | input / output |
| `_o_n` / `_oe_n` | 低有效输出 / 输出使能 |
| `_inst` | 实例名 |
| `*_tdata/tvalid/tready` | AXI-Stream 风格 |

## 与工作的关联

- 直接对应 GAO 多卡采集工程学习线：[[计划-FPGA学习-GAO多卡采集工程]]
- 读懂顶层后可继续拆 `eth_top`、`data_process_top` 内部状态机
- 改通道数/从卡数只需改 `GT_CHANNEL_N`、`SLAVE_CARD_N` 等参数

## 待深入 / 疑问

- [ ] `MB_Ctrl` 内部 MicroBlaze 子系统时钟树如何生成 `clk_mb_50/100/125/200m`
- [ ] `user_regs` 的 Bus2IP 寄存器映射表（64 个 `C_NUM_REG` 如何分配）
- [ ] 中文注释乱码：文件编码是 GBK，Vivado 切换编码可恢复

## 关联

- [[概念-Verilog-wire-reg-assign]]
- [[概念-AXI-Stream握手与SystemVerilog]]
- [[仓库-GAO_325T-系统架构与数据通路]]
- [[MOC-FPGA]]
