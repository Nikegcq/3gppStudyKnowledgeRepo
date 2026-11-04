---
type: resource
tags: [FPGA, 多卡采集, Aurora, 以太网, 时钟域, 组包, GAO_325T]
created: 2026-09-30
updated: 2026-09-30
status: active
source: 系统框图 + prj_coloturm_325t RTL
---

# 仓库：GAO_325T 系统架构与数据通路

## 一句话总结

**1 主卡 + 最多 11 从卡**的分布式同步采集：主卡用 UDP 对上位机，用 MicroBlaze 写寄存器下发配置；从卡各自采 ADC，经 Aurora 回传带 `card_id`/`pkg_id` 的数据；主卡 `DATA_PROCESS` 收齐（或 3s 超时发 ERROR）后打统一 timestamp 成包送出。中间是 **32bit 轮询仲裁 + 异步 FIFO**，`dest` 决定通路，`last` 决定包界。

可编辑框图：![[图-GAO_325T-多卡采集系统框图.excalidraw]]

工程目录与寄存器分组见 [[仓库-GAO_325T-工程总览]]。

---

## 1. 主卡 vs 从卡

| | 主卡 | 从卡 |
| --- | --- | --- |
| 对外 | RJ45 / UDP → 上位机 | 无，只挂 Aurora |
| 处理器 | MicroBlaze（配置、组包策略、中断） | 也有 MB（收命令） |
| 采集 | 本地 ADC → `DATA_PROCESS` | 本地 ADC → Aurora 回传 |
| 板间 | 多路 AURARO（GTX）扇出/汇聚 | 1 路 AURARO |

RTL 对应：`SLAVE_CARD_N = 11`；`pkg_data_to_eth` 中 `card_num` ≤ 12；`post_reg_control` 配置 `card_master` / `card_id` / `card_mask_used`。

## 2. 控制面（配置 / 命令）

```text
上位机 UDP → receive_FIFO → Arbiter(u_udp_switch)
           → receive_FIFO_mb → intc → MB
MB → send_FIFO_mb（带 dest + last）
   → u_udp_send_switch → SWITCH
   → 各路 FIFO → AURARO → 从卡 MB
```

- `fifo_mb`：**AXI-Stream FIFO**（给 MB）
- 其余 FIFO：普通 FIFO（缓冲 + **跨时钟域**）
- 所有 Arbiter：**轮询**

## 3. 数据面（采集回传）

```text
从卡 ADC → send_FIFO_mb → Arbiter → AURARO
                ↓
主卡 AURARO → type check → data fifo → DATA_PROCESS
主卡 ADC ────────────────→ DATA_PROCESS
DATA_PROCESS → Arbiter → send_FIFO → UDP → 上位机
```

### DATA_PROCESS 多卡组包（`pkg_data_to_eth.v`）

1. 内部 **timestamp + 包 ID Gen**；
2. 等齐各卡：`r_recv_map == card_flag`（每卡 1 bit，MB 配 `card_num`）；
3. 从收到**第一张卡**起 **3s 定时**，超时未齐 → 发 **ERROR 包**；
4. 齐了才 `PACKAGE_HEAD` → `PACKAGE_DATA`；
5. 发完 **cardID 与 timestamp 清零**，等下一轮。

包头（`adc_post1.v`）：`{pkg_id, pkg_id[1:0], card_id, card_id, 8'hAA}`，并用 `card_mask` 记录在场卡。

## 4. 时钟域（读代码先看这个）

| 域 | 速率 | 主要模块 |
| --- | --- | --- |
| 以太网 | ~125 MHz | UDP/RGMII、`send_FIFO`/`receive_FIFO` 边界 |
| 系统 | 100 MHz | MB、SWITCH、Arbiter、DATA_PROCESS、寄存器 |
| Aurora | ~70 MHz | AURARO 及其前后 FIFO |

图中每个小 FIFO ≈ **CDC + 仲裁缓冲**，不只是深度缓冲。

## 5. 框图名称 ↔ RTL 对照

| 框图 | RTL |
| --- | --- |
| UDP / RJ45 | `eth_top` → `rgmii_to_gmii` + `eth` |
| u_udp_switch / Arbiter | `eth_switch_2s1m`（`u_switch_udp_recv`） |
| receive_FIFO_mb / send_FIFO_mb | `eth_sfifo_32b`（AXI-Stream 进/出 MB） |
| SWITCH（dest 选路） | `eth_switch_1s12m`（`u_mb_send_switch`） |
| AURARO | `aurora_top` / `GTX_FIFO_64B_Mod` / `aurora_64b66b_*` |
| type check | `aurora_recv_mux`：首拍 `tdata` 当 type，`tdest={3'h0,type}` |
| u_auraro_pkg / u_auraro_data | `aurora_switch_11s1m` 分出 code / data |
| DATA_PROCESS | `data_process_top` + `pkg_data_to_eth` + `adc_post*` |
| MB 控制窗 | `user_regs` + `MB_Ctrl` BD |

`data_process_top` 内：本地结果与 `aurora_data_*` 经 `data_process_switch_2s1m` 汇聚，再进 `pkg_data_to_eth`。

## 6. 单卡数据处理链（DATA_PROCESS 内部）

```text
ADC 原始(LVDS/SPI)
  → adc_top（ADS6243/ADS5562 + SelectIO + FIFO）
  → adc_lpf（sinc3 + dwt_denoise）
  → adc_delay（对齐）
  → adc_bias（偏置/基线，penalized_baseline、quick_select）
  → adc_trig / adc_trig_master（触发、窗口）
  → adc_post（成包）→ axis_post_pkg → pkg_data_to_eth
  → dac_top（反馈/校准）
```

算法重点：`dwt_*` Mallat 小波（8 个 FIR Compiler）+ `denoise_signal` 浮点阈值降噪。

## 7. 建议精读顺序

1. `pkg_data_to_eth.v`（约 300 行）—— 等卡 / 超时 / 组头
2. `aurora_recv_mux.v` —— type check、code/data 分流、11 路轮询
3. `eth_top.v` switch 网络 —— dest/last 选路
4. `adc_post1.v` —— 包头与 card_mask
5. `data_process_top` 算法链 —— LPF/DWT/触发

## 相关

- [[仓库-GAO_325T-工程总览]]
- [[图-GAO_325T-多卡采集系统框图.excalidraw]]
- [[计划-FPGA学习-GAO多卡采集工程]]
- [[MOC-FPGA]]
