---
type: project
tags: [项目, BOM, FPGA, colotrum, GAO_325T, CC328, Aurora]
created: 2026-10-19
updated: 2026-10-19
status: active
source: 90-Attachments/GAO_325T/CC328-7K325T-V1P0-KAILE.pdf
---

# 项目：colotrum BOM 与副板接口清单

本文整理 `CC328-7K325T V1.0` 板卡的 BOM 和副板连接关系。原始 PDF 没有独立 BOM 页，以下内容从原理图页 1–39 抽取；`DNI`、`NC`、`0R(NC)` 需要按实际装配变体筛选。

关键结论：

- 原理图页 3–4 画有 **2 颗 MT41K256M16TW-107IT**，但当前工程 RTL/软件**没有例化或使用 DDR**；它不属于当前项目的工作内容，也不是副板接口。实际板卡是否贴装以实物为准。
- 副板高速链路是 **Aurora 64b/66b/GTX**，走 P1/P3 的 `PA/PB/PC/PD` 差分对。
- 每个副板槽位的信号线为 **8 根**：Aurora 4 根 + 低速控制/时钟或 SGMII 4 根。
- 代码按 **11 个从卡**组织，使用 12 条 GT lane 中的 11 条，lane0 保留。

原始资料：[[CC328-7K325T-V1P0-KAILE.pdf|打开 PDF]]

表格附件：[[BOM-CC328-7K325T.csv|打开 CSV 版 BOM]]

## 一、核心 IC BOM

| 类别 | 数量 | 型号 | 位号/页码 | 说明 |
| --- | ---: | --- | --- | --- |
| FPGA | 1 | XC7K325TFFG900 | U41，p5–p22 | Kintex-7 325T，FFG900 |
| DDR3（板载/未使用） | 2 | MT41K256M16TW-107IT | p3–p4 | 原理图有器件，当前 RTL/软件未使用 |
| QSPI NOR Flash | 1 | S25FL256SAGMFI00 | U29，p19 | 256Mb FPGA 配置 Flash |
| 时钟抖动衰减器 | 2 | LMK04828BISQ | p23–p24 | 双 PLL、多路时钟输出 |
| 时钟缓冲器 | 1 | Si53306-B-GM | U50，p30 | 4 路差分时钟扇出 |
| 千兆以太网 PHY | 1 | RTL8211F-CG | U34，p29 | 原理图符号名 CX8211 |
| USB-UART | 1 | CP2102 | U15，p30 | USB Type-C 调试串口 |
| I2C EEPROM | 1 | M24C08-WDW6TP | U86，p39 | 8Kb EEPROM |
| 16 位 ADC | 8 | ADS5562IRGZT | U24、U11、U10、U9、U8、U7、U6、U5 | ADC1–ADC8 |
| 14 位 ADC | 1 | ADS6243IRGZT | U16，p27 | ADC9/ADC10 双通道 |
| ADC 差分驱动/滤波 | 10 | LTC6601IUF-1#PBF | U78、U76、U77、U79–U85 | 每个模拟通道一颗 |
| ADC 低噪声 LDO | 9 | TPS7A8300RGR | U12、U4、U23、U22、U21、U20、U19、U18、U17 | 3.3V @3A |
| 16 通道 DAC | 1 | AD5674 | U3，p28 | 多通道增益/偏置控制 |
| 单通道 DAC | 1 | AD5681R | U2，p28 | 辅助 DAC |
| 4 位电平转换 | 10 | SN74AVC4T774RSVR | p1、p2、p30 | FPGA 与外部接口电平转换 |
| 1 位电平转换 | 2 | SN74AVC1T45DCKR | p2 | 单比特双向电平转换 |
| 单路缓冲器 | 5 | SN74LVC1G125DBVR | p1 | 时钟/控制缓冲 |
| 8 位总线收发 | 2 | RS8T245YTSS24 | p1、p28 | 电平/总线隔离 |
| ESD 保护阵列 | 12 | SP3051-04HTG | p1、p2、p30 | 4 通道 ESD |
| ESD 保护阵列 | 1 | SP0503BAHTG | U75，p30 | 3 通道 ESD |
| 电源监控/复位 | 1 | ADM706RARZ | p2 | 复位与电源监控 |
| 模拟开关 | 1 | TD-11XA | SW1，p2 | 调试/配置切换 |
| N-MOS | 3 | 2N7002 | Q1–Q3，p38 | LED 驱动 |
| 指示灯 | 1 | LED0603-GRN | D4，p38 | 绿色 LED |
| 双色/特殊 LED | 1 | 553-0122F | D1，p38 | 电源/状态指示 |
| 25MHz 晶振 | 1 | 25MHz | Y3，p24 | 时钟芯片参考 |
| 25MHz 晶振 | 1 | 25MHz | X1，p29 | RTL8211F PHY 参考 |
| 125MHz LVPECL 振荡器 | 1 | 125MHz/LVPECL/3225/3.3V | p30 | SFP+ 参考时钟 |
| 100MHz LVPECL 振荡器 | 1 | 100MHz/LVPECL/3225/3.3V | p30 | DNI，未装配 |
| 10MHz 外部参考 | 1 | SMA-KWHD | J1，p24 | DNI |

## 二、连接器与副板接口

| 数量 | 型号/类型 | 位号/页码 | 用途 |
| ---: | --- | --- | --- |
| 3 | 1410189-3 | P0、P1、P3，p25 | 高速背板连接器 |
| 2 | 36500200 | J2、J3，p28 | 36 位排针/连接器 |
| 2 | SM12B-NSHSS-TB | J4、J5，p28 | 12 位连接器 |
| 1 | 10226-1210PE | p28 | 10 位排针/连接器 |
| 1 | 721-81-025W00 | J10，p28 | 12V 风扇接口 |
| 1 | RJ45 带网络变压器 | J7，p29 | 千兆以太网口 |
| 1 | USB Type-C | J6，p30 | USB 调试/供电 |
| 1 | SFP+ Cage | J8，p30 | SFP+ 笼子 |
| 1 | SFP+ Connector | J9，p30 | SFP+ 连接器 |
| 1 | 2-pin 13V 输出 | p28 | 给模拟板供电 |
| 1 | SMA | J1，p24 | 10MHz 外部参考，DNI |

### P0/P1/P3 的角色

| 连接器 | 主要信号 | 连接对象 |
| --- | --- | --- |
| P0 | `+12V_AUX`、`-12V_AUX`、`3.3V_AUX`、`SYSRESET*`、`NVMRO`、`TRIG`、`TMS/TCK/TDI/TDO`、`REF_CLK±`、`SGMII_BUS±`、`Board_SYNC_IO0..5`、`SLOT_NUMBER`、`FPGA_SPIO_3V3_1/2` | 主控/背板公共控制、时钟、同步、调试 |
| P1 | `S0..S5_CLK_FROM_MASTER_P/N`、`S0..S5_FPGA_GPIO_3V3_1/2`，以及 `PA/PB/PC/PD` 高速差分对 | 从卡槽 S0–S5 |
| P3 | `S6..S11_SGMII_MASTER_TXP/TXN/RXP/RXN`，以及 `PA/PB/PC/PD` 高速差分对 | 从卡槽 S6–S11 |

## 三、每个副板有多少根信号线

按原理图页 25 的槽位分组统计，每个副板槽位为 **8 根信号线**：

```text
每个从卡槽：
  Aurora 高速数据：TXP/TXN + RXP/RXN       = 4 根（2 对差分）
  低速控制：
    S0–S5：CLK_FROM_MASTER_P/N + 2×GPIO   = 4 根（1 对差分 + 2 根单端）
    S6–S11：SGMII_MASTER_TXP/TXN/RXP/RXN  = 4 根（2 对差分）
  ------------------------------------------------------------
  合计：8 根信号线
```

- 只算 Aurora 数据线：每个副板 **4 根**，即 1 条 lane。
- 算上该槽位的时钟/控制或 SGMII：每个副板 **8 根信号线**。
- 电源、地、背板公共的 `Board_SYNC`、`TRIG`、`SYSRESET`、JTAG 等不在上述 8 根里。

## 四、Aurora lane 与从卡槽位

`Top.v` 参数：

```verilog
parameter GT_CHANNEL_N = 3;
parameter GT_LANE_N    = 4;
parameter SLAVE_CARD_N = 11;
```

即 3 个 GT quad × 4 lane = 12 条 GT lane。`aurora_gtx_mux.v` 中每个从卡只映射一条 lane。按 lane0 保留、S0 为保留槽位理解：

| 从卡槽位 | GT lane | 所属 GTX quad |
| --- | ---: | --- |
| S0 | lane 0 | GTX116 lane0，保留/未使用 |
| S1 | lane 5 | GTX117 lane1 |
| S2 | lane 4 | GTX117 lane0 |
| S3 | lane 3 | GTX116 lane3 |
| S4 | lane 2 | GTX116 lane2 |
| S5 | lane 1 | GTX116 lane1 |
| S6 | lane 6 | GTX117 lane2 |
| S7 | lane 7 | GTX117 lane3 |
| S8 | lane 8 | GTX118 lane0 |
| S9 | lane 9 | GTX118 lane1 |
| S10 | lane 10 | GTX118 lane2 |
| S11 | lane 11 | GTX118 lane3 |

注意：这张表是从 `aurora_gtx_mux.v` 的 `card_*_lane_id` 反推的；如果背板丝印或槽位号与代码里的 `card_id` 有偏移，需要以实际背板定义再核对一次。

## 五、无源器件与其他

按原理图位号粗略统计：

| 类别 | 数量（约） | 主要规格 |
| --- | ---: | --- |
| 电容 C | 334 | 0.1uF/100nF、1uF、10uF、47uF、22uF、100pF、1500pF、10pF、33pF、2.2nF、10nF |
| 电阻 R | 293 | 0R、10K、4.7K、22R、33R、100R、120R、200R 0.1%、820R、1K、330R、24.7K |
| 磁珠 FB | 8 | BLM18AG121SN1D、BLM18KG121TN1、HZ08 系列 |
| 馈通滤波 | 10 | NFM18PC225B1A3D，2.2uF/10V/4A |
| 电感 L | 1 | L150/24N，约 24nH |
| 保险丝 F | 4 | F1、F2、F9、F16 |
| TVS/PTC | 2 | T52C13、ASMD0805-100-16V |
| 测试点 TP | 9 | TP1–TP9 |
| 安装孔 MH | 14 | MECH_HOLE_126 |
| 二极管/LED | 约 10 | 电源、状态、调试指示 |

## 六、注意事项

1. 原 PDF 没有独立 BOM 页，所有页标题栏都写 `Sheet 1 of 24`，文本层中存在位号重复/错位。
2. 表中 `DNI`、`NC`、`0R(NC)` 很多，实际贴片 BOM 必须先确定装配变体。
3. BOM 没有完整的封装、容差、耐压、温漂、替代料信息，不能直接用于采购和贴片。
4. 正式 BOM 应从原始 Altium/EDA 工程导出 `Comment / Designator / Footprint / Quantity / DNP / MPN`。
5. 原理图页 3–4 有 DDR3 器件和网络，但当前工程代码没有例化/使用 DDR；简历和项目描述中不要写 DDR 相关工作量，除非后续确实接入了 DDR 控制器。

## 关联

- [[计划-FPGA学习-GAO多卡采集工程]]
- [[仓库-GAO_325T-工程总览]]
- [[仓库-GAO_325T-系统架构与数据通路]]
- [[图-GAO_325T-工程结构与远程升级-drawio]]（远程升级部分为工程资料，非本人工作）
- [[MOC-FPGA]]
