---
type: resource
tags: [开源, srsRAN, PHY, 下行, OFDM]
repo: srsRAN_Project
repo_url: https://github.com/srsran/srsRAN_Project
local_path: /home/nick/work/repo/srsRAN_Project
created: 2026-09-03
updated: 2026-09-03
status: active
---

# srsRAN_Project 下行物理信道与 OFDM 发射（实现 ↔ 3GPP）

> 所属：[[仓库-srsRAN_Project-PHY总览]]；协议入口：[[领域-L1物理层]]

## 下行发射总链（以 PDSCH 为例）

```
MAC TB
 └→ 信道编码：CRC + LDPC + 速率匹配（TS 38.212）        [pdsch_encoder_impl]
 └→ 加扰（TS 38.211 §7.3.1.1，代码注释标注）            [pdsch_modulator_impl::scramble]
 └→ 调制（TS 38.211 §7.3.1.2）QPSK~256QAM              [modulation_mapper_*]
 └→ 层映射（CW→Layer，最多 2 CW，见 pdsch_processor::MAX_NOF_TRANSPORT_BLOCKS）
 └→ 预编码/天线端口映射（Layer→Port，W 矩阵）           [channel_precoder_*]
 └→ RE 映射到资源网格                                   [resource_grid_mapper]
 └→ OFDM 调制（IFFT + 加 CP）                           [ofdm_modulator_impl]
 └→ 基带采样 → radio / RU
```

概念辨析（码字/层/端口、调制符号/OFDM 符号/RE）可先读仓库内 `docs/pdsch_codeword_layer_port_explanation.md`，本笔记聚焦代码位置。

## PDSCH 实现与条文对照

目录：`lib/phy/upper/channel_processors/pdsch/`

| 处理阶段 | 3GPP 锚点（代码注释） | 代码 |
| --- | --- | --- |
| TB 编码（LDPC+速率匹配） | TS 38.212 §7.2 / §5.4.2 | `pdsch_encoder_impl.cpp`（另有 `pdsch_encoder_hw_impl` 硬件后端） |
| 加扰 | TS 38.211 §7.3.1.1 | `pdsch_modulator_impl.h` 的 `scramble()`，用 `pseudo_random_generator` |
| 调制 | TS 38.211 §7.3.1.2 | `modulate()` → `modulation_mapper`（LUT / AVX512 / NEON 后端） |
| 层映射/预编码/RE 映射 | TS 38.211 §7.3.1 相关小节 | `map()`：`resource_grid_mapper::map` + `precoding_configuration`，单层时跳过层映射直接写栅格 |
| DM-RS | TS 38.211 §7.4.1.1（代码注释） | `dmrs_pdsch_processor_impl.cpp`（序列 + 映射，helper 在 `signal_processors/dmrs_helper.*`） |
| PT-RS | TS 38.211 §7.4.1.2（代码注释）；幅度 ρ 见 TS 38.214 §4.1 | `ptrs_pdsch_generator_impl.cpp`（频/时域密度、RE 偏移、`ratio_ptrs_to_pdsch_data_dB`） |

处理器骨架：

- 接口：`include/srsran/phy/upper/channel_processors/pdsch/pdsch_processor.h`（含 `MAX_NOF_TRANSPORT_BLOCKS = 2`、codeword_description、ptrs_configuration 等）
- 通用实现：`pdsch_processor_impl.cpp`；流水线实现：`pdsch_processor_flexible_impl.cpp`（用 `pdsch_block_processor_impl` 按码块流水）
- 校验器：`pdsch_processor_validator_impl`；池：`pdsch_processor_pool`；日志装饰器：`logging_pdsch_processor_decorator.h`

## PDCCH 实现与条文对照

目录：`lib/phy/upper/channel_processors/pdcch/`

- 编码：`pdcch_encoder_impl`（Polar，代码注释 TS 38.212 §7.3）——DCI 比特经 CRC（RNTI 掩码）→ Polar → 速率匹配
- 调制：`pdcch_modulator_impl`：
  - 加扰：TS 38.211 §7.3.2.3（代码注释）
  - 调制：§7.3.2.4（QPSK）
  - RE 映射：§7.3.2.5
  - CRB 掩码计算：TS 38.211 §7.3.2.2（代码注释，`compute_crb_mask` 相关）
- 整体：`pdcch_processor_impl`；DM-RS：`signal_processors/pdcch/dmrs_pdcch_processor_impl`

3GPP 知识要点：PDCCH 的传输单元是 CCE（由 REG 组成），聚合等级 AL=1/2/4/8/16；CORESET 决定频域与首符号；搜索空间决定监听时机。srsRAN 的 PDU 校验器与实现里都能看到 REG/CCE/聚合等级参数。

## SSB / PBCH 实现与条文对照

目录：`lib/phy/upper/channel_processors/ssb/`

- `ssb_processor_impl`：组装整个 SSB（PSS + SSS + PBCH）
- `pbch_encoder_impl`：BCH 信息 → CRC → Polar → 速率匹配（TS 38.212 BCH 章节）
- `pbch_modulator_impl`：加扰 §7.3.3.1、调制 §7.3.3.2、物理资源映射 §7.3.3.3（均为代码注释标注）
- `pss_processor_impl` / `sss_processor_impl` + `pss_sequence_generator` / `sss_sequence_generator`
- DM-RS for PBCH：`dmrs_pbch_processor_impl`

3GPP 知识要点：SSB 由 PSS/SSS/PBCH 组成，是小区搜索第一步；其时频位置（半帧内 L_max 个候选、SCS 相关 pattern）决定 UE 同步与 MIB 解调。

## 通用发射功能（generic_functions）

- 预编码：`lib/phy/generic_functions/precoding/channel_precoder_*`（generic/AVX2/AVX512/NEON），接口 `include/srsran/phy/generic_functions/precoding/channel_precoder.h`
- 资源网格与映射：`include/srsran/phy/support/resource_grid_mapper.h`、`re_pattern.h`、`rb_allocation.h`、`precoding_configuration.h`
- OFDM：`lib/phy/lower/modulation/ofdm_modulator_impl.*`；DFT 后端 `lib/phy/generic_functions/dft_processor_*`（FFTW/generic/AVX2）
- 序列：`upper/sequence_generators/pseudo_random_generator_impl`（加扰用 Gold 序列，对应 TS 38.211 §5.2.1 伪随机序列生成）

## 硬件加速 / FPGA 视角

- `pdsch_encoder_hw_impl`、`pdsch_block_processor_hw_impl`、`pusch_decoder_hw_impl` 等是硬件后端骨架
- 配套 `lib/hal`（硬件抽象层）做算子派发；FPGA 加速的落地通常从这些 `*_hw_impl` 与 HAL 接口入手
- 参考：[[MOC-FPGA]]

## 代码走读建议

1. 从 `pdsch_processor.h` 读 PDU 配置结构（codeword、precoding、dmrs、ptrs、rb_allocation）
2. 单测：`tests/unittests/phy/upper/channel_processors/pdsch/`（PDSCH TX/RX vector test）
3. 打开 `logging_pdsch_processor_decorator` 观察单次传输的 MCS/层数/PRB/功率参数
4. 对照仓库内 `docs/pdsch_codeword_layer_port_explanation.md` 把概念映射到代码字段

## 关联

- [[仓库-srsRAN_Project-信道编码与速率匹配]]
- [[仓库-srsRAN_Project-PHY总览]]
- [[领域-L1物理层]]

