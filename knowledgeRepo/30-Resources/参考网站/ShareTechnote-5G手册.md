---
type: resource
tags: [L1, 物理层, 参考网站, 学习计划, 5G, 手册]
layer: L1
created: 2026-09-08
updated: 2026-09-08
status: active
source: ShareTechnote
source_url: https://www.sharetechnote.com/html/5G/Handbook_5G_Index.html
---

# ShareTechnote 5G 手册（NR 学习参考网站）

## 一句话总结

ShareTechnote 的 5G/NR 手册是「图解 + 分步举例」风格的个人技术资料站，按主题字母索引覆盖数百个 5G 主题；物理层部分几乎对应 L1 学习计划的每个阶段，适合先建立直觉，再回 3GPP 原文核对数字与条文。

## 站点入口与特点

- 总索引：https://www.sharetechnote.com/html/5G/Handbook_5G_Index.html （QuickReference - 5G/NR，字母序，页面多建议用 Ctrl+F 定位）
- 页面地址规律：`https://www.sharetechnote.com/html/5G/<主题>.html`
- 特点：每页以示意图、表格、逐步例子为主，适合「先看图再读规范」；部分页面配 Matlab 5G Toolbox 演示（位于 `html/lte_toolbox/`），可做信号级可视化。
- 定位：个人讲解网站，非 3GPP 官方；内容以 R15–R17 为主，少量 R18/R19 特性。

## 怎么和 3GPP 规范配合用（推荐节奏）

1. 先开 ShareTechnote 页面建立直觉：概念关系图、参数表、一步一步的示例；
2. 再回 [[3GPP-38系列-NR物理层规范]] 对应章节核对「权威数字/公式/条件」；
3. 最后对照 [[仓库-srsRAN_Project-PHY总览]] 等代码笔记看落地实现；
4. 发现不一致时以本地 R19 PDF 原文为准，并把差异记到对应学习笔记的「待深入 / 疑问」。

## 与 L1 七阶段计划的对照

| 学习阶段 | 推荐的 ShareTechnote 页面 |
| --- | --- |
| 1 帧结构 / 参数集 / 资源网格（38.211 §4） | [Numerology](https://www.sharetechnote.com/html/5G/5G_Phy_Numerology.html)、[Frame Structure](https://www.sharetechnote.com/html/5G/5G_FrameStructure.html)、[Resource Grid](https://www.sharetechnote.com/html/5G/5G_ResourceGrid.html)、[Point A / RB 索引](https://www.sharetechnote.com/html/5G/5G_ResourceBlockIndexing.html)、[BWP](https://www.sharetechnote.com/html/5G/5G_CarrrierBandwidthPart.html)、[Timing Units](https://www.sharetechnote.com/html/5G/5G_Phy_TimingUnit.html)、[FR / Operating Band](https://www.sharetechnote.com/html/5G/5G_FR_Bandwidth.html) |
| 2 SSB / 小区搜索（38.211 §7.4.3、38.213 §4/§13、38.212 §7.1） | [Synchronization](https://www.sharetechnote.com/html/5G/5G_Phy_Synchronization.html)、[PSS](https://www.sharetechnote.com/html/5G/5G_PSS.html)、[SSS](https://www.sharetechnote.com/html/5G/5G_SSS.html)、[SS Block, SS/PBCH](https://www.sharetechnote.com/html/5G/5G_SS_Block.html)、[PBCH](https://www.sharetechnote.com/html/5G/5G_PBCH.html)、[PBCH Decoding](https://www.sharetechnote.com/html/5G/5G_PBCH_Decoding.html)、[Cell Search / SIB1 Decoding](https://www.sharetechnote.com/html/5G/5G_CellSearch.html)、[MIB / SIB](https://www.sharetechnote.com/html/5G/5G_Mib_Sib.html)、[Type0 PDCCH CSS](https://www.sharetechnote.com/html/5G/5G_CommonSearchSpace_Type0_PDCCH.html)、[Matlab SSB 演示](https://www.sharetechnote.com/html/lte_toolbox/Matlab_LteToolbox_5G_SS_PBCH.html) |
| 3 PDCCH / DCI（38.211 §7.3.2、38.213 §10、38.212 §7.3） | [PDCCH](https://www.sharetechnote.com/html/5G/5G_PDCCH.html)、[PDCCH Common](https://www.sharetechnote.com/html/5G/5G_PDCCH_Common.html)、[DCI](https://www.sharetechnote.com/html/5G/5G_DCI.html)、[RE/REG/CCE/CORESET 资源单位](https://www.sharetechnote.com/html/5G/5G_ResourceAllocationUnit.html)、[Search Space](https://www.sharetechnote.com/html/5G/5G_SearchSpace.html) |
| 4 信道编码（38.212 §5/§6/§7） | [Channel Coding](https://www.sharetechnote.com/html/5G/5G_ChannelCoding.html)、[Polar Coding](https://www.sharetechnote.com/html/5G/5G_PolarCoding.html)、[LDPC](https://www.sharetechnote.com/html/5G/5G_LDPC.html)、[CBG](https://www.sharetechnote.com/html/5G/5G_CBG.html) |
| 5 PDSCH / PUSCH 调度传输（38.214 §5.1/§6.1） | [PDSCH](https://www.sharetechnote.com/html/5G/5G_PDSCH.html)、[PUSCH](https://www.sharetechnote.com/html/5G/5G_PUSCH.html)、[Mapping Type A/B](https://www.sharetechnote.com/html/5G/5G_PDSCH_PUSCH_MappingType.html)、[MCS/TBS/Code Rate](https://www.sharetechnote.com/html/5G/5G_MCS_TBS_CodeRate.html)、[资源分配时域 K0/K1/K2](https://www.sharetechnote.com/html/5G/5G_ResourceAllocation.html)、[RA Type 0/1](https://www.sharetechnote.com/html/5G/5G_ResourceAllocationType.html)、[PDSCH DMRS](https://www.sharetechnote.com/html/5G/5G_PDSCH_DMRS.html)、[PUSCH DMRS](https://www.sharetechnote.com/html/5G/5G_PUSCH_DMRS.html)、[PTRS](https://www.sharetechnote.com/html/5G/5G_PTRS_DL.html) |
| 6 CSI-RS / SRS / 波束管理（38.211 §7.4.1.5/§6.4.1、38.214 §5.2） | [Reference Signals](https://www.sharetechnote.com/html/5G/5G_Phy_ReferenceSignal.html)、[CSI RS](https://www.sharetechnote.com/html/5G/5G_CSI_RS.html)、[CSI Framework](https://www.sharetechnote.com/html/5G/5G_CSI_Framework.html)、[CSI Report](https://www.sharetechnote.com/html/5G/5G_CSI_Report.html)、[CSI Codebook](https://www.sharetechnote.com/html/5G/5G_CSI_RS_Codebook.html)、[SRS](https://www.sharetechnote.com/html/5G/5G_SRS.html)、[Beam Management](https://www.sharetechnote.com/html/5G/5G_Phy_BeamManagement.html)、[QCL / TCI](https://www.sharetechnote.com/html/5G/5G_QCL.html)、[MIMO DL](https://www.sharetechnote.com/html/5G/5G_MIMO.html)、[MIMO UL](https://www.sharetechnote.com/html/5G/5G_MIMO_UL.html)、[RSRP 等测量定义](https://www.sharetechnote.com/html/5G/5G_PowerDefinition.html) |
| 7 HARQ / 调度时序（38.213 §9/§10、38.321） | [HARQ](https://www.sharetechnote.com/html/5G/5G_HARQ.html)、[HARQ-ACK Codebook](https://www.sharetechnote.com/html/5G/5G_Harq_Codebook.html)、[Slot Configuration](https://www.sharetechnote.com/html/5G/5G_SlotConfiguration.html)、[Slot Format Combination](https://www.sharetechnote.com/html/5G/5G_SlotFormatCombination.html)、[Self-Contained Slot](https://www.sharetechnote.com/html/5G/5G_SelfContainedSlot.html)、[TDRA 适用范围](https://www.sharetechnote.com/html/5G/5G_ApplicableTimeDomainAllocation.html)、[MAC Overview](https://www.sharetechnote.com/html/5G/5G_MAC.html)、[Timing Advance](https://www.sharetechnote.com/html/5G/5G_TimingAdvance.html) |
| 常备工具页 | [MCS/TBS/Code Rate](https://www.sharetechnote.com/html/5G/5G_MCS_TBS_CodeRate.html)、[Max Throughput Estimation](https://www.sharetechnote.com/html/5G/5G_MaxThroughputEstimation.html)、[FR / Operating Band](https://www.sharetechnote.com/html/5G/5G_FR_Bandwidth.html)、[PHY 参数结构](https://www.sharetechnote.com/html/5G/5G_ParameterStructure_Phy.html)、[Waveform](https://www.sharetechnote.com/html/5G/5G_Waveform.html)、[UL Timing](https://www.sharetechnote.com/html/5G/5G_UL_Timing.html) |

## 2026-09-08 抽查核对记录

- Numerology 页：与本地 R19 38.211 Table 4.2-1 一致——μ=0..6 共 7 种 numerology（480/960 kHz 为 R17 加入、R19 仍在），Extended CP 仅 μ=2。
- 38.300 支持矩阵：网站汇总与本地 38.300 v19.3.0 Table 5.1-1 一致——PSS/SSS/PBCH 用 μ={0,1,3,4,5,6}（不用 μ=2），其他信道用 μ={0,1,2,3,5,6}（不用 μ=4）；「载波最多 275 PRB」在 R19 里出自 38.300（而非网站引用的旧版 38.211 表格位置）。
- Resource Grid 页：概念与 38.211 §4.4 一致（每 numerology/方向/天线端口一个网格；RE=(k,l)；Point A 起 CRB 编号）；页面截图多为 R15（只到 μ=4），文字已补充 R17 的 μ5/6 说明。
- Frame Structure 页抽查时加载超时，用时直接打开；主要内容为帧/子帧/时隙结构图，可对照 38.211 §4.3 与 Table 4.3.2-1/-2。

## 使用注意

- 网站以 R15–R17 为主，少量 R18/R19；R19 中部分小节号、表格位置有变化，引用前以本地 `90-Attachments/3GPP规范/` 的 PDF 为准。
- 站点存在个别历史笔误/拼写不一致（如 BWP 页文件名 `5G_CarrrierBandwidthPart.html` 多打了个 r），URL 有效；找不到页面时回总索引按字母定位。
- 更适合当「直觉地图」而不是速查表：数字、公式、条件语句都要回 spec 验证。

## 关联

- [[3GPP-38系列-NR物理层规范]]（L1 学习计划主文档）
- [[学习-38.211-阶段1-帧结构与时频资源]]（已配合本站 Numerology / Frame Structure / Resource Grid 页）
- [[领域-L1物理层]]
- [[仓库-srsRAN_Project-PHY总览]]（看完概念后对照代码）
