---
type: note
tags: [RFSoC, RFDC, RF-ADC, RF-DAC, PG269, ZCU670, DFE, 驱动, AXI4-Stream, luxshare]
layer: L1
created: 2026-10-09
updated: 2026-10-09
status: active
source: PG269 v2.6（Zynq UltraScale+ RFSoC RF Data Converter Gen1/2/3/DFE）+ UG1530 v2.1 + embeddedsw xrfdc 驱动源码
---

# 学习：RFDC 使用方法梳理（PG269）

## 一句话总结

RFDC（RF Data Converter）是 Zynq UltraScale+ RFSoC 内直接采样的 **RF-ADC/RF-DAC 硬核 + 数字上下变频链**，用法分三层：**Vivado 里静态配 IP → 运行期用 `XRFdc_*` 驱动 API 改配置/读状态 → PL 侧走 AXI4-Stream 数据面**。软件**必须走驱动 API**，除状态/中断寄存器外不要直接写内部寄存器。

## 1 硬件结构（PG269 第 2 章）

- 转换器按 **tile** 组织，每个 tile 含 1/2/4 个 RF-ADC 或 RF-DAC，**tile 内自带 PLL 与时钟分发**逻辑
- 接收链：输入 buffer → ADC → **DDC（NCO 混频 + 抽取滤波）** → AXI4-Stream
- 发射链：AXI4-Stream → **DUC（内插 + NCO 混频）** → DAC → 输出
- 每个通道还有：QMC（正交调制校正）、粗延迟（coarse delay）、可选的多带（multi-band）
- Gen3/DFE 额外有 TDD 模式、片上时钟分发（clock forwarding）、DSA（数字步进衰减）等
- 本板（ZU67DR）：8× 2.95 GSPS + 2× 5.9 GSPS RF-ADC，8× 10 GSPS RF-DAC，详见 [[ZCU670-PL-PS-参数]]

## 2 三层使用模型（核心心智模型）

| 层 | 时机 | 做什么 | 关键点 |
| --- | --- | --- | --- |
| **Vivado IP 配置** | 设计期 | 启用 tile/block、设采样率与 PLL、选抽取/内插、混频模式、数据宽度、可选端口 | 配好烧进 bitstream；PL 配置完成后 IP 的**上电状态机自动完成** RFDC 上电与初始配置 |
| **驱动 API（XRFdc_*）** | 运行期 | 改 NCO/抽取、切 Nyquist 区、校准、MTS、上下电、处理中断 | 裸机与 Linux **同一套代码**，跑在 libmetal 之上 |
| **PL 数据面** | 运行期 | AXI4-Stream 收发 IQ 数据 | 流率 = 采样率 ÷ 抽取（× 内插）因子；位宽与 PL 时钟共同决定接口数量 |

## 3 第一步：Vivado 里配置 RFDC IP

IP catalog → **Zynq UltraScale+ RFSoC Data Converter**，双击 Customize IP。

**Presets 快捷配置**：`4x4`（4 ADC R2C + 4 DAC C2R）、`8x8`、`R2C/C2R Multi x2`、`C2C Multi x2`、`C2R Multi 2x2`、`C2R Multi x4`。

**Basic tab 的关键参数**：

| 分组 | 参数 | 说明 |
| --- | --- | --- |
| System Configuration | System Clock、参考时钟频率、器件/速度等级 | 决定 PLL 能否配出目标采样率 |
| Tile 使能 | ADC/DAC Tile 0–3 | 本板 ZU67DR 可用 tile 数见器件手册 |
| Tile 级 | Sampling Rate、PLL Enable、RefClkDiv / FeedbackDiv / OutputDiv | 采样率与参考时钟的关系；也可选外部直供时钟 |
| Block 级（数字通路） | Data Type（Real / IQ）、Decimation（Interpolation）Mode、Mixer Type（Fine/Coarse/Bypass/…）、NCO 频率、FIFO Enable、Data Width | 决定数据面格式与带宽 |
| 模拟通路 | 输入/输出模式（R2C、C2R、C2C、R2R）、DAC 输出电流、InvSincFIR | |
| 可选端口/功能 | MTS（SYSREF）、TDD、中断、状态 | 用不到就别开，容易漏约束 |

生成后，IP 会把默认配置导出成 **`xrfdc_g.c` 里的 `XRFdc_Config` 配置表**，驱动初始化时直接读它 —— 所以 **Vivado 里的设置就是上电后的初始状态**，运行期只需要改"会变的那几个值"。

## 4 第二步：驱动 API（PG269 附录 C）

### 4.1 驱动文件结构

| 文件 | 职责 |
| --- | --- |
| `xrfdc.c` / `xrfdc.h` | 主 API 实现与原型、所有结构体定义 |
| `xrfdc_sinit.c` | 初始化（`XRFdc_LookupConfig` 等） |
| `xrfdc_mts.c` | 多 tile/多器件同步（MTS） |
| `xrfdc_mixer.c` | 混频器 / NCO |
| `xrfdc_clock.c` | 时钟与 PLL |
| `xrfdc_mb.c` | 多带（multi-band） |
| `xrfdc_ap.c` / `xrfdc_dp.c` | 模拟通路 / 数字通路 |
| `xrfdc_intr.c` | 中断与错误处理 |
| `xrfdc_hw.h` | 寄存器映射与掩码 |

本地源码（可直接对着读）：`/home/congqiang/work/repo/embeddedsw/XilinxProcessorIPLib/drivers/rfdc/src/`

### 4.2 初始化流程

```c
XRFdc RFdcInst;
XRFdc_Config *CfgPtr = XRFdc_LookupConfig(DeviceId);  /* Linux 下用 XRFdc_RegisterMetal() */
XRFdc_CfgInitialize(&RFdcInst, CfgPtr);              /* 必须先调用，之后才能用其它 API */

/* 需要时手动控制某个 tile 上电/下电 */
XRFdc_StartUp(&RFdcInst, XRFDC_ADC_TILE, 0);
XRFdc_Shutdown(&RFdcInst, XRFDC_ADC_TILE, 0);
```

要点：所有 API 的第一个参数都是 `InstancePtr`；`XRFdc_CfgInitialize` 之前调用任何其它 API 都是未定义行为。

### 4.3 API 分类速查

| 类别 | 代表函数 | 说明 |
| --- | --- | --- |
| 初始化 / 上下电 | `XRFdc_LookupConfig`、`XRFdc_CfgInitialize`、`XRFdc_RegisterMetal`、`XRFdc_StartUp`、`XRFdc_Shutdown`、`XRFdc_CustomStartUp`、`XRFdc_Reset` | 上电状态机多数情况自动完成 |
| 状态查询 | `XRFdc_GetIPStatus`、`XRFdc_GetBlockStatus`、`XRFdc_GetFIFOStatus`、`XRFdc_DumpRegs` | 排障第一步；`DumpRegs` 打印寄存器偏移与内容 |
| 混频器 / NCO | `XRFdc_SetMixerSettings`、`XRFdc_GetMixerSettings`、`XRFdc_ResetNCOPhase`、`XRFdc_UpdateEvent` | 运行期改频的主要手段 |
| 抽取 / 内插 | `XRFdc_SetDecimationFactor`、`XRFdc_GetDecimationFactor`、`XRFdc_SetInterpolationFactor`、`XRFdc_SetDecimationFactorObs` | 可用因子：OFF/1/2/3/4/5/6/8/10/12/16（**20/24/40 仅 Gen3/DFE**） |
| Nyquist 区 | `XRFdc_SetNyquistZone`、`XRFdc_GetNyquistZone` | 取值 1=奇数区（Odd）、2=偶数区（Even） |
| 校准 / QMC | `XRFdc_SetCalibrationMode`、`XRFdc_SetCalFreeze`、`XRFdc_SetCalCoefficients`、`XRFdc_DisableCoefficientsOverride`、`XRFdc_SetQMCSettings` | 交调/增益失配校正；调试时可冻结校准 |
| 延迟 | `XRFdc_SetCoarseDelaySettings`、`XRFdc_GetCoarseDelaySettings` | 通道间粗对齐（波束/多通道相位） |
| 阈值 / 检波 | `XRFdc_SetThresholdSettings`、`XRFdc_SetThresholdClrMode`、`XRFdc_ThresholdStickyClear`、`XRFdc_SetSignalDetector`（Gen3/DFE） | 信号检测与超阈值中断 |
| 模拟通路 | `XRFdc_SetDSA`（Gen3/DFE 步进衰减）、`XRFdc_SetDACVOP`、`XRFdc_SetDACCompMode`、`XRFdc_GetOutputCurr`、`XRFdc_SetInvSincFIR`、`XRFdc_SetDACDataScaler` | 增益/电流/sinc 校正 |
| 时钟 / PLL | `XRFdc_DynamicPLLConfig`、`XRFdc_GetClockSource`、`XRFdc_GetPLLConfig`、`XRFdc_GetPLLLockStatus`、`XRFdc_SetClkDistribution`（Gen3/DFE） | 运行期改采样率走这里 |
| 多 tile 同步 | `XRFdc_MultiConverter_Init`、`XRFdc_MultiConverter_Sync`、`XRFdc_MTS_Sysref_Config` | 见第 6 节 |
| 多带 / 数据通路模式 | `XRFdc_MultiBand`、`XRFdc_SetDataPathMode`（Gen3/DFE） | 一通道多载波、RX/Obs 共享 |
| 中断 | `XRFdc_IntrEnable`、`XRFdc_IntrClr`、`XRFdc_GetIntrStatus`、`XRFdc_SetStatusHandler` | 阈值/溢出/FIFO 等事件 |

### 4.4 必须认识的几个结构体

```c
typedef struct {           /* XRFdc_Mixer_Settings */
    double Freq;           /* NCO 频率 */
    double PhaseOffset;    /* NCO 相位偏移 */
    u32 EventSource;       /* 事件源：立即/由 PL 事件触发 */
    u32 CoarseMixFreq;     /* 粗混频模式 */
    u32 MixerMode;         /* 混频器模式 */
    u8  FineMixerScale;    /* NCO 输出缩放，0/1/2 */
    u8  MixerType;         /* 精细/粗/旁路 */
} XRFdc_Mixer_Settings;

typedef struct {           /* XRFdc_MultiConverter_Sync_Config */
    u32 RefTile;           /* 参考 tile */
    u32 Tiles;             /* 待同步 tile 位掩码，如 0x3 = tile0+tile1 */
    int Target_Latency;    /* 确定性延迟目标；-1 表示只测量 */
    int Offset[4];         /* 返回：各 tile 偏移 */
    int Latency[4];        /* 返回：各 tile 延迟 */
    int Marker_Delay;
    int SysRef_Enable;
    XRFdc_MTS_DTC_Settings DTC_Set_PLL;   /* 数字延迟调节 */
    XRFdc_MTS_DTC_Settings DTC_Set_T1;
} XRFdc_MultiConverter_Sync_Config;
```

其它常用：`XRFdc_Config`、`XRFdc_ADCTile_Config` / `XRFdc_DACTile_Config`（含 `SamplingRate`、`RefClkFreq`、`FabClkFreq`、分频比）、`XRFdc_ADCBlock_DigitalDataPath_Config`（`DecimationMode`、`MixerInputDataType`、`DataWidth`、`FifoEnable`、`MixerType`、`NCOFreq`）、`XRFdc_Tile_Clock_Settings`、`XRFdc_Distribution_Settings`、`XRFdc_IPStatus` / `XRFdc_TileStatus`。

## 5 典型上电与配置序列

```c
/* 1. 时钟与采样率 */
XRFdc_DynamicPLLConfig(&RFdcInst, XRFDC_ADC_TILE, 0, XRFDC_INTERNAL_PLL_CLK, 245.76, 4915.2);
while (XRFdc_GetPLLLockStatus(&RFdcInst, XRFDC_ADC_TILE, 0) != XRFDC_PLL_LOCKED) { }
XRFdc_SetClkDistribution(&RFdcInst, &DistSettings);            /* Gen3/DFE：时钟分发 */

/* 2. 数字链路 */
XRFdc_SetDecimationFactor(&RFdcInst, 0, 0, XRFDC_INTERP_DECIM_8X);

/* 3. 频点规划：Nyquist 区 + NCO */
XRFdc_SetNyquistZone(&RFdcInst, XRFDC_ADC_TILE, 0, 0, 1);      /* 1=Odd(NZ1/3/5), 2=Even(NZ2/4) */
XRFdc_Mixer_Settings Mix = {0};
Mix.Freq = 3500.0; Mix.PhaseOffset = 0; Mix.MixerMode = XRFDC_MIXER_MODE_C2R;
Mix.MixerType = XRFDC_MIXER_TYPE_FINE; Mix.FineMixerScale = XRFDC_MIXER_SCALE_1P0;
XRFdc_SetMixerSettings(&RFdcInst, XRFDC_ADC_TILE, 0, 0, &Mix);
XRFdc_ResetNCOPhase(&RFdcInst, XRFDC_ADC_TILE, 0, 0);

/* 4. 校准（注意：这个 API 不带 Type 参数） */
XRFdc_SetCalibrationMode(&RFdcInst, 0, 0, XRFDC_CALIB_MODE_AUTO);

/* 5. 状态确认 */
XRFdc_IPStatus Status; XRFdc_GetIPStatus(&RFdcInst, &Status);
```

> 上面是"顺序示意"，具体参数名请以你树里的 `xrfdc.h` 与实际器件配置为准（宏名各版本略有差异）。

**运行期真正会变的通常只有**：NCO 频率/相位（`SetMixerSettings` + `ResetNCOPhase` / `UpdateEvent`）、增益（DSA）、切换抽取率（RX/Obs 共享）。

## 6 多 tile / 多器件同步（MTS）

多 tile 之间时钟独立，相位、FIFO 延迟不同，需要 MTS 才能对齐（多通道波束成形、多板级联必需）。

调用顺序：

```c
XRFdc_MultiConverter_Init(&SyncCfg, NULL, NULL, 0); /* 初始化同步配置（末参 = RefTile） */
SyncCfg.Tiles = 0x3;                               /* 要同步哪些 tile（位掩码） */
SyncCfg.Target_Latency = -1;                       /* 先测量 */
XRFdc_MTS_Sysref_Config(&RFdcInst, &DACSyncCfg, &ADCSyncCfg, 1);  /* 使能 SYSREF */
XRFdc_MultiConverter_Sync(&RFdcInst, XRFDC_DAC_TILE, &SyncCfg);   /* 读回 Latency[] */
/* 第二次运行前设确定性目标：实测值 + 余量（DAC 常数取 16；ADC 需为 FIFO 读字数×抽取因子的倍数） */
```

**SYSREF 的硬性要求**（不满足就同步不上）：

1. 高质量、低抖动、自由运行的连续时钟
2. 频率 = `GCD(DAC_fs/16, ADC_fs/16)` 的整数分频，且 **< 10 MHz**；同时必须是所有采样它的 PL 时钟的整数分频
3. 模拟 SYSREF 与 PL SYSREF 必须**同频同相**；PL 侧采样要满足建立/保持
4. MTS 过程期间 SYSREF 必须持续存在（完成后可关）
5. 若要跨器件同步 DUC/DDC 的 NCO 相位，模拟 SYSREF 需 DC 耦合且能产生单脉冲/多脉冲

示例：ADC 3.93216 GSPS、DAC 4.9152 GSPS → GCD(fs/16) = 61.44 MHz → 取 **7.68 MHz** 作为 SYSREF。

## 7 数据面：AXI4-Stream 怎么对上

- **流率 = 采样率 ÷ 抽取因子**（发射为 × 内插因子后）
- 接口数 × 位宽 × PL 时钟由 IP 配置决定；抽取/内插就是用来把 GSPS 数据流降到 PL 能跑的频率

| 文档示例 | 配置 | AXI4-Stream |
| --- | --- | --- |
| 单 RF-DAC | 4 GSPS，8× 内插，I/Q 同一接口 | 500 MHz |
| 单 RF-ADC | 2 GSPS，4× 抽取，I/Q 同一接口 | 500 MHz |
| 双 RF-DAC（实数据） | 4 GSPS，8× 内插 | 每路 250 MHz |

**ZCU670 TRD 实测参数**（UG1530，可直接对照你自己的工程）：DFE DUC/DDC 接口 **491.52 MSPS**（IBW），DPD 采样率 **983.04 MSPS**，载波级 **122.88 MSPS**，天线交织 2 → 聚合 **245.76 MSPS**；RF 时钟参考来自 Si5381 的 245.76 MHz PL_CLK 与 8A340001 的 122.88 MHz。

## 8 运行期注意事项与坑

1. **只走 API**：除已明确列出的状态/中断寄存器，直接写内部寄存器会破坏驱动状态一致性。
2. **重配 bitstream 的安全流程**（否则可能影响器件寿命）：静音模拟前端 → 对每个在用的 tile 调 `XRFdc_Shutdown()` → 加载新/旧 bitstream → IP 上电状态机自动按序恢复。
3. **TDD 模式（Gen3/DFE）**：两种用法——*power saving*（通道独立上下电，交织校准自动处理）与 *RX/Obs sharing*（同一 RF-ADC 在不同时隙以两种抽取率工作），都由 PL 引脚控制。
4. **NCO 与 Nyquist 区配合**：NCO 物理范围只有 ±Fs/2；信号在子采样区（Fc > Fs/2）时，GUI/API 会按采样理论把 10 GHz 以内的设定值自动换算成等效 NCO。**为避免频谱倒置**：下变频时偶 Nyquist 区用正频、奇 Nyquist 区用负频；上变频反过来。
5. **抽取因子随代际不同**：20/24/40 只在 Gen3/DFE 上可用。
6. **时钟**：AXI4-Stream 时钟必须由 PL 侧的 PL_CLK 输入产生，不要用 IP 自己的输出时钟去驱动 AXI 流接口（MTS 场景尤其重要）。

## 9 在 ZCU670 / Luxshare N78 项目里怎么落地

| 事项 | 情况 |
| --- | --- |
| 软件栈 | PetaLinux（linux-xlnx）+ **libmetal**；低层用 UIO 与 `/dev/mem`，`devmem` 工具可直接看未加驱动的空间 |
| 驱动来源 | `embeddedsw/XilinxProcessorIPLib/drivers/`：`rfdc`、`dfemix`（DUC/DDC+混频）、`dfeccf`（通道滤波）、`dfeequ`、`dfeofdm`、`dfeprach` |
| 本地路径 | `/home/congqiang/work/repo/embeddedsw/XilinxProcessorIPLib/drivers/{rfdc,dfemix,dfeccf,dfeequ,dfeofdm,dfeprach}` |
| 时钟链 | 8A340001 SMU（PTP 同步）+ Si5381；用 `XRFdc_SetClkDistribution()` 设分发（UG1530 §Clock） |
| 数据链路 | RFDC（AXI4-Stream）→ dfemix → dfeccf → dfeofdm / dfeprach → eCPRI（PG370） |
| 相关笔记 | [[资源-ZCU670文档索引]]、[[ZCU670-PL-PS-参数]]、[[概念-射频采样率-RFSoC与AD9361]]、[[概念-物理层射频驱动全景]] |

## 10 查阅顺序建议

文档本体（已归档）：[[PG269_RF-Data-Converter_v2.6.pdf]]、[[UG1530_RFSoC-DFE-TRD_UserGuide_v2.1.pdf]]、[[PG393_RFSoC-DFE-DUC-DDC-Mixer_v2.0.pdf]]、[[PG395_RFSoC-DFE-Channel-Filter.pdf]]、[[PG390_RFSoC-DFE-FFT_v1.0.pdf]]、[[PG392_RFSoC-DFE-Resampler_v1.0.pdf]]、[[PG370_ORAN-Radio-Interface.pdf]]

1. PG269 **第 2 章**：搞清 tile/block 与数据通路结构
2. PG269 **第 4 章**：时钟、上电序列、TDD、MTS、AXI4-Stream 时序（做硬件设计必读）
3. PG269 **附录 C**：API 逐个查（配合本地 `xrfdc.h` 看结构体字段最准）
4. UG1530 **第 4 章**：看 TRD 怎么把这套东西跑起来（含设备树、时钟、DFE 串联）
5. PG393 / PG395 / PG390 / PG392：DFE 硬核 IP 的参数与接口

## 待补

- 对着本地 `xrfdc.c` 走一遍 `XRFdc_CfgInitialize` / `XRFdc_StartUp` / `XRFdc_MultiConverter_Sync` 的实现路径
- 把 ZCU670 TRD 里 RFDC 的实际配置（采样率、抽取、Nyquist 区、NCO）抄成一张对照表
- 在板子上验证：改 NCO 频率 → 用频谱仪/RF Analyzer（PG269 附录 D）看实际搬移
