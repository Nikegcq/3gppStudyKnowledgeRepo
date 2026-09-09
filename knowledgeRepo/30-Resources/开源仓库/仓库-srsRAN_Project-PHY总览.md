---
type: resource
tags: [开源, srsRAN, PHY, O-RAN]
repo: srsRAN_Project
repo_url: https://github.com/srsran/srsRAN_Project
local_path: /home/nick/work/repo/srsRAN_Project
created: 2026-09-03
updated: 2026-09-03
status: active
---

# srsRAN_Project PHY 总览与代码地图（深化版）

> 入口仓库：[[仓库-srsRAN_Project]]；协议入口：[[领域-L1物理层]]
> 本文所有“入口/方法名”均按本机 `include/srsran/phy/` 与 `lib/phy/` 实际代码核对。

## 1. PHY 在整机里的位置

```
MAC（lib/mac + lib/scheduler：调度决策、HARQ 管理）
   │  FAPI（lib/fapi_adaptor）
   │    MAC 侧：mac_pdu_handler / mac_cell_slot_handler / mac_cell_result_notifier 等
   │    PHY 侧：phy_fapi_adaptor / phy_fapi_{p5,p7}_sector_adaptor（另有 *fastpath* 变体）
   ▼
upper_phy  （lib/phy/upper，接口 include/srsran/phy/upper/）
   │  downlink_processor_pool ── PDU → 资源网格
   │  uplink_processor_pool   ── 网格/符号 → PDU（TB、UCI、测量）
   │  资源网格池 resource_grid_pool（lib/phy/support）
   ▼
lower_phy  （lib/phy/lower，接口 include/srsran/phy/lower/）
   │  OFDM 调制/解调、符号级基带处理、CFO/时偏/幅度控制
   ▼
radio（Split-8：UHD/ZMQ） 或  RU + OFH（Split-7.2x：lib/ru + lib/ofh）
```

对应关系：

- 3GPP：gNB = CU（CU-CP/CU-UP）+ DU；PHY 属于 DU 的 L1，向上与 MAC（F1 之内）衔接（TS 38.300/38.401）
- O-RAN：Split-8 = PHY 射频功能全在 DU 内（`lib/radio`）；Split-7.2x = PHY 高低切分，DU 保留上 PHY+部分下 PHY，RU 通过 `lib/ofh`（Open Fronthaul：以太网/Ethernet、eCPRI、压缩）连接
- 应用层：`apps/gnb`（一体）、`apps/du`（DU）、`apps/du_low`（7.2x 的 DU-Low 形态）

## 2. 上 PHY 接口清单（代码核对）

| 接口（include 路径） | 关键方法 | 说明 |
| --- | --- | --- |
| `phy/upper/upper_phy.h` | `get_rx_symbol_handler()`、`get_timing_handler()`、`get_downlink_processor_pool()`、资源网格池/error/metrics 等 getter | 上 PHY 门面；实现 `lib/phy/upper/upper_phy_impl.cpp` |
| `upper_phy_timing_handler.h` | `handle_tti_boundary()`、`handle_ul_half_slot_boundary()`（第 7 OFDM 符号）、`handle_ul_full_slot_boundary()`（第 14 符号） | 时隙/半时隙边界事件；下行准备与上行“收包截止”都挂在这里 |
| `upper_phy_rx_symbol_handler.h` | `handle_rx_symbol(context{sector,slot,symbol}, grid, is_valid)`、`handle_rx_prach_window()` | 每个上行 OFDM 符号到达的通知；PRACH 单独走 window |
| `downlink_processor.h` | `downlink_processor_pool::get_processor_controller(slot)` → `configure_resource_grid(context, grid)` 返回 `unique_downlink_processor`；接口 `process_ssb/process_pdcch/process_pdsch(data,pdu)/process_nzp_csi_rs/process_prs`；`finish_processing_pdus()` | 下行“取时隙处理器 → 配置网格 → 逐 PDU 处理 → 完成发网格”的 RAII 语义 |
| `downlink_pdu_validator`（同文件） | `is_valid(ssb/pdcch/pdsch/csi-rs/prs)` | 每个下行 PDU 参数先校验再处理 |
| `uplink_processor.h` | `get_slot_processor(slot)`、`get_pdu_slot_repository(slot)` | 上行时隙处理器与 PDU 仓库池 |
| `uplink_request_processor.h` | `process_prach_request()`、`process_uplink_slot_request(context, grid)` | 调度器/适配器发起的上行处理请求 |
| `uplink_slot_processor.h` | `handle_rx_symbol(end_symbol_index, is_valid)`、`process_prach()`、`discard_slot()` | 到达指定符号后真正触发 PUSCH/PUCCH/SRS 处理 |

实现侧重点文件：`upper_phy_impl.cpp`、`upper_phy_rx_symbol_handler_impl.cpp`、`downlink_processor_pool_impl.cpp`、`downlink_processor_multi_executor_impl.*`、`uplink_processor_impl.cpp`、`uplink_request_processor_impl.cpp`、`uplink_processor_fsm.h`、`uplink_pdu_slot_repository_impl.h`。

## 3. 下 PHY 接口清单（代码核对）

| 接口 | 关键方法 | 说明 |
| --- | --- | --- |
| `lower_phy.h` | `get_downlink_handler()`、`get_uplink_request_handler()`、`get_controller()`、TX/RX 的 CFO/中心频点/时偏控制器 | lower PHY 门面 |
| `lower_phy_downlink_handler.h` | `handle_resource_grid(context, grid)` | 接收上 PHY 整时隙网格 → OFDM 调制 → 基带 |
| `lower_phy_uplink_request_handler.h` | `request_uplink_slot(context, grid)`、`request_prach_window(context, buffer)` | 上 PHY 先“预约”上行时隙/PRACH，采样到了按预约填充 |
| `lower_phy_timing_notifier.h` | `on_tti_boundary()`、`on_ul_half_slot_boundary()`、`on_ul_full_slot_boundary()` | 把无线帧/时隙定时事件送给上 PHY timing handler |
| `lower_phy_rx_symbol_notifier.h` | `on_rx_symbol(context, grid, is_valid)`、`on_rx_prach_window()` | 每符号解调完成后通知上 PHY |

实现侧重点：`lib/phy/lower/lower_phy_impl.cpp`；上行基带采样处理在 `processors/uplink/uplink_processor_impl.cpp`（方法含 `process_symbol_boundary()`、`process_collecting()`、`process_alignment()`）；下行基带在 `processors/downlink/downlink_processor_baseband_impl.cpp`；OFDM 在 `lower/modulation/ofdm_{modulator,demodulator}_impl.*`。

## 4. 下行时隙处理细节（代码路径）

调用顺序（名字均来自接口头）：

1. lower PHY 在无线帧边界产生 `on_tti_boundary()` → 上 PHY `upper_phy_timing_handler::handle_tti_boundary()`：该时隙的下行窗口打开
2. MAC 侧经 FAPI 下发本时隙各 PDU（SSB/PDCCH/PDSCH/CSI-RS/PRS）与 TB 数据
3. `downlink_processor_pool::get_processor_controller(slot)` 取到该时隙的控制器
4. `downlink_processor_controller::configure_resource_grid(context, grid)` 绑定时隙资源网格，返回 RAII 句柄 `unique_downlink_processor`——出作用域即表示“该时隙 PDU 全部提交完毕”
5. 期间依次调用（`downlink_processor` 接口）：
   - `process_ssb(pdu)` → `ssb_processor_impl`（PBCH 编码/调制、PSS/SSS）
   - `process_pdcch(pdu)` → `pdcch_processor_impl`
   - `process_pdsch(data, pdu)` → `pdsch_processor_impl` 或流水线版 `pdsch_processor_flexible_impl`（多 TB 用 `static_vector<shared_transport_block, MAX_NOF_TRANSPORT_BLOCKS=2>`）
   - `process_nzp_csi_rs(config)` / `process_prs(config)`
   PDU 参数一致性由 `downlink_pdu_validator` 按类型提供 `is_valid()`（ssb/pdcch/pdsch/csi-rs/prs）；
   处理结果写入 `resource_grid_writer`
6. `finish_processing_pdus()` 后，整时隙网格经 gateway 交给 `lower_phy_downlink_handler::handle_resource_grid()`，由 OFDM 调制器变成基带采样

各 PDU 内部处理链分别见：

- [[仓库-srsRAN_Project-下行物理信道与OFDM发射]]
- [[仓库-srsRAN_Project-信道编码与速率匹配]]

实现多执行器版本 `downlink_processor_multi_executor_impl`：一个时隙内不同 PDU/不同码块可交给不同 executor 并行，最后由完成回调汇总。

## 5. 上行时隙处理细节（代码路径）

1. 调度器提前把本时隙的接收配置（PUSCH/PUCCH/SRS 的 PDU 参数）放进 `uplink_pdu_slot_repository`（每时隙一个仓库，`get_pdu_slot_repository(slot)`）
2. lower PHY 收基带采样：OFDM 解调逐符号/逐天线端口写入上行资源网格；每解出一个符号就 `lower_phy_rx_symbol_notifier::on_rx_symbol()` → 上 PHY `upper_phy_rx_symbol_handler::handle_rx_symbol()`（context 带 sector/slot/symbol）
3. 上 PHY 按符号推进；到第 7/14 个 OFDM 符号时，timing handler 触发 `handle_ul_half_slot_boundary()/handle_ul_full_slot_boundary()`，由 `uplink_slot_processor::handle_rx_symbol(end_symbol_index, is_valid)` 启动“已收满”信道的处理：
   - PUSCH：DM-RS 信道估计 → 均衡 → 解调 → UCI/数据分离 → 译码（详见 [[仓库-srsRAN_Project-上行接收与信道估计]]）
   - PUCCH：按格式检测/解调出 HARQ-ACK、SR、CSI
   - SRS：信道探测
4. PRACH 不走普通符号路径：`handle_rx_prach_window()` / `process_prach()` 按 preamble 窗处理（`prach_buffer` 上下 PHY 共享）
5. 结果（TB、CRC、UCI、测量）经 `upper_phy_rx_results_notifier` 回 FAPI/MAC；MAC 据此做 HARQ 重传、链路自适应

本机未提交文件 `upper_phy_rx_dci_extractor_decorator.*` 挂在上行 RX 结果/PDCCH 提取路径上（自行核对是否接入工厂）。

## 6. 并发与资源管理模型

- **池化**：`downlink_processor_pool`、`uplink_processor_pool`、`resource_grid_pool`、`rx_buffer_pool` 都按“时隙 + 容量”预分配，避免运行时高频 malloc
- **RAII 生命周期**：`unique_downlink_processor` 出作用域 = 该时隙不再接受新 PDU，配合 `finish_processing_pdus()` 保证网格在全部 PDU 完成后才下发
- **执行器**：`upper_phy_executor` / `task_executor`（`upper_phy_execution_configuration.h`）把多时隙/多 PDU 处理分发到线程池；多执行器下行实现是研究“PHY 并行化”的入口
- **共享传输块**：`shared_transport_block`（MAC TB → PHY 编码的零拷贝/共享语义）
- **软缓冲**：`rx_buffer_pool` 保存每 UE/每 HARQ 进程的 LLR，重传软合并
- **指标**：`upper_phy_metrics`/各 processor metrics（EVM、编码时间等）由 metrics collector 汇总，可接 srslog

## 7. FAPI 与切分再梳理

- MAC↔PHY 边界：`lib/fapi_adaptor` 里 `include/srsran/fapi_adaptor/mac/`（MAC 侧处理器：`mac_pdu_handler`、`mac_cell_slot_handler`、结果回调等）与 `include/srsran/fapi_adaptor/phy/`（PHY 侧 `phy_fapi_adaptor`、p5/p7 sector adaptor、fastpath 版本）
- p5/p7 目录对应 FAPI 内部不同层级的 PDU 集合；`*fastpath*` 用于低时延直连路径
- 越往 RU 走：`lib/ru`（RU 抽象：定时、IQ 流）→ `lib/ofh`（Split 7.2：以太网/eCPRI、压缩、定时对齐），配置形态决定走 `lib/radio` 还是 OFH
- 团队文档 `docs/mac_to_ofh_sequence.md/.puml` 正好覆盖“MAC 调度 → FAPI → 上 PHY → 资源网格 → OFH”的调用时序，与本笔记第 4 节配合阅读

## 8. 深化阅读路线

建议按此顺序打断点/插日志：

1. `upper_phy_impl.cpp`：看构造函数里各 handler/pool 如何组装
2. `upper_phy_rx_symbol_handler_impl.cpp`：下行 finish / 上行符号推进的实际代码
3. `downlink_processor_pool_impl.cpp`：`get_processor_controller → configure_resource_grid` 的池分配逻辑
4. `pdsch_processor_impl.cpp`：单条 PDSCH PDU 的完整 TX（配 `tests/unittests/phy/upper/channel_processors/` 测试）
5. `uplink_processor_impl.cpp` + `uplink_slot_processor`：看半/满时隙边界怎么触发 PUSCH/PUCCH 处理
6. `lower/processors/uplink/uplink_processor_impl.cpp`：`process_symbol_boundary/process_collecting` 基带采样到网格的细节
7. `fapi_adaptor/phy` 的 sector adapter：一条 FAPI 消息如何变成 `process_pdsch/process_pusch_request`

## 疑问清单

- [ ] 多执行器下行：时隙间与码块间的并行度由谁决定？时隙顺序如何保证？
- [ ] 半时隙边界（第 7 符号）与完整时隙（第 14 符号）分别对哪些 PUSCH/PUCCH 配置生效？
- [ ] PRACH window 的时间基准如何从 lower PHY 对齐到上 PHY？
- [ ] Split-7.2x 下哪些功能留在 DU 的 lower PHY、哪些下沉到 RU？

## 关联

- [[领域-L1物理层]]
- [[MOC-O-RAN开源]]
- [[MOC-C++与软件]]
- [[仓库-srsRAN_Project]]
- [[仓库-srsRAN_Project-下行物理信道与OFDM发射]]
- [[仓库-srsRAN_Project-上行接收与信道估计]]
- [[仓库-srsRAN_Project-信道编码与速率匹配]]
