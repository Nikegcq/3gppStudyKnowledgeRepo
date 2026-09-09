---
type: resource
tags: [L1, 物理层, 3GPP, 学习计划, SSB, PSS, 同步, 实现参考, MATLAB, OAI, srsRAN, DSP]
layer: L1
created: 2026-09-09
updated: 2026-09-09
status: active
source: MATLAB 5G Toolbox / Wireless HDL Toolbox、OAI（openairinterface5g）、srsRAN_4G、ShareTechnote
source_url: https://www.mathworks.com/help/5g/ug/nr-cell-search-and-mib-and-sib1-recovery.html
---

# 实现参考：PSS 检测与同步的代码与示例（MATLAB / OAI / srsRAN / Python）

## 一句话

规范的 PSS 只定义“3 条 127 长的 m 序列 + 映射位置”（3GPP TS 38.211 §7.4.2.2），怎么“找到它并同步”全部在接收机侧。要读实现，推荐四条主线：**MATLAB 5G Toolbox 官方示例（算法最清楚）→ srsRAN_4G 的 NR SSB 搜索栈（代码最干净）→ OAI 的 NR UE 初始同步（最接近产品级）→ ShareTechnote 的 Python/py3gpp 脚本（可边看边跑）**。若目标是 FPGA 工程，再补 MATLAB Wireless HDL Toolbox 的硬件友好版参考。

## 来源总览

| 来源 | 形态 | 覆盖范围 | 适合 |
| --- | --- | --- | --- |
| MATLAB 5G Toolbox 官方示例 | MATLAB（可运行） | PSS→SSS→PBCH DM-RS→PBCH/BCH→MIB→SIB1 全链路 | 先把算法看懂、跑通 |
| MATLAB Wireless HDL Downlink Receiver Reference | MATLAB 参考 + Simulink/HDL | 硬件友好的 cell search（PSS 搜索/DDC/细频偏/SSS） | FPGA 定点流式实现 |
| OAI `openairinterface5g` | C（完整 NR UE 接收机） | GSCN 并行扫描→PSS→频偏补偿→FFT→SSS→PBCH→RSRP/AGC | 真实工程、协议与实现细节最全 |
| srsRAN_4G（srsue NR 栈） | C/C++ | FFT 相关做 PSS 定时与粗频偏 + 频域 SSS 检测 + PBCH 校验 | 代码干净，适合精读；另有 LTE 版对照 |
| ShareTechnote DSP 页 | Python（py3gpp） | PSS 时域相关定位 + 整条 PBCH 解码脚本 | 无 MATLAB 环境时的自测/教学 |

## 1. MATLAB：5G Toolbox 官方示例（首选）

### 1.1 NR Cell Search and MIB and SIB1 Recovery

- 本地打开：`openExample('5g/NRCellSearchMIBAndSIB1RecoveryExample')`
- 文档页：<https://www.mathworks.com/help/5g/ug/nr-cell-search-and-mib-and-sib1-recovery.html>
- 配套讲解（知乎）：<https://zhuanlan.zhihu.com/p/347035177>
- 需要 5G Toolbox（支持读本地抓包波形或自己用 `nrWaveformGenerator` 生成含 SSB + SIB1 的波形加 AWGN）。

接收机各步和关键 helper 的对应关系：

1. **PSS 搜索 + 频偏校正**（`hSSBurstFrequencyCorrect`）：
   - 把波形按**半个子载波间隔为步进**的候选频偏做频移，再与 3 条 PSS 序列相关（`searchBW = 6*scsSSB` 控制搜索带宽）；
   - 最强相关峰同时给出 **N_ID^(2)**、粗频偏（PSS 频域居中，峰值位置相对载波中心的偏移即粗频偏）、以及“信道条件最好”的时刻；
   - **半 SCS 以内的小数倍频偏**用 SSB 内各 OFDM 符号的 CP 与其本体相关，相位正比于频偏。
2. **时间同步 + OFDM 解调**：用已检测 N_ID^(2) 构造参考 grid，`nrTimingEstimate` 找定时偏移；注意参考 PSS 放在**第 2 个 OFDM 符号**，避开符号 0 的特殊 CP；解调后取符号 2..5 即 SSB。
3. **SSS 检测**：从网格提取 SSS 的 127 个 RE，与 336 条本地序列相关（代码即 `sum(abs(mean(sssRx .* conj(sssRef),1)).^2)`），最强峰给 N_ID^(1)，合成 PCI。
4. **PBCH DM-RS 盲检**：对 8 个候选 `ibar_SSB` 分别做信道估计并测 SNR，最优者给出 SSB index 低位（L_max=4 时 `v = mod(ibar_SSB,4)`，否则 `v = ibar_SSB`）。
5. **PBCH/BCH 解码**：用 SSS + DM-RS 做整块信道估计与 MMSE 均衡，解扰后 Polar 解码，得到 SFN 低 4 bit、半帧 bit、SSB index/k_SSB；MIB 给出 CORESET#0 配置，继续解 SIB1。

规范对照：TS 38.211 §7.4.2.2/§7.4.2.3（PSS/SSS 序列）、§7.4.1.4.1（PBCH DM-RS）、§7.3.3.1（PBCH 加扰）；TS 38.213 §4.1（SSB burst 位置）；TS 38.101-1 Table 5.3.5-1（最小信道带宽，用于定 CORESET#0）。

### 1.2 FPGA 路线：NR HDL Downlink Receiver MATLAB Reference

- 文档页：<https://www.mathworks.com/help/wireless-hdl/ug/nr-hdl-cell-search-and-mib-recovery-ml-ref.html>
- 用途：把上面的算法改成**硬件友好版**的 MATLAB 参考（`nrhdlexamples.cellSearch` / `ssbDetect` / `ssbDetectSearchDemod` / `ssbDecode`），与 Simulink 流式定点模型一一对应（NR HDL Cell Search / MIB Recovery / SIB1 Recovery，含 FR2 变体；另有 AD9361 SoC 的“PL 做 SSB Detector + PS 做 Search Controller”示例）。
- 值得记的结构差异：
  - 前端 DDC 把 61.44 Msps 降采样到 7.68 Msps（30 kHz SCS 直接用；15 kHz 再降一半到 3.84 Msps）；
  - SSB Detector 的 **search 模式**返回 `NCellID2 / timingOffset / pssCorrelation / pssEnergy / frequencyOffset`，细频偏用 SSB 4 个符号的 CP 量；**demod 模式**按已知定时做 256 点 FFT（SSB 240 个子载波）并检测 SSS；
  - Search Controller 以低速率跑在软件侧，负责“粗频偏按半 SCS 步进扫描 + 选细频偏最小的候选”；
  - 定时参考以 20 ms（1228800 样本 @61.44 MHz）回绕——SSB 周期 ≤20 ms 是搜索可以依赖的假设。

## 2. OAI：openairinterface5g 的 NR UE 初始同步

仓库：<https://github.com/openairinterface/openairinterface5g>（分支 `develop`）。这是**完整可编译的 NR UE 接收机**，初始同步链路从“不知道小区”一直做到 PBCH 解出 SSB index、RSRP/AGC 调整。

| 文件 | 关键函数 | 看什么 |
| --- | --- | --- |
| `openair1/PHY/NR_UE_TRANSPORT/nr_initial_sync.c` | `nr_initial_sync` / `nr_scan_ssb` / `nr_search_ssb_common` / `compensate_freq_offset` / `do_time_to_freq` / `nr_pbch_detection` | 流程编排：每个 GSCN 一个线程扫描；先生成 3 条 PSS 时域模板 → PSS 搜索 → 频偏补偿 → 4 个符号 FFT → SSS → PBCH DM-RS 相关 + Polar 解码 → RSRP/AGC。注释里画了 SSB 在帧缓冲里的位置（`pss|pbch|sss|pbch`） |
| `openair1/PHY/NR_UE_TRANSPORT/pss_nr.c` | `generate_pss_nr` / `generate_pss_nr_time` / `pss_search_time_nr` | 序列生成（38.211 §7.4.2.2，x 初值 {0,1,1,0,1,1,1}）；IDFT 出时域模板；**时域滑窗点积**：步进 4 个样本保证 SIMD 对齐，峰值要求 > 5×平均（非指定小区场景）且位置 ≥ 一个 CP；3 路结果按峰排序 |
| `openair1/PHY/NR_UE_TRANSPORT/sss_nr.c` | `rx_sss_nr` / `init_context_sss_nr` / `pss_ch_est_nr` | 用 PSS 的 RE 逐点做信道估计（H* = R*·PSS）并补偿到 SSS 上；对 336 个 N_ID^(1) × 15 个相位假设做相关，门限 `SSS_METRIC_FLOOR_NR=30000`；从最强假设的相位再提一次残余 CFO |
| `openair1/PHY/NR_REFSIG/pss_nr.h` / `sss_nr.h` | 接口与常量 | `PSS_SSS_SUB_CARRIER_START`、序列长度、`pss_search_t` / `nr_sss_params_t` 结构 |

实现细节里值得注意的工程点：

- 频偏：`pss_search_time_nr` 只估**小数倍**——在相关峰处把 PSS 模板和接收信号各劈成前后两半，`ffo = atan2(Im(r1^*·r2), Re(r1^*·r2))/π`，再乘 SCS 得到 Hz（注释引用 Huang et al., “Joint time and frequency offset estimation in LTE downlink”, CHINACOM 2012）；SSS 之后再修正一次。
- FFT 取窗：`do_time_to_freq` 从估计起点加 CP 后，再往前回退 **CP 的 1/8**（`nb_prefix_samples/ofdm_offset_divisor`），避免 ISI。
- 符号顺序注释写明：0=PSS、1=PBCH、2=SSS、3=PBCH。
- 最少缓冲 2 个 10 ms 帧（代码注释对应 TS 38.213 §4.1 cell search 的周期假设）。
- `nr_search_ssb_common` 被初始同步和邻区测量共用（`openair1/PHY/NR_UE_ESTIMATION/nr_ue_measurements.c`），邻区场景可传排除 PCI 列表。
- 同目录还有 sidelink 版 `nr_initial_sync_sl.c`，可对照看相同框架如何复用。

想跑起来需要整套 OAI 构建（`nr-uesoftmodem`），成本较高；更轻量的做法是直接网页/克隆后按上面三个函数走读。

## 3. srsRAN_4G：NR UE（srsue）SSB 搜索栈 + LTE 对照

先说清楚仓库边界：**srsRAN_Project（5G gNB 主干）没有 NR UE 接收侧同步**，库内 [[仓库-srsRAN_Project-下行物理信道与OFDM发射]] 记录的是发射侧 `pss_processor`/`ssb_processor`；**NR UE 的 cell search 代码保留在 srsRAN_4G**（master 分支，srsue 内仍有 NR 支持）。另外老仓库 srsLTE 的 LTE 同步实现是这一套代码的前身，最成熟。

仓库：<https://github.com/srsRAN/srsRAN_4G>

| 文件 | 关键函数 | 看什么 |
| --- | --- | --- |
| `lib/src/phy/sync/ssb.c` | `ssb_pss_search` / `srsran_ssb_search` | **FFT 相关**：滑窗取一段样本→FFT→与预生成的 PSS 频域模板共轭相乘，并用**循环移位**扫整数倍频偏（先半 SCS 粗扫、命中后再整格细扫）→IFFT→找峰；一个函数同时返回 N_ID^(2)、定时延迟、粗 CFO |
| `lib/src/phy/sync/pss_nr.c` | `srsran_pss_nr_find` / `_extract_lse` / `_put` | 序列生成（`constructor` 里预生成）+ 频域 3 路相关；`extract_lse` 给信道估计用 |
| `lib/src/phy/sync/sss_nr.c` | `srsran_sss_nr_find` | 频域检测：对 112 个 m1 先解 d1 序列，再对每个 m1 的 3 个 m0 候选相关（m0/m1 按 38.211 §7.4.2.3），归一化到平均功率 |
| `srsue/src/phy/nr/cell_search.cc` | `init/start/run_slot` | 每 slot 调 `srsran_ssb_search`，判定条件：SNR ≥ −10 dB 且 PBCH CRC 通过；配套测试 `nr_cell_search_test.cc` / `nr_sa_cell_search_test.cc` / `nr_cell_search_rf.cc`（最后一个可接 RF/USRP） |

细频偏精修在 `ssb.c` 里：PSS/SSS 各自去调制后整体求和，用二者相位差 `cargf(corr_sss * conj(corr_pss))` 换算 Hz。

LTE 对照（算法思想同 NR，注释更全、验证工具更多）：`lib/src/phy/sync/pss.c` / `sss.c` / `cp.c` / `sync.c`、`lib/src/phy/ue/ue_cell_search.c`、可独立运行的 `lib/examples/cell_search.c`（文件或 USRP 输入）。

## 4. ShareTechnote DSP 页：Python（py3gpp）可跑版本

- 页面：<https://www.sharetechnote.com/html/5G/5G_PHY_DSP_SSB.html>（配合 [[ShareTechnote-5G手册]]）
- 内容：读 SigMF 格式的真实下行 IQ 抓包，走完整 PBCH 解码 pipeline：
  1. 用 `nrPSS(NID2)` 生成 3 条时域参考波形（OFDM 调制后去掉 CP），`scipy.signal.correlate` 对 25 ms 波形做相关，峰值给 **N_ID^(2) + SSB 时间**；
  2. 以检测到的 NID2 构造参考 grid 细化定时，OFDM 解调出 SSB 网格；
  3. 提取 PSS/SSS/DM-RS/PBCH，画星座图并继续解 PBCH。
- 说明：`py3gpp` 是 MATLAB 5G Toolbox 风格函数的 Python 移植，脚本里 `nrPSS`/`nrSSS`/`nrOFDMModulate` 的用法和 MATLAB 几乎一致，适合没有 MATLAB 授权时先跑通概念。

## 5. 实现差异速览（同一条规范，三种做法）

| 实现 | 定时 + N_ID^(2) 怎么找 | 粗/整数倍频偏 | 细/小数倍频偏 |
| --- | --- | --- | --- |
| MATLAB 示例 | 波形按 1/2 SCS 步进频移后与 3 条 PSS 相关，取最强峰 | 由峰所在频移格直接给（PSS 居中） | SSB 符号 CP 相关 |
| OAI | 时域滑窗点积（4 样本步进、SIMD），峰值 ≥ 5×均值 | 该文件内未做整数格搜索 | PSS 半符号分段相位差 + SSS 再修正 |
| srsRAN_4G | FFT 循环相关（滑窗 + 循环移位） | 循环移位格数即粗 CFO（先半 SCS 后整格） | PSS/SSS 相位差精修 |
| ShareTechnote Python | scipy 直接时域相关 | 脚本用 `delta_f` 变量手动频移 | 脚本可选 `apply_fine_CFO` |

## 6. 建议阅读顺序

1. 先跑/读 **MATLAB 官方示例**：它把“PSS 相关峰 → 频偏 → 定时 → SSS → DM-RS → PBCH”切成清晰小节，和 [[PSS检测与同步-定时频偏估计]] 的推导一一对应。
2. 精读 **srsRAN_4G** 的 `pss_nr.c` + `sss_nr.c` + `ssb.c`：函数少、命名清楚，能同时看到“频域模板 + 循环移位扫整数频偏”的实现思路。
3. 再啃 **OAI**：`nr_initial_sync.c` 看编排，`pss_nr.c`/`sss_nr.c` 看产品级细节（SIMD 对齐、门限、CP 1/8 取窗、多帧缓冲、邻区复用）。
4. FPGA 目标：对照 MATLAB **Wireless HDL 参考**的 `ssbDetectSearchDemod` 与 Simulink 定点模型，把浮点算法换成流式定点。
5. 需要自测/演示时用 ShareTechnote 的 **Python 脚本**改参数跑。

## 相关笔记

- 算法原理：[[PSS检测与同步-定时频偏估计]]（相关峰定时、CP 相位差、整数/小数倍频偏）
- 流程全景：[[小区搜索流程分步详解]]
- 学习计划主线：[[学习-阶段2-SSB与小区搜索]]
- 规范入口：[[3GPP-38系列-NR物理层规范]]
- 发射侧对照（srsRAN_Project）：[[仓库-srsRAN_Project-下行物理信道与OFDM发射]]
