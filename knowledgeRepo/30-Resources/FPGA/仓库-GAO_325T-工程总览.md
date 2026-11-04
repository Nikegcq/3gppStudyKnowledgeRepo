---
type: resource
tags: [FPGA, Vivado, Kintex-7, 工程地图, GAO_325T, 多卡采集]
created: 2026-09-30
updated: 2026-09-30
status: active
source: prj_coloturm_325t.zip / GAO_325T.zip
repo: C:\Users\Admin\work\prj_colotrum
board: Kintex-7 xc7k325tffg900-2
---

# 仓库：GAO_325T 工程总览

## 一句话总结

`GAO_325T` 是跑在 **Kintex-7 325T** 上的**多卡 ADC 采集 + 实时处理 + 以太网/Aurora 传输**工程：主卡对外 UDP，从卡经 Aurora 回传数据；FPGA 侧用 MicroBlaze 写寄存器控制 PL，数据侧含触发、基线、小波降噪与多卡组包。版本标记 `FPGA_VERSION_A = 20250903`。

系统级理解见 [[仓库-GAO_325T-系统架构与数据通路]]，框图见 [[图-GAO_325T-多卡采集系统框图.excalidraw]]。

---

## 1. 器件与工具

| 项 | 值 |
| --- | --- |
| 器件 | `xc7k325tffg900-2`（Kintex-7 325T） |
| 工具 | Vivado 2023.1（工程内部分注释仍见 2018.2 痕迹） |
| 软件 | Vitis / MicroBlaze + RT-Thread 4.0.2 + bootloader(SREC) |
| 配置 | SPI x4，`CONFIG_VOLTAGE 3.3` |

## 2. 本机路径（Windows）

| 内容 | 路径 |
| --- | --- |
| **完整 Vivado 工程（含全部 RTL）** | `C:\Users\Admin\work\prj_colotrum\prj_coloturm_325t.zip` |
| 精简包（多为 IP/缓存） | `...\GAO_325T.zip` |
| 已解出用户 RTL | `...\_prj_full\prj_coloturm_325t\GAO_325T.srcs\` |
| 软件 | `...\vitis_export_archive.ide\`、`base_soc\` |
| 手册/资料 | `C:\Users\Admin\work\fpga\`（正点原子等） |

> Linux 侧原始路径形态为 `.../prj_colotrum/prj_coloturm_325t/GAO_325T.srcs`，与 zip 内结构一致。

## 3. 目录地图（`GAO_325T.srcs`）

```text
GAO_325T.srcs/
├── constrs_1/new/pins.xdc          # 管脚 / IOSTANDARD
├── sources_1/
│   ├── new/
│   │   ├── Top.v                   # 顶层（约 756 行）—— 入口
│   │   └── axi_lite2user.vhd
│   ├── imports/
│   │   ├── hdl/MB_Ctrl_wrapper.v
│   │   └── src/
│   │       ├── user_regs.v         # 64×32bit 软件寄存器窗
│   │       ├── user_gpio.v / sync_reset.v
│   │       ├── data_process_top.v  # 采集处理总装
│   │       ├── eth_top.v           # UDP/ARP/RGMII
│   │       ├── aurora_top.v        # GTX / Aurora
│   │       ├── LMK04828_*.v
│   │       ├── src_data_process/   # ADC/触发/DWT/降噪/成包
│   │       ├── src_eth/
│   │       └── src_gtx/
│   ├── bd/MB_Ctrl/MB_Ctrl.bd       # MicroBlaze SoC
│   └── ip/                         # FIR/FIFO/ILA 等 IP
└── sim_1/new/tb_aurora_recv_mux.v
```

**学习入口顺序**：`Top.v` → `user_regs.v` → `data_process_top.v` → `pkg_data_to_eth.v` / `aurora_recv_mux.v` → `src_data_process/*`。

## 4. 五大子系统（速查）

| 子系统 | 作用 | 主要文件 |
| --- | --- | --- |
| 控制面 | MB 读写 64 寄存器，配置触发/网络/主从 | `MB_Ctrl.bd`、`user_regs.v` |
| 数据面 | ADC→滤波→触发→成包 | `data_process_top`、`src_data_process/*` |
| 以太网 | 对上位机 UDP/ARP | `eth_top`、`src_eth/*` |
| Aurora | 板间 64b/66b，多从卡汇聚 | `aurora_top`、`aurora_recv_mux` |
| 时钟/同步 | LMK04828、主从时钟选择 | `LMK04828_*`、`user_gpio` |

## 5. 管脚规模（`pins.xdc`）

- IOSTANDARD：LVDS_25 ×156（ADC）、LVCMOS33 ×93、LVCMOS18 ×18（以太网）
- 接口：系统差分时钟、DDR3、QSPI Flash、RGMII、2×LMK04828 SPI、9 组 ADC SPI、ADC LVDS、DAC（AD5674/AD5681）SPI、Aurora GT、UART、`fb_*` 背板同步

## 6. `user_regs` 寄存器分组（索引 = slv_reg[n]）

| 索引 | 功能 |
| --- | --- |
| 0–3 | DMA 控制 / 状态 |
| 4–7 | GPIO |
| 8–18 | ADC 控制、触发、数据配置、幅度阈值 |
| 19–26 | Bias / 基线 |
| 27–36 | 后处理、DAC、包长 / 包间隔 |
| 37–50 | 降噪参数（ratio / threshold / offset…） |
| 51–61 | 以太网 MAC/IP/端口/发包 |
| 62–63 | Aurora channel / lane 状态 |

主从关键位（`adc_post1.v` / `post_reg_control`）：

- `[31]` `card_master`：是否主卡
- `[2:0]` `card_id`：卡号
- `[8:3]` `card_mask_used`：使用的从卡掩码

## 7. 软件侧

| 部分 | 说明 |
| --- | --- |
| `bootloader` | SREC 从 QSPI Flash 加载应用 |
| `rtthread_mb` | RT-Thread 移植（application / cmd / drivers） |
| `code/new_dqspi_flash.c` | Quad-SPI Flash 驱动 |
| 文档 | `pg153-axi-quad-spi.pdf`、Flash 规格书、Infineon SLLD |

## 相关

- [[仓库-GAO_325T-系统架构与数据通路]]
- [[图-GAO_325T-多卡采集系统框图.excalidraw]]
- [[计划-FPGA学习-GAO多卡采集工程]]
- [[MOC-FPGA]]
