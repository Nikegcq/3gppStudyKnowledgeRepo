---
type: resource
tags: [FPGA, SystemVerilog, AXI-Stream, 握手, 接口]
layer: L1
created: 2026-09-30
updated: 2026-09-30
status: active
source: GAO_325T 数据通路 / 通用 AXI4-Stream
---

# 概念：AXI-Stream 握手与 SystemVerilog

## 一句话

AXI-Stream 核心只有一条：**`tvalid && tready` 同时为 1 的上升沿完成一拍传输，否则数据必须保持**；SystemVerilog 用 `logic + always_comb/always_ff` 理清“谁驱动谁”。

## 背景 / 为什么重要

GAO 工程顶层有几十组 `tdata/tvalid/tready/tlast/tdest`（MB↔ETH、ETH↔Aurora、data_process↔ETH），全是同一握手模式的重复。写对握手，跨模块数据通路就不会丢包/粘包；SV 现代写法还能让接口和检查更清晰。

## 关键概念与流程

### 1. 握手规则

| 规则 | 含义 |
|------|------|
| 传输条件 | `clk` 上升沿且 `tvalid=1 && tready=1` |
| Valid 不得依赖 Ready | 主设备不能“看你 ready 我才 valid” |
| Valid 拉高后数据保持 | 直到 handshake 完成 |
| Ready 可以依赖 Valid | 从设备可以“有数据我才 ready” |
| `tlast` | 包/帧最后一拍 |

信号族（GAO 工程命名）：

| 信号 | 含义 |
|------|------|
| `tdata` | 数据 |
| `tvalid` / `tready` | 主/从握手 |
| `tlast` | 包结束 |
| `tdest` | 目的端口 |
| `tkeep` | 字节有效（`4'hf` = 4 字节全有效） |

### 2. 最小生产者（源）

要点：`if (m_tvalid && m_tready)` 才推进；`tready=0` 时寄存器不动。

```systemverilog
module producer #(
    parameter int PKG_LEN = 8
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    output logic        m_tvalid,
    input  logic        m_tready,
    output logic        m_tlast,
    output logic [31:0] m_tdata
);
    typedef enum logic [1:0] { S_IDLE, S_SEND } state_e;
    state_e      state;
    logic [31:0] beat_cnt, data_r;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; m_tvalid <= 1'b0; m_tlast <= 1'b0;
            beat_cnt <= '0; data_r <= '0; m_tdata <= '0;
        end else begin
            case (state)
                S_IDLE: begin
                    m_tvalid <= 1'b0; m_tlast <= 1'b0;
                    if (start) begin
                        state    <= S_SEND;
                        beat_cnt <= '0;
                        data_r   <= 32'hA5A5_0000;
                        m_tvalid <= 1'b1;
                        m_tdata  <= 32'hA5A5_0000;
                        m_tlast  <= (PKG_LEN == 1);
                    end
                end
                S_SEND: if (m_tvalid && m_tready) begin
                    if (m_tlast) begin
                        state <= S_IDLE; m_tvalid <= 1'b0; m_tlast <= 1'b0;
                    end else begin
                        beat_cnt <= beat_cnt + 1;
                        data_r   <= data_r + 1;
                        m_tdata  <= data_r + 1;
                        m_tvalid <= 1'b1;
                        m_tlast  <= (beat_cnt + 1 == PKG_LEN - 1);
                    end
                end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
```

### 3. 最小消费者（宿）

```systemverilog
module consumer (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        allow_in,     // 背压：0 = 堵住
    input  logic        s_tvalid,
    output logic        s_tready,
    input  logic        s_tlast,
    input  logic [31:0] s_tdata
);
    assign s_tready = allow_in;

    logic [31:0] sum;
    logic [15:0] beat_cnt, pkg_cnt;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum <= '0; beat_cnt <= '0; pkg_cnt <= '0;
        end else if (s_tvalid && s_tready) begin
            sum      <= sum + s_tdata;
            beat_cnt <= beat_cnt + 1'b1;
            if (s_tlast) begin
                beat_cnt <= '0;
                pkg_cnt  <= pkg_cnt + 1'b1;
            end
        end
    end
endmodule
```

### 4. Testbench 要点

- `always #5 clk = ~clk;` 产生时钟
- 中途拉低 `allow_in` 制造背压，观察 `tdata/tvalid` 是否冻结
- 监视器：`if (tvalid && tready) $display(...)`

### 5. SystemVerilog 对照表

| Verilog-2001 | SystemVerilog | 说明 |
|--------------|---------------|------|
| `wire` / `reg` | `logic` | 统一变量类型 |
| `always @(*)` | `always_comb` | 自动敏感、强制全覆盖 |
| `always @(posedge clk)` | `always_ff` | 时序检查更严 |
| `8'd0` | `'0` | 全 0，位宽自适应 |
| 无 | `unique case` | 互斥检查 |
| 扁平端口 | `interface` + `modport` | 接口打包 |

```systemverilog
interface axi_stream_if #(
    parameter int DATA_W = 32, DEST_W = 4
) (input logic clk, input logic rst_n);
    logic              tvalid, tready, tlast;
    logic [DATA_W-1:0] tdata;
    logic [DEST_W-1:0] tdest;
    modport master (output tvalid, tdata, tlast, tdest, input tready);
    modport slave  (input  tvalid, tdata, tlast, tdest, output tready);
endinterface
```

### 6. 多通道扁平总线（GAO 风格）

```verilog
wire [     SLAVE_CARD_N - 1 : 0] w_aurora_send_tvalid;
wire [32 * SLAVE_CARD_N - 1 : 0] w_aurora_send_tdata;

generate
  for (genvar i = 0; i < SLAVE_CARD_N; i++) begin : g_aurora
    assign w_aurora_send_tdata[i*32 +: 32] = ch_data[i];
    assign ch_tready[i] = w_aurora_send_tready[i];
  end
endgenerate
```

`base +: width`：从 `base` 起升序取 `width` 位。

### 7. 波形应看到什么

| 现象 | 含义 |
|------|------|
| `allow_in=1` | 数据连续走 |
| `allow_in=0` | `tready=0`，`tdata/tvalid` 冻结 |
| `tlast` 且握手 | 包结束 |
| 违反 valid 依赖 ready | 仿真可能仍跑，硬件会死锁/丢拍 |

## 与工作的关联

| GAO 信号 | 角色 |
|----------|------|
| `w_data_send_*` | data_process → eth_top |
| `w_mb_send_*` / `w_mb_recv_*` | MicroBlaze ↔ eth_top |
| `w_aurora_send_*`（扁平 11 路） | eth_top → aurora_top |
| `w_aurora_data_*` / `w_aurora_code_*` | aurora 复用后数据/控制 |

## 待深入 / 疑问

- [ ] 在 WSL 用 iverilog 把 producer/consumer/tb 跑通，抓波形
- [ ] 把 GAO 某条真实握手（如 `data_send_*`）标出 master/slave 与打拍位置
- [ ] 工程能否逐步迁移到 `axi_stream_if` interface

## 关联

- [[概念-Verilog-wire-reg-assign]]
- [[学习-Verilog-Top.v顶层语法精读]]
- [[仓库-GAO_325T-系统架构与数据通路]]
- [[MOC-FPGA]]
