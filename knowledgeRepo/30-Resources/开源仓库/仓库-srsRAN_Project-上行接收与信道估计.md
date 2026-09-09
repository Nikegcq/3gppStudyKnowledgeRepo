---
type: resource
tags: [开源, srsRAN, PHY, 上行, 信道估计]
repo: srsRAN_Project
repo_url: https://github.com/srsran/srsRAN_Project
local_path: /home/nick/work/repo/srsRAN_Project
created: 2026-09-03
updated: 2026-09-03
status: active
---

# srsRAN_Project 上行接收与信道估计（实现 ↔ 3GPP）

> 所属：[[仓库-srsRAN_Project-PHY总览]]；协议入口：[[领域-L1物理层]]

## 上行接收总链（以 PUSCH 为例）

```
RU/radio 基带采样
 └→ OFDM 解调（去 CP + FFT）                    [ofdm_demodulator_impl]
 └→ 资源网格（上行 resource_grid）
 └→ DM-RS 信道估计                              [dmrs_pusch_estimator_impl + port_channel_estimator_average_impl]
 └→ 均衡（ZF）                                  [channel_equalizer_generic_impl（equalize_zf_1xn / 2xn）]
 └→ 解调 → 软比特 LLR                          [pusch_demodulator_impl → demodulation_mapper]
 └→ UCI/数据分离                                [ulsch_demultiplex_impl]
    ├→ UL-SCH：解速率匹配 → LDPC 译码 → CRC → MAC TB   [pusch_decoder_impl + ldpc_decoder + rx_buffer 软合并]
    └→ UCI：HARQ-ACK / SR / CSI → uci_decoder_impl → 调度器
```

## PUSCH 接收实现

目录：`lib/phy/upper/channel_processors/pusch/`

| 阶段 | 代码 | 3GPP 说明 |
| --- | --- | --- |
| 处理器入口 | `pusch_processor_impl`（接口 `pusch_processor.h`；结果含 data + control 两部分：`pusch_processor_result_data/control`） | 一个时隙可同时解数据与 UCI |
| DM-RS 估计 | `dmrs_pusch_estimator_impl` + `port_channel_estimator_average_impl`（`signal_processors/channel_estimator/`） | 上行 DM-RS 序列/映射见 TS 38.211 上行参考信号章节；估计出每端口信道 H |
| 均衡 | `channel_equalizer_generic_impl`（`upper/equalization/`，ZF，`equalize_zf_1xn/2xn`） | 把多接收天线信号合并/分离出各层；NR 里均衡需要知道 DM-RS 端口与层映射 |
| 解调 | `pusch_demodulator_impl`（软比特） | 调制阶数来自 MCS；输出 LLR（`log_likelihood_ratio`） |
| UCI/数据分离 | `ulsch_demultiplex_impl` | PUSCH 上 UCI 的 RE 位置/交织见 TS 38.212 UCI 复用章节 |
| 数据译码 | `pusch_decoder_impl`（另有 `pusch_decoder_hw_impl`、`pusch_decoder_empty_impl`）；内部走 LDPC 解速率匹配 + 译码（见 [[仓库-srsRAN_Project-信道编码与速率匹配]]） | 需要 RV、软缓冲（`rx_buffer_pool`）做 HARQ 合并 |
| UCI 译码 | `uci_decoder_impl`（Polar/短块） | HARQ-ACK/SR 的码本与时序由调度器按 TS 38.213 管理 |

## PUCCH 接收实现

目录：`lib/phy/upper/channel_processors/pucch/`

- Format 0：`pucch_detector_format0.cpp`——序列检测（SR/HARQ 1~2 bit）；代码注释把序列选择表指向 TS 38.213 §9.2.4（HARQ-ACK 反馈序列）
- Format 1：`pucch_detector_format1.cpp`——正交序列 + 循环移位检测（`pucch_orthogonal_sequence_format1`）
- Format 2：`pucch_demodulator_format2.cpp` + `dmrs_pucch_estimator_format2.cpp`——QPSK 调制、少量 UCI
- Format 3/4：`pucch_demodulator_format3/4` + `dmrs_pucch_estimator_formats3_4`；Format 4 支持 UE 复用（`pucch_orthogonal_sequence_format4`），调制可为 QPSK/π/2-BPSK（代码注释：TS 38.211 §6.3.2.6.2）
- 汇总：`pucch_processor_impl`，结果结构 `pucch_processor_result` / `pucch_uci_message`

3GPP 知识要点：PUCCH Format 0/1 承载 ≤2 bit（SR、HARQ），Format 2 承载 >2 bit 且 ≤11 bit，Format 3/4 承载更长的 UCI；物理结构（占多少 PRB/符号、是否跳频）由 TS 38.211 §6.3.2 与 38.213 参数共同决定。

## PRACH

- TX 侧（随机接入前导生成）：`prach_generator_impl`（接口 `prach_generator.h`）——ZC 序列 + 循环移位，按 preamble 格式生成
- RX 侧：`prach_detector_generic_impl`（相关检测、阈值表 `prach_detector_generic_thresholds.cpp`）；下 PHY 侧解调 `ofdm_prach_demodulator_impl`（`lower/modulation/`）
- 缓冲：`support/prach_buffer`（上下 PHY 共享，`shared_prach_buffer.h`）

3GPP 知识要点：PRACH preamble 的序列与格式见 TS 38.211 PRACH 章节；随机接入过程（preamble→RAR→Msg3→竞争解决）见 TS 38.213/38.321。

## SRS（探测参考信号）

- `srs_estimator_generic_impl`（`signal_processors/srs/`）：估计上行信道，输出定时/质量/信道信息（`srs_estimator_result.h`）
- 序列用低 PAPR 序列集合：`sequence_generators/low_papr_sequence_*`（对应 TS 38.211 低 PAPR/计算机生成序列章节）

用途：上行信道探测、下行预编码辅助（非码本）、定时提前估计等。

## 接收侧公共支撑

- 资源网格与缓冲：`resource_grid_pool`、`re_buffer`/`re_measurement`（模块化缓冲类型）
- 时间对齐：`support/time_alignment_estimator/`、`support/interpolator/`
- 下 PHY 控制：CFO/时偏/中心频点控制器（`lower_phy_cfo_controller` 等头文件）
- 结果接口：`upper_phy_rx_results_notifier`（PHY→MAC/调度器）
- 本机定制：`upper_phy_rx_dci_extractor_decorator.*`（未提交，RX DCI 提取装饰器，需自行确认是否启用）

## 3GPP 知识对照提示

- 接收机算法（估计/均衡/检测）本身不在 3GPP 标准范围内，标准约束的是“发什么、怎么映射、参数怎么取”：DM-RS 位置与序列、PUSCH 的 DM-RS 端口数/层数、UCI 复用规则、HARQ 时序与码本等
- 对照时建议从 PDU 配置结构反查规范：`pusch_processor.h` 里的 dmrs/config 字段 → TS 38.211 相应章节

## 代码走读建议

1. 先跑通 `tests/unittests/phy/upper/channel_processors/pusch/` 与 `pucch/` 的 vector 测试
2. 在 `pusch_processor_impl.cpp` 打断点看“估计→均衡→解调→译码”各阶段缓冲
3. 对比 DL/UL 的对称性：PUSCH 数据用与 PDSCH 相同的 LDPC 链；区别在 DM-RS、变换预编码（DFT-s-OFDM）与 UCI 复用

## 关联

- [[仓库-srsRAN_Project-信道编码与速率匹配]]
- [[仓库-srsRAN_Project-PHY总览]]
- [[领域-L1物理层]]
- [[MOC-FPGA]]（上行检测/均衡若下沉硬件）

