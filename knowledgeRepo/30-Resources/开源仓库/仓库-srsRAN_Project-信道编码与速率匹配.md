---
type: resource
tags: [开源, srsRAN, PHY, 信道编码]
repo: srsRAN_Project
repo_url: https://github.com/srsran/srsRAN_Project
local_path: /home/nick/work/repo/srsRAN_Project
created: 2026-09-03
updated: 2026-09-03
status: active
---

# srsRAN_Project 信道编码与速率匹配（实现 ↔ 3GPP）

> 所属：[[仓库-srsRAN_Project-PHY总览]]；协议入口：[[领域-L1物理层]]

## 为什么先看这里

信道编码是 L1 里最“标准驱动”的部分：代码结构几乎就是 3GPP 流程的镜像，适合建立“规范条文 ↔ 函数/类”的对照能力。代码全部在 `lib/phy/upper/channel_coding/`（实现）与 `include/srsran/phy/upper/channel_coding/`（接口），按 CRC / LDPC / Polar / short block 四块组织，另有 `lib/phy/upper/` 下的 `rx_buffer_*`（HARQ 软合并）。

## 1. CRC（crc_calculator）

实现文件：`crc_calculator_generic_impl`（通用）、`crc_calculator_lut_impl`（查表）、`crc_calculator_clmul_impl`（x86 CLMUL 指令加速）、`crc_calculator_neon_impl`（ARM NEON）。

- 用途：传输块/码块 CRC（TB-CRC、CB-CRC）、以及 BCH/控制信息里的 CRC
- 3GPP 对照：TS 38.212 的 CRC 计算章节；代码在 `ldpc_segmenter_helpers.h` 中把分段与 CRC 属性标注为 TS 38.212 §5.2.2 相关
- 看点：同一接口多后端（generic/LUT/SIMD），是学习“接口 + 工厂 + 多实现”模式的样板

## 2. LDPC（DL-SCH / UL-SCH 数据信道）

目录：`channel_coding/ldpc/`

TX 侧：
- `ldpc_segmenter_tx_impl`：TB → 码块分段、CRC 附加、确定 Base Graph（BG1/BG2）与 N_cb（环形缓冲长度），属性见 TS 38.212 §5.2.2 / §5.4.2.1（代码注释）
- `ldpc_encoder_impl` + 后端：`ldpc_encoder_generic` / `_avx2` / `_neon`（编码矩阵运算）
- `ldpc_rate_matcher_impl`：比特选择（§5.4.2.1）与比特交织（§5.4.2.2），代码注释明确标注这两个条文
- `pdsch_encoder_impl` 包装 gNB 下行整条编码链（接口头在
  `include/srsran/phy/upper/channel_processors/pdsch/`）。注意：gNB 侧没有
  “PUSCH 编码器”——PUSCH 由 UE 发射，srsRAN gNB 侧对应的是
  `pusch_decoder_impl` 反向链（速率去匹配 + 译码）

RX 侧：
- `ldpc_rate_dematcher_impl`：恢复速率匹配前的 LLR 序列（§5.4.2 的逆过程）
- `ldpc_decoder_impl` + 后端：`ldpc_decoder_generic` / `_avx2` / `_avx512` / `_neon`（置信传播类迭代译码）
- HARQ 软合并：`rx_buffer_pool` / `rx_buffer_impl`（`lib/phy/upper/`）保存每码块 LLR，重传按 RV 合并后再译码

3GPP 知识要点：

- 5G 数据信道用 LDPC，两种 Base Graph：BG1 面向大 TB/低码率，BG2 面向小 TB/高码率；TBS 与码率决定选哪个（TS 38.212）
- 速率匹配用“环形缓冲 + 比特选择”，RV（冗余版本）从环上不同起点取比特，实现增量冗余 HARQ
- 码块级 CRC（CRC24B）用于译码后错误检测，TB 级 CRC（CRC24A）用于最终校验

## 3. Polar（BCH / DCI / 长 UCI）

目录：`channel_coding/polar/`

- `polar_code_impl`：码长/信息位/冻结位构造（可靠度序列）
- `polar_encoder_impl` / `polar_decoder_impl`：编码与译码
- `polar_rate_matcher_impl` / `polar_rate_dematcher_impl`：子块交织 + 比特选择/逆过程（代码注释：TS 38.212 §5.4.1）
- `polar_interleaver_impl`、`polar_allocator_impl`（信息位/冻结位/PC 位放置）、`polar_deallocator_impl`
- 使用方：
  - PBCH：`pbch_encoder_impl`（BCH 编码，`channel_processors/ssb/`）
  - PDCCH DCI：`pdcch_encoder_impl`（代码注释：TS 38.212 §7.3）
  - PUSCH 上的长 UCI：`uci_decoder_impl`（代码注释：最大 Polar 码块尺寸见 TS 38.212 §5.2.1）

3GPP 知识要点：Polar 是 5G 的控制信道编码（PBCH/DCI/UCI≥12bit），核心是“极化 + 可靠度排序”；DCI 还要做 CRC 加扰（RNTI 掩码）、子块交织与速率匹配。

## 4. Short block（≤11 bit 的 UCI）

目录：`channel_coding/short/`

- `short_block_encoder_impl`：短块编码与速率匹配（代码注释：TS 38.212 §5.4.3）
- `short_block_detector_impl`：短块检测（代码注释关联 TS 38.211 短序列相关章节）

用途：HARQ-ACK/SR 等短 UCI（PUCCH Format 0/1 与 PUSCH 上少量 UCI），不需要 Polar 时用短块/重复。

## 代码走读建议

1. 从 `include/srsran/phy/upper/channel_coding/ldpc/` 看 `ldpc_encoder.h`、`ldpc_decoder.h` 的接口
2. 跟 TX：`ldpc_segmenter_tx_impl.cpp → ldpc_encoder_impl.cpp → ldpc_rate_matcher_impl.cpp`
3. 跟 RX：`ldpc_rate_dematcher_impl.cpp → ldpc_decoder_impl.cpp`，再配合 `rx_buffer_pool_test.cpp` 理解软合并
4. 单测目录：`tests/unittests/phy/upper/channel_coding/`

## 关联

- [[仓库-srsRAN_Project-PHY总览]]
- [[仓库-srsRAN_Project-下行物理信道与OFDM发射]]
- [[仓库-srsRAN_Project-上行接收与信道估计]]
- [[MOC-C++与软件]]（SIMD 多后端实现）
