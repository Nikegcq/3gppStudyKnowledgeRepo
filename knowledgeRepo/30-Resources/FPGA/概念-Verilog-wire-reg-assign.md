---
type: resource
tags: [FPGA, Verilog, wire, reg, assign, 基础语法]
layer: L1
created: 2026-09-30
updated: 2026-09-30
status: active
source: GAO_325T Top.v / 通用 Verilog
---

# 概念：Verilog wire / reg / assign

## 一句话

`wire` 是导线，由 `assign` 或子模块输出驱动；`reg` 是变量，只能在 `always`/`initial` 里赋值；`assign` 是连续赋值，只驱动 `wire`。**`reg` 不一定是寄存器**——要不要 FF 看是不是 `always @(posedge clk)`。

## 背景 / 为什么重要

这是 Verilog 最容易混的一组概念。类型选错会直接综合报错，`=` / `<=` 用错会导致仿真与硬件不一致。GAO 工程顶层里大量 `wire` 互连、少量 `reg` 打拍、`assign` 做常量/广播，模式非常典型。

## 关键概念与流程

### 三者关系

| | `wire` | `reg` |
|--|--------|-------|
| 本质 | 网络（导线） | 变量 |
| `assign` 驱动 | 能 | **不能** |
| `always` 赋值 | **不能** | 能 |
| 作子模块输出连接 | 能 | 不能 |
| 综合成什么 | 连线 / 组合 / 寄存器 | 组合 / 寄存器 / 锁存器 |

**谁能驱动 `wire`：** `assign`、子模块输出端口、原语输出（如 `IOBUF.O`）。

### 场景 A：纯组合（wire + assign）

```verilog
module mux_assign (
    input  wire [7:0] a, b,
    input  wire       sel,
    output wire [7:0] y
);
    wire [7:0] and_r = a & b;
    wire [7:0] or_r  = a | b;
    assign y = sel ? and_r : or_r;
endmodule
```

全是 LUT，无时钟、无寄存器。

### 场景 B：模块互连（Top.v 风格）

```verilog
wire [31:0] w_data_send_tdata;
wire        w_data_send_tvalid;

data_process_top u_data (
    .data_eth_tdata (w_data_send_tdata), ...
);
eth_top u_eth (
    .data_send_tdata (w_data_send_tdata), ...
);
```

`wire` 就是模块之间的网线。

### 场景 C：时序逻辑 → 真正的寄存器

```verilog
module counter (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    output reg  [7:0] cnt
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)      cnt <= 8'd0;
        else if (en)     cnt <= cnt + 8'd1;
    end
endmodule
```

综合结果：8 个触发器 + 加法器。输出是 `reg` 才能在过程块被赋值。

### 场景 D：reg 做组合（不是寄存器）

```verilog
reg [7:0] y;
always @(*) begin
    case (sel)
        2'b00:   y = a;
        2'b01:   y = b;
        2'b10:   y = c;
        default: y = 8'd0;
    endcase
end
```

`always @(*)` 无时钟 → 纯 LUT。

### 场景 E：锁存器（Latch）——通常要避免

```verilog
reg y;
always @(*) begin
    if (en) y = a;   // en=0 时保持 → 推断 LATCH
end
```

**原则：组合 `always` 必须赋完整；要“保持”就用 `always @(posedge clk)`。**

### 场景 F：打拍（工程最高频写法）

```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_d1  <= 8'd0;
        valid_d1 <= 1'b0;
    end else begin
        data_d1  <= data_in;
        valid_d1 <= valid_in;
    end
end
```

用途：时序收敛、跨时钟域同步、流水线对齐。

### assign 常用形态

```verilog
assign y = a & b;                          // 组合
assign {cout, sum} = a + b;                // 拼接目标
assign version_date = FPGA_VERSION_A;      // 常量绑定
assign adc_reset_o  = {(ADC_N+1){w_adc_reset}};  // 复制广播
assign io_pin = oe ? out_data : 1'bz;      // 三态
```

### 阻塞 `=` vs 非阻塞 `<=`

| 符号 | 场景 | 语义 |
|------|------|------|
| `=` | 组合 `always`、`initial` | 立即更新 |
| `<=` | 时序 `always @(posedge)` | 时钟沿统一更新 |

```verilog
// 时序：必须 <=（交换 a/b）
always @(posedge clk) begin
    a <= b;
    b <= a;
end
```

### 端口类型合法组合

| 端口 | 类型 | 驱动 |
|------|------|------|
| `input` | 通常 `wire` | 外部 |
| `output` | `wire` 或 `reg` | wire→assign/实例；reg→always |
| `inout` | `wire` | 三态 assign / IOBUF |

### 常见错误速查

| 错误 | 后果 | 正确 |
|------|------|------|
| `assign` 驱动 `reg` | 不合法 | 改 `wire` 或 `always` |
| `always` 赋值 `wire` | 不合法 | `output reg` |
| 时序块用 `=` | 仿真/综合不一致 | 改 `<=` |
| 组合漏分支 | 推断 latch | 补 `else` |
| 两条 `assign` 同一 wire | 多驱动 | 单一驱动源 |

## 与工作的关联

GAO `Top.v` 实证：

```verilog
wire [31:0] w_mb_recv_tdata;          // 模块互连
reg  [7:0]  udp_rx_tdata;             // always 中间缓存
assign aurora_channel_up_status = gtx_channel_up;  // 状态回读
```

## 待深入 / 疑问

- [ ] SystemVerilog `logic` 如何统一 wire/reg（见 [[概念-AXI-Stream握手与SystemVerilog]]）
- [ ] 多时钟域 `wire` 传递是否必须打两拍同步

## 关联

- [[学习-Verilog-Top.v顶层语法精读]]
- [[概念-AXI-Stream握手与SystemVerilog]]
- [[MOC-FPGA]]
