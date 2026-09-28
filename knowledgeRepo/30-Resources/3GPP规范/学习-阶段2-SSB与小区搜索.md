---
type: resource
tags: [L1, 物理层, 3GPP, 学习计划, SSB, 小区搜索, PBCH, MIB]
layer: L1
created: 2026-09-08
updated: 2026-09-23
status: active
source: 3GPP TS 38.211/38.212/38.213/38.331（R19，ETSI）
source_url: https://www.3gpp.org/DynaReport/38211.htm
---

# 学习：阶段 2 —— SSB 与小区搜索

## 一句话

UE 开机后不知道任何频率/时间/小区信息，小区搜索就是靠 SSB（SS/PBCH block）完成“定时同步 + 频偏估计 + 拿 PCI + 读 MIB”，再用 MIB 里的 CORESET#0/搜索空间配置去解 SIB1，进入可接入状态。整条链：PSS → SSS → PBCH/MIB → Type0-PDCCH → PDSCH(SIB1)。

## 阅读范围

- 主读：
  - 3GPP TS 38.211 §7.4.2（PSS/SSS 序列与 PCI）、§7.4.3（SS/PBCH block 结构与映射）
  - 3GPP TS 38.213 §4.1（小区搜索、SSB 时域位置 Case A–G、SSB index 确定）
  - 3GPP TS 38.212 §7.1（BCH/PBCH：载荷生成、加扰、CRC、Polar、速率匹配）
- 配套：38.331（MIB 字段、SIB1 结构）、38.215（SS-RSRP）、[[概念-NR时间单位-Tc与Ts]]、[[学习-38.211-阶段1-帧结构与时频资源]]（Point A/CRB）
- PDF：38.211 / 38.212 / 38.213 / 38.331（`90-Attachments/3GPP规范/`）

## 1 小区搜索流程总览

```
时频粗同步 + 检测 PCI
  PSS（3 种序列）→ 符号定时、载波频偏粗估计、N_ID^(2)
  SSS（336 种）→ N_ID^(1)，得 PCI = 3·N_ID^(1) + N_ID^(2)
      ↓
PBCH DM-RS：SSB index 低位 + 信道估计
PBCH/MIB：SFN、k_SSB、subCarrierSpacingCommon、CORESET#0/SS0 配置
      ↓
Type0-PDCCH CSS 里收 DCI 1_0（SI-RNTI 加扰）
      ↓
PDSCH：SIB1（含 PLMN、cell selection、offsetToPointA、SCS-SpecificCarrier…）
```

关键点：NR 的 SSB 不像 LTE 那样固定在系统带宽中心，而是可以放在频带内特定位置（SS raster），所以“SSB 在网格里到底哪个 RB”必须由 k_SSB/offsetToPointA 显式告诉 UE——这正是阶段 1 里 Point A 讨论的用途。

### 1.1 每步在“消除什么不确定性”

| 步骤          | 输入            | 输出/收获                                           | 主依据                |
| ----------- | ------------- | ----------------------------------------------- | ------------------ |
| PSS         | 时域信号          | 符号定时 + 频偏粗估 + N_ID^(2)（3 选 1）                   | 38.211 §7.4.2.2    |
| SSS         | 定时 + N_ID^(2) | N_ID^(1)（336 选 1）→ PCI = 3·N_ID^(1)+N_ID^(2)    | 38.211 §7.4.2.3    |
| PBCH DM-RS  | SSB 位置        | SSB index 低位（2/3 bit）+ 解 PBCH 用的信道估计            | 38.211 §7.4.1.4    |
| PBCH/MIB    | 432 个 RE      | SFN（6 MSB + 4 LSB）、k_SSB、SIB1 SCS、CORESET#0/SS0 | 38.212 §7.1、38.331 |
| Type0-PDCCH | CORESET#0/SS0 | DCI 1_0（SI-RNTI）→ SIB1 的 PDSCH 调度               | 38.213 §13         |
| PDSCH/SIB1  | DCI 1_0       | offsetToPointA、载波/BWP、接入参数 → 可做小区选择             | 38.331             |

### 1.2 几个关键衔接

- **PCI 是分两步拼出来的**：PSS 只有 3 个候选，SSS 有 336 个；先 PSS 后 SSS 让相关运算量少两个数量级。
- **SSB index 是分两段拿到的**：低位在 PBCH DM-RS 序列 index，高位在 PBCH 载荷的 ā̄ 位。
- **SFN 是分两处带的**：MIB 带 10 位 SFN 的 6 个 MSB，PBCH 附加位带 4 个 LSB。
- **频域位置是分两批给的**：MIB 给 k_SSB（SSB 相对网格的子载波偏移），SIB1 给 offsetToPointA（Point A 相对 SSB 的 RB 偏移）——两批合起来才定位完整网格。
- **PBCH 与 SIB1 的节奏不同**：PBCH/BCH 80 ms TTI（可软合并、需要判断 80 ms 边界），SIB1 默认 160 ms 周期调度；别把两个“周期”搞混。

更细的逐步版（含每步的候选数、时序小抄、易错点）放在子目录：[[小区搜索流程分步详解]]。

PSS 定时/频偏怎么用 DSP 算出来，单独见子目录里的 [[PSS检测与同步-定时频偏估计]]。

## 2 SSB 的时频结构（38.211 §7.4.3.1）

- 一个 SSB = **4 个 OFDM 符号 × 240 个子载波（20 个 RB）**，子载波在 SSB 内部编号 0..239。
- 内容分布（Table 7.4.3.1-1）：

| 信号 | 符号（SSB 内） | 子载波 | 说明 |
| --- | --- | --- | --- |
| PSS | 0 | 56–182（127 个） | m 序列 |
| SSS | 2 | 56–182（127 个） | 两个 m 序列相乘 |
| PBCH | 1、3 | 全部 0–239 | 数据 + DM-RS |
| PBCH | 2 | 0–47、192–239（边缘 96 个） | SSS 占据中间 |
| PBCH DM-RS | 1、2、3 | 间隔 4 的梳齿位置 | v = PCI mod 4 |

- PBCH 数据 RE 共 432 个（576 个可用 RE − 144 个 DM-RS），QPSK 调制 → 864 bit，正好对应 38.212 速率匹配后的 E=864。
- 天线端口 4000：PSS/SSS/PBCH/PBCH DM-RS 共用同一端口；同一 SSB index、同一中心频点的 SSB 之间满足 QCL（延迟扩展/多普勒等大尺度参数可互推）。
- 3 MHz 窄信道场景：SSB 边缘子载波会被“打孔”（puncturing），只保证中间 12 个 RB 可收。

## 3 PSS / SSS 与 PCI（38.211 §7.4.2）

- PCI（物理小区 ID）：N_ID^cell = 3·N_ID^(1) + N_ID^(2)
  - N_ID^(2) ∈ {0,1,2}：由 PSS 区分（3 条不同的 m 序列相位/根）；
  - N_ID^(1) ∈ {0,…,335}：由 SSS 区分（336 个）；
  - 共 1008 个 PCI。
- PSS/SSS 序列长度都是 127，映射在 SSB 中间的 127 个子载波上（k=56..182），与 LTE 的 62 个完全不同。
- 同一 SSB 内 PSS、SSS、PBCH 使用相同 SCS 与 CP；接收端可假设 SSS/PBCH DM-RS/PBCH 数据 EPRE 相同，PSS/SSS 的 EPRE 比值是 0 dB 或 3 dB（38.213 §4.1）。

## 4 SSB 时域位置与 Case（38.213 §4.1）

候选 SSB 只在“含 SSB 的半帧”内出现，首符号位置由 Case 决定（下表按 R19 简化）：

| Case | SSB SCS | 主要场景          | 半帧内首符号模式（含 n 范围）                        | L_max             |
| ---- | ------- | ------------- | ------------------------------- | ----------------- |
| A    | 15 kHz  | FR1           | {2,8} + 14·n；L_max=4 时 n=0,1；L_max=8 时 n=0..3     | ≤3 GHz：4；>3 GHz：8 |
| B    | 30 kHz  | FR1           | {4,8,16,20} + 28·n；L_max=4 时 n=0；L_max=8 时 n=0,1  | 4 或 8             |
| C    | 30 kHz  | FR1           | {2,8} + 14·n；L_max=4 时 n=0,1；L_max=8 时 n=0..3     | 4 或 8             |
| D    | 120 kHz | FR2-1/FR2-NTN | {4,8,16,20} + 28·n；n=0..15（4×16=64）                | 64                |
| E    | 240 kHz | FR2-1/FR2-NTN | {8,12,16,20,32,36,40,44} + 56·n；n=0..7（8×8=64）    | 64                |
| F    | 480 kHz | FR2-2         | {2,9} + 14·n；n=0..31（2×32=64）                      | 64                |
| G    | 960 kHz | FR2-2         | {2,9} + 14·n；n=0..31（2×32=64）                      | 64                |

补充：
- 具体用哪个 Case 与频段、SSB SCS 相关（38.101-x 按频段规定），同一小区所有 SSB 用同一个 Case。
- **L_max 不是 n 的取值**：n 是公式的“第几组 slot”，L_max 是候选 SSB 总数 = 基础集合个数 × 合法 n 的个数。例：Case B 基础集合 4 个，n=0 → 4 个候选；n=0,1 → 8 个。没有“n=4 或 8”的取法。
- 候选都落在**含 SSB 的那个半帧**内，不是整个 10 ms 帧对折重复；Case B 最多 8 个，不是 16。
- L_max 是小区最多可用的 SSB index 数；实际发哪些由高层 ssb-PositionsInBurst 决定（波束扫描：每个 SSB index 常对应一个波束方向）。
- 初始小区选择时，UE 假设含 SSB 的半帧每 **2 帧（20 ms）**出现一次；接入后网络可配更细周期（如 5/10/20/40/80/160 ms）。
- 3 MHz 信道、共享频谱（NR-U）等有额外打孔/窗口规则，用到时再翻。

## 5 SSB index 怎么确定

候选 SSB 在半帧内按时间从 0 编号；UE 需要知道收到了哪个 index（波束/测量都依赖它）：

- **低位**：来自 PBCH DM-RS 序列 index——L_max=4 时 2 个 LSB；L_max>4 时 3 个 LSB。
- **高位**：来自 PBCH 载荷里的 ā̄ 位（38.212 §7.1.1，内容随 L_max 变化）：例如 L_max=64 时用 3 个 ā̄ 位作 index 的 3 个 MSB。
- 无共享频谱时，SSB index = 候选 index；共享频谱场景另有 QCL/发现突发窗口规则。

## 6 PBCH / MIB：从 32 bit 到 SIB1 入口

### MIB 字段（38.331，共 23 bit）

Spec 格式（38.331 `MIB`，注释为物理层用途）：

```text
MIB ::= SEQUENCE {
  systemFrameNumber          BIT STRING (SIZE (6)),   -- SFN[9:4]，高 6 位；低 4 位在 PBCH 载荷
  subCarrierSpacingCommon    ENUMERATED {scs15or60,   -- 0：FR1 15 kHz / FR2 60 kHz（common/BWP 的 SCS）
                                         scs30or120},-- 1：FR1 30 kHz / FR2 120 kHz
  ssb-SubcarrierOffset       INTEGER (0..15),         -- k_SSB 低 4 位；FR1 最高位由 PBCH 的 1 个 ā 补
  dmrs-TypeA-Position        ENUMERATED {pos2, pos3}, -- PDSCH/PUSCH Type A 首个 DM-RS 符号
  pdcch-ConfigSIB1           INTEGER (0..255),        -- 拆成 8 bit：见下
  cellBarred                 ENUMERATED {barred, notBarred},
  intraFreqReselection       ENUMERATED {allowed, notAllowed},
  spare                      BIT STRING (SIZE (1))    -- 保留
}
-- 合计 6+1+4+1+8+1+1+1 = 23 bit（BCCH-BCH 传输块再去掉 1 bit 消息类型前导）
```

结构体形式（便于对照实现 / MATLAB）：

```matlab
% ---- MIB（RRC 23 bit，来自 BCH 传输块 trblk(2:end)）----
mib.systemFrameNumber        % 6 bit, 0..63      SFN 高 6 位 → NFrame(9:4)
mib.subCarrierSpacingCommon  % 1 bit             0→15/60 kHz, 1→30/120 kHz
mib.ssb_SubcarrierOffset     % 4 bit, 0..15      k_SSB 低 4 位
mib.dmrs_TypeA_Position      % 1 bit             0→pos2, 1→pos3
mib.pdcch_ConfigSIB1         % 8 bit, 0..255
%   ├─ 高 4 bit = controlResourceSetZero (0..15) → 38.213 表 13-1..13-10（CORESET0）
%   └─ 低 4 bit = searchSpaceZero       (0..15) → 38.213 表 13-11..13-15（监听时机）
mib.cellBarred               % 1 bit             1=barred, 0=notBarred
mib.intraFreqReselection     % 1 bit
mib.spare                    % 1 bit
```

拼装后的“初始系统信息”坐标（解码后常用的派生量）：

```matlab
sys.NFrame   = mib.systemFrameNumber*16 + sfn4lsb;          % 10 bit SFN = 6 MSB + 4 LSB
sys.scsCommon = scsCommon(mib.subCarrierSpacingCommon + 1); % FR1 {15,30} / FR2 {60,120}
sys.k_SSB    = mib.ssb_SubcarrierOffset + msb_kssb;         % 4 bit +（需要时）1 bit ā
sys.dmrs_TypeA_Position = 2 + mib.dmrs_TypeA_Position;      % 2 或 3
sys.cset0Idx = floor(mib.pdcch_ConfigSIB1 / 16);            % 表 13-x Index
sys.ss0Idx   = mod(mib.pdcch_ConfigSIB1, 16);               % 表 13-11+ Index
```

### PBCH 载荷与编码（38.212 §7.1）

```text
PBCH 物理载荷 32 bit（38.212 §7.1.1，交织前逻辑）:
┌──────────────────────────┬─────────────────────────────────────────────┐
│ BCH 传输块 24 bit        │ 物理层附加 8 bit                              │
│  1 bit 消息类型 + MIB 23 │                                               │
├──────────────────────────┼─────────┬──────┬────────────────────────────┤
│                          │ sfn4lsb │ HRF  │ ā ā ā（3 bit，随 L_max 变）│
│                          │ SFN[3:0]│ 半帧 │  L_max=4/8: k_SSB 的 MSB 等│
│                          │ 4 bit   │ 0/1  │  L_max=64:  i_SSB 高 3 位  │
└──────────────────────────┴─────────┴──────┴────────────────────────────┘
再经 Table 7.1.1-1 交织 → 加扰(c_init←PCI) → CRC24 → Polar → 864 bit → QPSK/432 RE
```

- PBCH 物理载荷共 **32 bit**：高层 BCH 传输块（MIB 内容）+ 物理层附加位——SFN 的 4 个 LSB、半帧指示位（HRF）、3 个 ā̄ 位；经 Table 7.1.1-1 的交织表重排后再加扰。
- SFN 共 10 位 = MIB 的 6 MSB + PBCH 里带的 4 LSB（38.331 明确这 4 位在 MIB 编码之外）。
- 编码链：32 bit 载荷 → 加扰（c_init 与 PCI 相关，80 ms 周期相关）→ 附 24 bit CRC → Polar 编码 → 速率匹配到 864 bit → QPSK → 432 个 RE。
- BCH 传输块每 80 ms 来一个；PBCH 在 80 ms 内的不同帧上重复发送，靠扰码/内容变化确定帧位置（细节属于阶段 4 编码 + PBCH DM-RS 精读）。

### MIB 之后怎么找到 SIB1

- pdcch-ConfigSIB1 的 4+4 bit 查 38.213 §13 的表，得到 CORESET#0 的时频大小和 SearchSpace#0 的监测时机。表 13-3 / 13-11 释义、手算与 MATLAB 例时频图见 [[CORESET0时频位置计算]]。
- 是否需要 CORESET#0：k_SSB 指示（FR1 中 k_SSB<24 表示有；≥24 表示该 SSB 不带 SIB1，pdcch-ConfigSIB1 另有含义，见 38.213 §13/38.331）。
- 在 Type0-PDCCH CSS 中监听 DCI 1_0（CRC 用 SI-RNTI 加扰），按 DCI 指示去 PDSCH 收 SIB1。
- SIB1 里才有 offsetToPointA、scs-SpecificCarrierList、initial DL/UL BWP 等“完整网格参数”——到此才和阶段 1 的 Point A/CRB 闭环。

## 7 易错点

- SSB 不是“在信道中心”，位置由同步光栅 + k_SSB + offsetToPointA 决定；LTE 思维要丢掉。
- SSB 的 20 个 RB 是以 **SSB 自己的 SCS** 计的（FR1 15/30 kHz、FR2 120/240/480/960 kHz），不是 subCarrierSpacingCommon 的网格。
- SFN 10 位 = MIB 6 MSB + PBCH 4 LSB；别以为 SFN 只有 8 位或全在 MIB 里。
- PSS 只给 N_ID^(2)（0..2），SSS 给 N_ID^(1)（0..335），两者合起来才是 PCI；先 PSS 后 SSS 的顺序不能反。
- SSB index 的低位在 DM-RS 序列里、高位在 PBCH 载荷里，不是简单从时域位置直接读。

## 练习（收尾动作）

1. 画一个 SSB 的 4×20 RB 网格：标出 PSS/SSS/PBCH/DM-RS 的位置（可用 Table 7.4.3.1-1）。
2. 选 Case A（15 kHz、FR1、>3 GHz），写出半帧内 8 个候选 SSB 的首符号位置，验证与 L_max=8 一致。
3. 走一遍“MIB 字段 → pdcch-ConfigSIB1 → CORESET#0/SS0 → SIB1”的手写链路，把每一步对应的规范小节标出来。

### 练习 3 参考答案：MIB → SIB1 链路

链路一句话：**PBCH 32 bit 载荷 → MIB（23 bit）里的 subCarrierSpacingCommon / k_SSB / pdcch-ConfigSIB1 → 查 38.213 §13 得到 CORESET#0 与 SearchSpace#0 → 在 Type0-PDCCH CSS 盲检 DCI 1_0（SI-RNTI）→ 按 DCI 收 PDSCH → 解 DL-SCH 得 SIB1**。

| 步 | 做什么 | 输入 → 输出 | 对应规范 |
| --- | --- | --- | --- |
| 1 | 解 PBCH/BCH，得到 32 bit 载荷；其中含 MIB 字段与 8 bit 时序附加位（SFN 4 LSB、半帧位等） | SSB 定时 + PCI + DM-RS 给出的 i_SSB → MIB 内容 | 38.212 §7.1（编码链）、38.331（MIB 定义）、38.211 §7.4.1.4/§7.4.3.1 |
| 2 | 先看“Type0-PDCCH CSS 是否存在”：FR1 k_SSB<24、FR2 k_SSB<12 才存在 | k_SSB（MIB 4 bit + PBCH 附加 1 bit）→ 存在性判断 | 38.213 §4.1（判定句在 Cell search 末尾） |
| 3 | 取 SCS：`subCarrierSpacingCommon` 决定 CORESET#0（FR1）与 SIB1 PDCCH/PDSCH 所在网格的 SCS | 1 bit → 15/30 kHz（FR1） | 38.331（MIB）；38.213 §13 |
| 4 | 拆 `pdcch-ConfigSIB1`：高 4 bit = `controlResourceSetZero`，低 4 bit = `searchSpaceZero` | 8 bit 索引 → CORESET#0 表行 + SS#0 表行 | 38.331（MIB 字段）；38.213 §13 |
| 5 | 查 CORESET#0 配置表：得到 {SSB, PDCCH} SCS 对应的 multiplexing pattern、RB 数、符号数、相对 SSB 的频域 offset | 表 13-0…13-10 按场景选表（3/5/10 MHz 等） | 38.213 §13（Table 13-0..13-10A） |
| 6 | 查 SearchSpace#0 监测时机表：得到监测周期/偏移、slot 与首符号；pattern 1 时监测 slot 还依赖 i_SSB 与 SFN 奇偶 | SS#0 索引 → 具体监听时频位置 | 38.213 §13（Table 13-11..13-15A） |
| 7 | 在 CSS 上盲检 PDCCH：CRC 用 SI-RNTI（0xFFFF）加扰的 **DCI 1_0**，命中后读调度字段 | PDCCH 软比特 → DCI：时域分配 4 bit、频域资源分配、MCS 5 bit、RV、系统信息指示等 | 38.212 §7.3.1.2（DCI 1_0 字段）、38.213 §13（监测）、38.321（SI-RNTI 值） |
| 8 | 按 DCI 调度接收 SIB1 的 PDSCH（Type1 RA、单 TB），解调/解扰后走 DL-SCH → BCCH | DCI → SIB1 message | 38.214 §5.1.2/§5.1.3（PDSCH 资源分配与 MCS）、38.212 §6（DL-SCH 编码）、38.331（SIB1） |
| 9 | 读 SIB1 内容完成闭环：`offsetToPointA` + `SCS-SpecificCarrierList` 定 Point A/CRB；initial DL/UL BWP、TDD、PRACH 等接入参数 | 至此 UE 才知道完整频域网格，可以进入接入 | 38.331（SIB1 / ServingCellConfigCommonSIB） |

为什么要“绕”这么一圈而不是 MIB 直接给 SIB1 调度：PBCH 只有 32 bit，装不下 SIB1 的完整调度，所以用 8 bit 索引去查公共表（CORESET#0/SS#0），再用所有 UE 都会的 fallback 格式 DCI 1_0 + 固定的 SI-RNTI 在公共搜索空间里盲检；这一整条链的每一步都在逐步“放大坐标”：SSB → CORESET#0 → DCI → PDSCH → SIB1 → Point A。

## 待深入 / 疑问

- PBCH 加扰与 80 ms 软合并的细节（读 38.212 §7.1.2/§7.1.3 + PBCH DM-RS 序列），阶段 4 学 Polar 时一并处理。
- Type0-PDCCH 的 CORESET#0/SS0 表怎么查（38.213 §13），阶段 3 主战场。
- SS raster（GSCN）与绝对频点关系（38.101/38.104）——已沉淀 [[概念-NR频率栅格-NR-ARFCN与GSCN]]（频点规划时直接查）。
- 3 MHz / 共享频谱 / 多波束下 SSB 的细节规则（38.213 §4.1 剩余条款）。

## 关联

- [[CORESET0时频位置计算]]（表 13-3/13-11 列含义、频/时手算、SSB–CORESET–PDCCH–DCI–SIB1 位置图）
- [[PSS相关检测与NID2判定]]（PSS m 序列 / 循环移位 / 互相关定 N_ID^(2)）
- [[学习-38.211-阶段1-帧结构与时频资源]]（Point A / CRB / k_SSB 前置知识）
- [[概念-NR频率栅格-NR-ARFCN与GSCN]]（信道栅格 / 同步栅格 / GSCN 计算）
- [[概念-NR时间单位-Tc与Ts]]
- [[学习-38.211-第5章-通用功能]]（调制、序列、OFDM 基带是 SSB 发射的底层）
- [[3GPP-38系列-NR物理层规范]]（L1 学习计划主文档）
- [[仓库-srsRAN_Project-下行物理信道与OFDM发射]]（SSB 生成/映射代码）
- [[ShareTechnote-5G手册]]（Synchronization / PSS / SSS / SS Block / PBCH / Cell Search 页）
- [[领域-L1物理层]]
