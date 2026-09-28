---
type: resource
tags: [L1, 物理层, 3GPP, SSB, CORESET0, PDCCH, DCI, SIB1, Type0-PDCCH, 小区搜索]
layer: L1
created: 2026-09-23
updated: 2026-09-23
status: active
source: 3GPP TS 38.213 §13 / §4.1；MATLAB 5G Toolbox《NR Cell Search and MIB and SIB1 Recovery》；见 [[3GPP-38系列-NR物理层规范]]
---

# CORESET 0 时频位置计算（表 13-3 / 13-11）

从 MIB 字段推到 CORESET 0 / PDCCH / SIB1 的**可算坐标**。频域查 38.213 表 13-1…13-10，时域查表 13-11…13-15；本文用 MATLAB 例的参数走表 13-3 + 表 13-11。

## Example 背景

对应 MathWorks 5G Toolbox 示例 *NR Cell Search and MIB and SIB1 Recovery*（`loadFromFile = 0`，本地 `nrWaveformGenerator` 生成）。下表**只收脚本里写死的参数**，以及该示例官方运行日志里打印出来的解码结果。

**1) 脚本 `config`（TX 生成）**

```matlab
config.NCellID = 102;
config.BlockPattern = 'Case B';
config.TransmittedBlocks = ones(1,8);
config.SubcarrierSpacingCommon = 15;
config.EnableSIB1 = 1;
config.MinChannelBW = 5;
boost = 6;
config.Power = zeros(1,8);  config.Power(1) = boost;
SNRdB = 20;   % AWGN（相对被 boost 的 SSB）
```

**2) `hSIB1WaveformConfiguration` 里与坐标相关的默认（同一示例）**

| 项 | 值 | 含义 |
| --- | --- | --- |
| DCI 频域 | `hRIV(csetNRB, 0, 8)` | BWP 内 **RB start=0，长 8 RB** |
| DCI 时域 | `TimeDomainResources = 0` | 38.214 Table 5.1.2.1.1-2 **行 1** |
| DCI MCS / RV | 0 / 0 | QPSK、初传 |
| SI-RNTI | 65535 | DCI 1_0 加扰 |
| CORESET 交织 | `REGBundleSize=6, InterleaverSize=2, ShiftIndex=NCellID` | 38.211 §7.3.2.2 |
| 时长 `numSubframes` | 20 | 一波 20 ms |

**3) 官方运行日志里的 MIB（解码结果，不是手填）**

| 项 | 日志值 | 含义 |
| --- | --- | --- |
| k_SSB | **0** | 与 CRB 栅格对齐 |
| SubcarrierSpacingCommon | **15** | μ=0 |
| DMRSTypeAPosition | **3** | PDSCH Type A DM-RS 在符号 3 |
| NFrame | 0 | 示意帧号 |
| SSB index | 0 | 检出的最强块（Power boost 的那个） |
| PDCCH | AL=**8**, candidate #1 | 盲检命中 |

**4) 手算用的表索引**（`PDCCHConfigSIB1` 由 `getWavegenSSBurstConfig` 填，脚本未写死）：

- `controlResourceSetZero = 0` → 表 13-3：**48 RB，Nsymb=1，Offset=2，pattern 1**
- `searchSpaceZero = 4` → 表 13-11：**O=5，M=1，First symbol=0**（与 TX 频谱里 SIB1 在 ~5 ms 后出现一致；若为 0 则 n0=i_SSB，会贴着 SSB）

SSB 中心频点取相对 0 Hz；L_max = `numel(TransmittedBlocks)` = 8。

## 表 13-3（频域）

**规范位置**：3GPP TS 38.213 §13, Table 13-3（见 [[3GPP-38系列-NR物理层规范]]；本地 PDF：`90-Attachments/3GPP规范/`）

适用：`{SSB SCS, 公共 SCS} = {30, 15}` kHz，信道最小带宽 5 或 10 MHz。

**列含义**

| 列       | 含义                                                                          |
| ------- | --------------------------------------------------------------------------- |
| Index   | 表行号 = MIB `pdcch-ConfigSIB1` 的 **controlResourceSetZero**（高 4 bit，0…15）     |
| pattern | SS/PBCH block 与 CORESET 的复用方式；**1** = 时分，CORESET 在 SSB 之后                   |
| NRB     | CORESET0 频域宽度（**公共 SCS** 的 RB 数）                                            |
| Nsymb   | CORESET0 时域长度（OFDM 符号数）                                                     |
| Offset  | 从 **SSB 最低 RB** 到 **CORESET0 最低 RB** 的距离（**公共 SCS** 的 RB；CORESET 在 SSB 低频侧） |

**数值**（本例 Index = 0 一行加粗）

| Index | pattern | NRB | Nsymb | Offset |
| ---: | ---: | ---: | ---: | ---: |
| **0** | **1** | **48** | **1** | **2** |
| 1 | 1 | 48 | 1 | 6 |
| 2 | 1 | 48 | 2 | 2 |
| 3 | 1 | 48 | 2 | 6 |
| 4 | 1 | 48 | 3 | 2 |
| 5 | 1 | 48 | 3 | 6 |
| 6 | 1 | 96 | 1 | 28 |
| 7 | 1 | 96 | 2 | 28 |
| 8 | 1 | 96 | 3 | 28 |
| 9–15 | — | 保留 | | |

Offset 定义（3GPP TS 38.213 §13，Tables 13-1 说明段）：以 **CORESET SCS**（= subCarrierSpacingCommon）的 RB 为单位，从 CORESET 最小 RB 到与 SSB 第一个 RB 重叠的公共 RB 的最小下标：

```text
Point A --offsetToPointA--> SSB 最低 RB --k_SSB--> SSB
                              │
                              │← Offset（表 13-3）
                              ▼
                       CORESET0 最低 RB
```

注意：`offsetToPointA` 在 **SIB1**，不是 MIB；收 CORESET0 时只用相对 SSB 的关系。

## 表 13-11（时域）

**规范位置**：3GPP TS 38.213 §13, Table 13-11（见 [[3GPP-38系列-NR物理层规范]]）

适用：multiplexing pattern **1** + **FR1**。

**列含义**

| 列             | 含义                                                               |
| ------------- | ---------------------------------------------------------------- |
| Index         | 表行号 = MIB `pdcch-ConfigSIB1` 的 **searchSpaceZero**（低 4 bit，0…15） |
| O             | 监听时机的 **slot 偏移**（进入 n0 公式）                                      |
| SS set / slot | 每个 slot 里 Type0 搜索空间集的个数                                         |
| M             | 相邻 SSB 监听 slot 的 **错开步进**（n0 公式中的 `⌊i_SSB·M⌋`）                   |
| First symbol  | slot 内 CORESET0 的 **起始 OFDM 符号**（配合 Nsymb 得到符号区间）                |

**数值**（本例 Index = 4 一行加粗）

| Index | O | SS set / slot | M | First symbol |
| ---: | ---: | ---: | ---: | --- |
| 0 | 0 | 1 | 1 | 0 |
| 1 | 0 | 2 | 1/2 | 偶数 occasion：0；奇数：Nsymb |
| 2 | 2 | 1 | 1 | 0 |
| 3 | 2 | 2 | 1/2 | 偶：0；奇：Nsymb |
| **4** | **5** | **1** | **1** | **0** |
| 5 | 5 | 2 | 1/2 | 偶：0；奇：Nsymb |
| 6 | 7 | 1 | 1 | 0 |
| 7 | 7 | 2 | 1/2 | 偶：0；奇：Nsymb |
| 8 | 0 | 1 | 2 | 0 |
| 9 | 5 | 1 | 2 | 0 |
| 10 | 0 | 1 | 1 | 1 |
| 11 | 0 | 1 | 1 | 2 |
| 12 | 2 | 1 | 1 | 1 |
| 13 | 2 | 1 | 1 | 2 |
| 14 | 5 | 1 | 1 | 1 |
| 15 | 5 | 1 | 1 | 2 |

**公式与相关量**（n0 定义见 3GPP TS 38.213 §13 正文，与 Table 13-11 配套）

| 符号 | 含义 |
| --- | --- |
| i_SSB | 半帧内第几个候选 SSB，0…L_max−1；低位来自 PBCH DM-RS 序列号，L_max=64 时高位来自 PBCH 载荷 ā |
| μ | log2(SCS_common / 15 kHz)，本例 0 |
| N | 每帧 slot 数 = 10·2^μ，本例 10 |
| n0 | 帧内监听起始 slot：`n0 = (O·2^μ + ⌊i_SSB·M⌋) mod N` |

FR1 + pattern 1：从 n0 起 **连续 2 个 slot**（n0、n0+1）各一次监听机会；初始小区搜索默认含 SSB 的半帧每 20 ms 出现，监听按同一周期重复。

## 频域计算

（算式与 Offset 定义见 3GPP TS 38.213 §13，[[3GPP-38系列-NR物理层规范]]；表值见上方 Table 13-3）

```text
① SSB 中心 = GSCN 对应频点（算相对偏移时取 0）
② SSB 最低子载波 = 中心 − 3.6 MHz   （Case B：20 RB @30 kHz = 7.2 MHz）
③ k_SSB 对齐 CRB 栅格 → 「SSB 最低 RB」
④ 查表 13-3 Index 0 → Offset = 2，NRB = 48
⑤ CORESET0 最低 RB = SSB 最低 RB − Offset×12×15 kHz
⑥ CORESET0 宽度 = NRB×12×15 kHz
```

| 量 | 算式 | 结果 |
| --- | --- | --- |
| SSB 最低 RB | 0 − 3.6 MHz | −3.6 MHz |
| Offset 换算 | 2×12×15 kHz | 0.36 MHz |
| CORESET0 起点 | −3.6 − 0.36 | **−3.96 MHz** |
| CORESET0 宽度 | 48×12×15 kHz | **8.64 MHz** |
| CORESET0 终点 | −3.96 + 8.64 | **+4.68 MHz** |
| PDSCH（8 RB） | 与 CORESET 同起点，+8×12×15 kHz | **−3.96 … −2.52 MHz** |

## 时域计算

（n0 与监听规则见 3GPP TS 38.213 §13，[[3GPP-38系列-NR物理层规范]]；表值见上方 Table 13-11）

```text
① 已知 i_SSB；公共 SCS=15 kHz → μ=0，N=10
② 查表 13-11 Index 4 → O=5，M=1，First symbol=0
③ n0 = (O·2^μ + ⌊i_SSB·M⌋) mod N
④ FR1 pattern 1：听 slot n0 与 n0+1
⑤ 每个 slot 内：符号 [First, First+Nsymb) = 符号 0（Nsymb=1）
⑥ 周期 20 ms
```

| i_SSB | n0 = (5+i) mod 10 | 监听 slot | 符号 |
| ---: | ---: | --- | --- |
| 0 | 5 | 5, 6 | 0 |
| 1 | 6 | 6, 7 | 0 |
| 2 | 7 | 7, 8 | 0 |
| 3 | 8 | 8, 9 | 0 |
| 4 | 9 | 9, 10 | 0 |
| 5 | 0 | 0, 1 | 0 |
| 6 | 1 | 1, 2 | 0 |
| 7 | 2 | 2, 3 | 0 |

PDSCH（SIB1）：K0=0，38.214 表行 1 + `DMRSTypeAPosition=3` → 示意 **符号 3–13**（与 PDCCH 的符号 0 不同）。

CORESET **每次只占 Nsymb=1 个符号**，不是整个 slot；pattern 1 的「2 个 slot」是两次独立监听机会。

## SSB / CORESET / PDCCH / DCI / SIB1 位置（按上算例）

DCI 与 MATLAB `hSIB1WaveformConfiguration` 一致：`hRIV(48, 0, 8)` → PDSCH 在 BWP 最低 **8 RB**；`TimeDomainResources=0` → 38.214 Table 5.1.2.1.1-2 行 1；`DMRSTypeAPosition=3`（日志值）→ Type A 从符号 3 起（示意 S=3, L=11）。

**1) 频域（横轴：相对 SSB 中心，MHz）**  
SSB 与 CORESET **大段重叠**；PDSCH 只占 CORESET 低频侧 8 个 RB，不是整条 CORESET。

```text
  MHz  -3.96    -3.60      -2.52     0        +3.60      +4.68
         │        │          │        │          │          │
CORESET0 ├──────────────────────────────────────────────────┤ 48 RB = 8.64 MHz
/BWP     │        │          │        │          │          │
PDSCH    ├────────┤          │        │          │          │  8 RB = 1.44 MHz
(SIB1)   │ 8 RB   │          │        │          │          │  ← DCI RIV: start=0,L=8
         │        ├──────────────────────────────┤          │
SSB      │        │     20 RB @30 kHz = 7.2 MHz │          │
         │        │   PSS│PBCH│SSS│PBCH          │          │
         │        │          │        │          │          │
         ◄Offset=2 RB(0.36)►        │          │          │
         │        │          │        │          │          │
PDCCH    └ 在 CORESET 占用的 CCE 上（频域可到 CORESET 两端，不限于 8 RB）
```

**2) 时域（两套 numerology，勿画进同一符号轴）**

```text
半帧（30 kHz 符号，Case B，i_SSB=0…7）
符号:  4  8    16 20    32 36    44 48     → 8 个 SSB，约 0–2 ms
       └SSB0┘  └SSB1┘  └SSB2┘  └SSB3┘ …   （4 符号一块）

帧（15 kHz slot，μ=0，共 10 slot）
slot:  0   1   2   3   4  [ 5 ] [ 6 ]  7   8   9
                              ▲     ▲
                    n0=5 时的两次监听（i_SSB=0）

slot 5 内部（14 符号，示意 TypeA pos=3、时域行 1）:
符号: 0   1   2   3   4 ………………… 13
      ├───┤   ├──────────────────────┤
      PDCCH   PDSCH(SIB1) S=3,L=11（符号 3–13）
      CORESET   DM-RS 起点 = 3（DMRSTypeAPosition）
      Nsymb=1
      （slot 6 符号 0 再听一次 PDCCH，pattern 1）
```

**3) 各块位置一览**

| 块 | 频域 | 时域 | 谁定义 |
| --- | --- | --- | --- |
| SSB | 中心=GSCN，−3.6…+3.6 MHz | Case B 半帧内 `{4,8,16,20}+28n`，4 符号 | 3GPP TS 38.213 §4.1, Table 4.1-1（[[3GPP-38系列-NR物理层规范]]） |
| CORESET0 | −3.96…+4.68 MHz（48 RB） | slot n0、n0+1 的 **符号 0**（1 符号） | 3GPP TS 38.213 §13, Table 13-3 / 13-11 |
| PDCCH | CORESET0 内的 CCE（可占满 48 RB） | 与 CORESET0 同矩形 | 38.213 §13；例解出 AL=8 |
| DCI 1_0 | **不是独立资源**，承载在 PDCCH 上 | 同上 | 3GPP TS 38.212 §7.3.1.2.1（[[3GPP-38系列-NR物理层规范]]） |
| SIB1 PDSCH | BWP 最低 **8 RB**（−3.96…−2.52 MHz） | K0=0，时域行 1：S=3,L=11 | 3GPP TS 38.214 §5.1（[[3GPP-38系列-NR物理层规范]]） |

> 图中 DCI 不单独成块：盲检成功的 PDCCH 码字解出来就是 DCI 1_0，再用它切出 PDSCH。

## 表号速查

均出自 **3GPP TS 38.213 §13**（[[3GPP-38系列-NR物理层规范]]）：

| {SSB SCS, 公共 SCS} | minBW | CORESET 表 | 监听表 |
| --- | --- | --- | --- |
| {15,15} | 5/10 MHz | 13-1 | 13-11（FR1 pattern 1） |
| {15,30} | 5/10 MHz | 13-2 | 13-11 |
| **{30,15}** | **5/10 MHz** | **13-3** | **13-11** |
| {30,30} | 5/10 MHz | 13-4 | 13-11 |
| {30,15} | 40 MHz | 13-5 | 另查 |
| FR2 | — | 13-7…13-10 | 13-12 等 |

## 关联

- [[学习-阶段2-SSB与小区搜索]]（阶段 2 主笔记、MIB→SIB1 链路）
- [[小区搜索流程分步详解]]（Step 4–6）
- [[学习-38.211-阶段1-帧结构与时频资源]]（k_SSB / Point A / CRB）
- [[PSS检测与同步实现参考]]（MATLAB / OAI 对照）
- [[PSS相关检测与NID2判定]]（PSS m 序列与 N_ID^(2) 相关检测）
