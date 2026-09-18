---
type: resource
tags: [Linux, 嵌入式, 驱动开发, AD9361, IIO, PlutoSDR, SPI, DMA, 教学]
created: 2026-09-14
updated: 2026-09-16
last_session: 2026-09-16 增加 TX/RX 数据流 Excalidraw 图
status: active
source: plutosdr-fw/linux @ f3da30df + 实板 dump kernel-lab/iio-dump/20260914-230339
repo: /home/congqiang/work/repo/plutosdr-fw
board: PlutoSDR Rev.C (Z7010/AD9363) root@192.168.2.1
---

# 教学：AD9361 驱动从零到通（结合实板）

## 一句话总结

AD9361 驱动不是「一个 .c 文件从头跑到尾」，而是**两套驱动 + 一个握手结构**协作：SPI 侧 `ad9361.c` 负责配置射频芯片（控制面），platform 侧 `cf_axi_adc_core.c` 负责把 IQ 样本搬进内存（数据面），中间靠设备树属性 `spibus-connected` 和 `struct axiadc_converter` 连起来。用户态最终看到两个（其实是三个）IIO 设备：`ad9361-phy` 管调参，`cf-ad9361-lpc` / `cf-ad9361-dds-core-lpc` 管收发数。

本文按「零基础 → 黑盒观察 → 设备模型 → probe 拆解 → 数据流 → 深挖」推进；每一步尽量对应**你板子上的真实输出**（dump 路径：`kernel-lab/iio-dump/20260914-230339/`）。

---

## 第 0 层：先建立地图（不知道 Linux 驱动也能读）

### 0.1 硬件上有什么

```text
                    天线
                      │
              ┌───────▼────────┐
              │    AD9363      │  射频收发芯片（ADI）
              │  70MHz–6GHz    │  内部：混频、滤波、增益、PLL、ADC/DAC
              └───┬───────┬────┘
        SPI 寄存器│       │数字 IQ（CMOS/LVDS）
                  │       │
         ┌────────▼──┐ ┌──▼──────────────────┐
         │  Zynq PS  │ │  Zynq PL (FPGA)     │
         │  SPI 控制器│ │  axi_ad9361 接口核   │
         │  ARM Linux│ │  axi_dmac DMA 引擎   │
         └───────────┘ │  → DDR 内存          │
                       └─────────────────────┘
```

你的板子是 **PlutoSDR Rev.C**，芯片丝印是 AD9363，但驱动按 **ad9364（1R1T）模式**初始化——dmesg 第一行就写了：

```text
ad9361 spi0.0: ad9361_probe : enter (ad9364)
```

片内 TX/RX 硬件数据流（UG-570 模块级，可在 Excalidraw 中编辑）：

![[图-AD9361-TX-RX路径硬件模块.excalidraw]]

混频与镜像原理见 [[概念-Mixer变频与镜像频率]]（零中频：混频后是基带 LPF，不是 IF BPF）。

### 0.2 软件为什么要「两套驱动」

| 问题 | 谁负责 | 驱动文件 |
| --- | --- | --- |
| 频率设多少？增益多大？带宽多少？FDD 还是 TDD？ | 控制面 | `drivers/iio/adc/ad9361.c`（SPI 从设备） |
| 采样点怎么从 FPGA 搬到内存？用户怎么读走？ | 数据面 | `drivers/iio/adc/cf_axi_adc_core.c`（platform） |
| TX 侧样本怎么送出去？ | 数据面 | `drivers/iio/frequency/cf_axi_dds.c` |
| DMA 描述符与中断 | DMA 引擎 | `drivers/dma/dma-axi-dmac.c` |

**类比**：控制面像「空调遥控器」（调参数），数据面像「水管」（送冷气/送水）。遥控器和水管是两套系统，但必须对齐——温度设定和出风量要匹配。

### 0.3 用户态看到什么（先黑盒）

实板 `/sys/bus/iio/devices` 抓到 6 个 IIO 设备：

| 节点 | name | 角色 | 有 `/dev` 字符设备？ |
| --- | --- | --- | --- |
| `iio:device0` | `ad9361-phy` | **控制面**：频率/增益/带宽/ENSM | 无（不走 buffer） |
| `iio:device1` | `xadc` | Zynq 片内 ADC（温度/电压） | 有 |
| `iio:device2` | `one-bit-adc-dac` | 板级辅助 ADC/DAC | 无 |
| `iio:device3` | `cf-ad9361-dds-core-lpc` | **TX 数据面**（DDS/DAC） | 有 `/dev/iio:device3` |
| `iio:device4` | `cf-ad9361-lpc` | **RX 数据面**（ADC） | 有 `/dev/iio:device4` |
| `iio:device5` | `adi-iio-fakedev` | AXI TDD 核包装成 IIO | 无 |

**第一课**：`ad9361-phy` **没有** `/dev` 节点。它没有 `scan_elements`、不走 buffer，只提供 sysfs 属性让你读写参数。真正的「采样流」在 device3/device4 上。

你板上两条关键 dmesg，正好对应两条主线 probe 成功：

```text
ad9361 spi0.0: ad9361_probe : enter (ad9364)
ad9361 spi0.0: ad9361_probe : AD936x Rev 0 successfully initialized
cf_axi_dds 79024000.cf-ad9361-dds-core-lpc: ... probed DDS AD9364
cf_axi_adc 79020000.cf-ad9361-lpc: ADI AIM (10.03.) ... probed ADC AD9364 as MASTER
```

---

## 第 1 层：设备树 —— 内核怎么知道有这块芯片

### 1.1 控制面节点（SPI 从设备）

源码：`linux/arch/arm/boot/dts/zynq-pluto-sdr.dtsi` 里 `&spi0` 下：

```dts
adc0_ad9364: ad9361-phy@0 {
    compatible = "adi,ad9363a";          /* 决定匹配哪个驱动 */
    reg = <0>;                            /* SPI 片选 CS0 */
    spi-cpha;
    spi-max-frequency = <10000000>;       /* 10 MHz */
    clocks = <&ad9364_clkin 0>;           /* 40 MHz 参考时钟 */
    #clock-cells = <1>;                   /* 它自己也是时钟提供者 */
    adi,frequency-division-duplex-mode-enable;
    adi,rf-rx-bandwidth-hz = <18000000>;
    adi,rx-synthesizer-frequency-hz = /bits/ 64 <2400000000>;
    adi,tx-synthesizer-frequency-hz = /bits/ 64 <2450000000>;
    /* BBPLL     ADC        R2CLK     R1CLK    CLKRF    RSAMPL  */
    adi,rx-path-clock-frequencies = <983040000 245760000 ... 30720000>;
    ...几十个 adi,* 参数...
};
```

你板上 `/sys/firmware/devicetree/base/.../ad9361-phy@0/` 能看到这些属性（dump 文件 `09-device-tree.txt`）。

### 1.2 数据面节点（FPGA AXI 外设）

```dts
fpga_axi: fpga-axi@0 {
    compatible = "simple-bus";            /* 内核会递归创建子 platform 设备 */

    rx_dma: dma@7c400000 { ... };         /* AXI DMAC，RX */
    tx_dma: dma@7c420000 { ... };         /* AXI DMAC，TX */

    cf-ad9361-lpc@79020000 {
        compatible = "adi,axi-ad9361-6.00.a";
        reg = <0x79020000 0x6000>;        /* AXI 寄存器窗口 */
        dmas = <&rx_dma 0>;               /* 连到 RX DMA */
        dma-names = "rx";
        spibus-connected = <&adc0_ad9364>; /* ★ 握手指针：指向 SPI 侧 */
    };

    cf-ad9361-dds-core-lpc@79024000 {
        compatible = "adi,axi-ad9364-dds-6.00.a";
        clocks = <&adc0_ad9364 13>;       /* 索引 13 = TX_SAMPL_CLK */
        dmas = <&tx_dma 0>;
        dma-names = "tx";
    };
};
```

**必须记住的三个属性**：

1. `compatible` —— 总线匹配的钥匙
2. `spibus-connected` —— ADI 自定义，数据面靠它找到控制面
3. `dma-names` / `dmas` —— 内核通用，按名字申请 DMA 通道

### 1.3 实板地址对照

| 设备树节点                    | 物理地址       | 实板 sysfs 路径片段                                                |
| ------------------------ | ---------- | ------------------------------------------------------------ |
| `spi0`                   | `e0006000` | `.../e0006000.spi/spi0/spi0.0/iio:device0`                   |
| `cf-ad9361-lpc`          | `79020000` | `.../fpga-axi@0/79020000.cf-ad9361-lpc/iio:device4`          |
| `cf-ad9361-dds-core-lpc` | `79024000` | `.../fpga-axi@0/79024000.cf-ad9361-dds-core-lpc/iio:device3` |
| `rx_dma`                 | `7c400000` | `/proc/interrupts` 里 `7c400000.dma`                          |
| `tx_dma`                 | `7c420000` | `/proc/interrupts` 里 `7c420000.dma`                          |

---

## 第 2 层：Linux 设备模型 —— 从 dtb 到 probe

通用公式：

```text
设备树节点 ──populate──▶ device ──match──▶ driver ──call──▶ probe()
```

### 2.1 platform 设备（数据面）

内核启动时 `of_platform_default_populate_init()` 递归遍历 DT：

- `fpga-axi@0` 是 `simple-bus` → 递归进去
- `cf-ad9361-lpc@79020000` → 创建 `platform_device`
- 驱动 `axiadc_driver` 的 `.of_match_table` 里有 `"adi,axi-ad9361-6.00.a"` → 命中
- 调用 `axiadc_probe()`

### 2.2 SPI 设备（控制面）

SPI 控制器 probe 成功后 `spi_register_controller()` → `of_register_spi_devices()`：

- 取 `compatible = "adi,ad9363a"`，**去掉厂商前缀 `adi,`** → `modalias = "ad9363a"`
- `ad9361_driver` 只有 `.id_table`，没有 `.of_match_table`
- `ad9361_id[]` 里有 `{"ad9363a", ID_AD9363A}` → 命中
- 调用 `ad9361_probe()`

```c
/* ad9361.c:9661 */
static const struct spi_device_id ad9361_id[] = {
    {"ad9361",  ID_AD9361},   /* 2RX2TX */
    {"ad9364",  ID_AD9364},   /* 1RX1TX  ← 你板子实际走这条 */
    {"ad9361-2x", ID_AD9361_2},
    {"ad9363a", ID_AD9363A},  /* dtsi compatible 对应这条 */
    {}
};
```

> 注意：dtsi 写 `adi,ad9363a`，但 dmesg 显示 `enter (ad9364)`。驱动内部对 AD9363A 也会按 1R1T 处理（Pluto 只有一路 RX/TX 天线口）。`hw_model` 报 `Rev.C (Z7010-AD9364)`。

### 2.3 顺序问题与 EPROBE_DEFER

数据面 probe 需要控制面已经挂好 converter。若 SPI 侧还没 probe 完：

```c
/* cf_axi_adc_core.c axiadc_probe */
ret = bus_for_each_dev(&spi_bus_type, ..., axiadc_attach_spi_client);
if (ret == 0)
    return -EPROBE_DEFER;   /* 告诉内核：依赖没就绪，稍后重试 */
```

内核把设备放回 deferred 链表，等 SPI 驱动成功后再自动重试。你板上最终两条 dmesg 都出现了，说明握手成功。

---

## 第 3 层：控制面 probe 逐步拆解（`ad9361_probe`）

函数位置：`ad9361.c` 约 9501 行。按顺序理解每一步在干什么：

```text
ad9361_probe(spi)
 │
 ├─1. devm_clk_get()                 取 40MHz 参考时钟；拿不到 → EPROBE_DEFER
 ├─2. devm_iio_device_alloc()        分配 IIO 设备 + ad9361_rf_phy
 ├─3. ad9361_phy_parse_dt()          把几十个 adi,* 属性译成 platform_data
 ├─4. GPIO（reset/sync/cal-sw）      可选，硬复位等
 ├─5. ad9361_reset() + ad9361_spi_check()
 │      硬复位芯片 → SPI 读 PRODUCT_ID → 校验 0x08（AD9361）
 ├─6. register_clocks()              创建芯片内部时钟树并注册到内核
 ├─7. ad9361_setup()                 ★ 真正把参数写进芯片寄存器
 │      时钟链 / RF 端口 / LO 频率 / 增益表 / 滤波器校准 / ENSM
 ├─8. of_clk_add_provider()          把时钟树暴露给 DT（给 DDS 节点用）
 ├─9. devm_iio_device_register()     注册 IIO 设备 ad9361-phy
 ├─10. ad9361_register_axi_converter()  ★ 与数据面握手
 └─11. sysfs bin + debugfs           filter_fir_config / gain_table_config
```

### 3.1 实板上能看到的结果

`iio_info` 显示 `ad9361-phy` 有 **9 个 channel**、**19 个 device 属性**：

| Channel             | 含义          | 实板当前值                                              |
| ------------------- | ----------- | -------------------------------------------------- |
| `altvoltage0` RX_LO | 接收本振        | 2400000000 Hz（2.4 GHz）                             |
| `altvoltage1` TX_LO | 发射本振        | 2450000000 Hz                                      |
| `voltage0` (input)  | RX1         | sampling 30720000，gain_mode slow_attack，gain 71 dB |
| `voltage0` (output) | TX1         | hardwaregain -10 dB，rf_port A                      |
| `voltage2` (input)  | RX2（若 2R2T） | 有 raw/scale                                        |
| `temp0`             | 芯片温度        | 41228（0.001°C）                                     |

Device 属性：`ensm_mode = fdd`、`calib_mode = auto`、`filter_fir_config`、`gain_table_config`（Pluto 默认 gaintable 覆盖 1.3–4 GHz）。

这些值和 dtsi 的初始参数一致（2.4/2.45 GHz、18 MHz 带宽、30.72 Msps）。

### 3.2 SPI 寄存器访问的底层格式

驱动所有配置最终走 SPI：

```text
16-bit 命令字 + N 字节数据
  bit15    : 1=写, 0=读
  bit14:12 : 数据长度-1
  bit9:0   : 寄存器地址
```

- 读：`spi_write_then_read(spi, cmd, 2, rbuf, num)`
- 写：`spi_write_then_read(spi, cmd+data, num+2, NULL, 0)`

你板上 `e0006000.spi` 中断计数 5228（采集时刻），说明 SPI 通信一直在跑。

> 每个地址/bit 的含义见 [[资源-AD9361-寄存器文档]]（UG-570 + `ad9361.h`）。

### 3.3 时钟树 —— DT 时钟与芯片寄存器的转换层

`register_clocks()` 之后，`/proc/clk_summary` 能看到（你板上实测）：

```text
ad9364_ext_refclk          40 MHz          ← 晶振
  bb_refclk                40 MHz
    bbpll_clk             983.04 MHz       ← BBPLL
      adc_clk             245.76 MHz
        dac_clk           122.88 MHz
          t2_clk → t1_clk → clktf_clk → tx_sampl_clk  30.72 MHz
          r2_clk → r1_clk → clkrf_clk → rx_sampl_clk  30.72 MHz
  rx_refclk                80 MHz
    rx_rfpll              1200 MHz         ← RX LO 本振
  tx_refclk                80 MHz
    tx_rfpll              1225 MHz         ← TX LO 本振
```

关键理解：**每个 `clk_ops` 回调最终都会变成一次 SPI 寄存器写**。用户态改 `sampling_frequency` → 内核 `clk_set_rate(rx_sampl_clk)` → 驱动重算整条时钟链 → SPI 写分频器。

---

## 第 4 层：握手结构 `axiadc_converter`（最容易迷路的地方）

### 4.1 它是什么

`struct axiadc_converter` 是控制面和数据面之间的**接口合同**，定义在 `cf_axi_adc.h`：

```c
struct axiadc_converter {
    struct chip_info *chip_info;   /* 通道数、位宽、scan_mask */
    int (*write_raw)(...);         /* 读写 IIO 属性时回调到 ad9361 */
    int (*read_raw)(...);
    int (*post_setup)(...);        /* 数据面 probe 后配置 HDL */
    struct clk *clk;               /* 采样时钟 */
    unsigned long adc_clk;
    void *phy;                     /* 指回 ad9361_rf_phy */
    ...
};
```

### 4.2 谁填、谁取

**填**（控制面 `ad9361_conv.c`）：

```c
int ad9361_register_axi_converter(struct ad9361_rf_phy *phy)
{
    conv = devm_kzalloc(...);
    conv->chip_info = &axiadc_chip_info_tbl[ID_AD9361 或 ID_AD9364];
    conv->write_raw = ad9361_write_raw;
    conv->read_raw  = ad9361_read_raw;
    conv->post_setup = ad9361_post_setup;
    conv->clk = phy->clks[RX_SAMPL_CLK];
    spi_set_drvdata(spi, conv);   /* ★ 挂到 SPI 设备上 */
}
```

**取**（数据面 `cf_axi_adc_core.c`）：

```c
/* spibus-connected → 找到 spi_device → spi_get_drvdata() */
conv = to_converter(st->dev_spi);
```

### 4.3 为什么这样设计

控制面和数据面是两个独立的 Linux driver，不能直接互相 `extern` 调用。通过：

1. 设备树 `spibus-connected` 建立拓扑关系
2. `spi_set_drvdata` / `spi_get_drvdata` 传递对象
3. `device_link_add` 锁定 probe/卸载/电源管理顺序

解耦后，同一套 `cf_axi_adc` 驱动可以接 AD9361、AD9364、AD9371、ADRV9009……只要对方填好 converter。

---

## 第 5 层：数据面 probe（`axiadc_probe`）

```text
axiadc_probe(pdev)
 │
 ├─1. of_parse_phandle("spibus-connected")   找 SPI 设备节点
 ├─2. bus_for_each_dev(...)                  找已 probe 的 spi_device
 │      找不到 → -EPROBE_DEFER
 ├─3. device_link_add()                      建立依赖链
 ├─4. devm_iio_device_alloc()                axiadc_state
 ├─5. ioremap(0x79020000, 0x6000)            映射 FPGA 寄存器
 ├─6. to_converter()                         ★ 取出握手对象
 ├─7. 复位 HDL 核（RSTN 寄存器三步）
 ├─8. 读版本号，校验 major
 ├─9. axiadc_channel_setup()                 拷贝 converter 里的通道表
 ├─10. conv->post_setup()                    ★ 控制面配置落到 HDL
 ├─11. axiadc_configure_ring_stream()        创建 DMA buffer
 └─12. devm_iio_device_register()            注册 cf-ad9361-lpc
```

### 5.1 post_setup 做了什么

`ad9361_post_setup()`（`ad9361_conv.c`）把 AD9361 的工作模式写进 **FPGA 接口核寄存器**：

- 1R1T / 2R2T（`R1_MODE`）
- I/Q 通道使能与格式
- DC 滤波、I/Q 校正系数
- 数字接口时序 tune（`ad9361_dig_tune`）

**这是控制面参数真正落到数据面硬件的时刻。**

### 5.2 实板数据面设备长什么样

`cf-ad9361-lpc`（device4，RX）：

```text
2 channels: voltage0 / voltage1
  format: le:S12/16>>0          ← 12-bit 有符号，16-bit 存储
  sampling_frequency: 30720000
buffer:
  direction = in
  length = 4096
  length_align_bytes = 8
  watermark = 2048
debug:
  pseudorandom_err_check       ← PN9 伪随机校验（数字接口质量）
  direct_reg_access            ← 可直接读写 AXI 寄存器
```

`cf-ad9361-dds-core-lpc`（device3，TX）：

```text
out_voltage0/1, format le:s16/16>>0
buffer direction = out
```

---

## 第 6 层：一次 RX 采样在内核里怎么流动

```text
用户态 iio_readdev / libiio
    │  写 sysfs: scan_elements/in_voltage0_en=1
    │            buffer/length=4096
    │            buffer/enable=1
    ▼
IIO buffer 框架
    │  axiadc_update_scan_mode() → 把 scan_mask 写进 HDL 通道控制寄存器
    ▼
axiadc_hw_submit_block()
    │  iio_dmaengine_buffer_submit_block()
    │    dmaengine_prep_slave_single(phys_addr, bytes, DMA_DEV_TO_MEM)
    │    dmaengine_submit() → dma_async_issue_pending()
    ▼
dma-axi-dmac.c
    │  描述符写入 DMAC 寄存器 @ 7c400000
    ▼
FPGA: axi_ad9361_adc_dma
    │  DMA_TYPE_SRC=2 (FIFO) → DMA_TYPE_DEST=0 (AXI-MM)
    │  样本：AD9361 → axi_ad9361 接口核 → DMA → DDR
    ▼
DMA 完成中断（GIC IRQ 89 = 7c400000.dma）
    │  IRQ handler → iio_dmaengine_buffer_block_done()
    ▼
用户态 read()/mmap()/poll() 返回 IQ 数据
```

你板上采集时刻 DMA 中断还是 0（buffer/enable=0），SPI 中断 5228——说明驱动已就绪，只是还没开始收数。跑一条：

```bash
iio_readdev -u local: -b 4096 cf-ad9361-lpc voltage0 | xxd | head
```

就能把 `/proc/interrupts` 里 `7c400000.dma` 打起来。

---

## 第 7 层：两个（三个）IIO 设备对照表

| 维度 | `ad9361-phy` | `cf-ad9361-lpc` | `cf-ad9361-dds-core-lpc` |
| --- | --- | --- | --- |
| 驱动 | `ad9361.c` | `cf_axi_adc_core.c` | `cf_axi_dds.c` |
| 总线 | SPI | platform | platform |
| 匹配 | `id_table` + modalias | `of_match_table` | `of_match_table` |
| IIO 模式 | `INDIO_DIRECT_MODE` | `INDIO_BUFFER_HARDWARE` | buffer + DDS |
| channels | 温度/LO/增益/带宽 | 2× I/Q ADC（S12/16） | 2× I/Q DAC（S16/16） |
| `/dev` 节点 | 无 | `/dev/iio:device4` | `/dev/iio:device3` |
| 用户态用途 | 调参 | 收数 | 发数 |

---

## 第 8 层：动手验证清单（对着你板子做）

```bash
# 1. 看设备名
cat /sys/bus/iio/devices/iio:device*/name

# 2. 看控制面关键参数
cat /sys/bus/iio/devices/iio:device0/in_voltage_sampling_frequency
cat /sys/bus/iio/devices/iio:device0/out_altvoltage0_frequency   # RX_LO
cat /sys/bus/iio/devices/iio:device0/ensm_mode

# 3. 看 debugfs 最终生效配置（171 条 adi,*）
ls /sys/kernel/debug/iio/iio:device0/

# 4. 直接读芯片寄存器
iio_reg ad9361-phy 0x00    # PRODUCT_ID，应为 0x08

# 5. 手动收一段数
echo 1 > /sys/bus/iio/devices/iio:device4/scan_elements/in_voltage0_en
echo 1 > /sys/bus/iio/devices/iio:device4/scan_elements/in_voltage1_en
echo 4096 > /sys/bus/iio/devices/iio:device4/buffer/length
echo 1 > /sys/bus/iio/devices/iio:device4/buffer/enable
iio_readdev -u local: -b 4096 cf-ad9361-lpc | xxd | head
echo 0 > /sys/bus/iio/devices/iio:device4/buffer/enable

# 6. 改频率看时钟树变化
echo 2000000000 > /sys/bus/iio/devices/iio:device0/out_altvoltage0_frequency
cat /proc/clk_summary | grep rfpll
```

---

## 第 9 层：源码阅读路线（按阶段推进）

| 阶段  | 目标   | 读什么                                                          | 验收                                  |
| --- | ---- | ------------------------------------------------------------ | ----------------------------------- |
| A   | 知道黑盒 | 本文 0–1 层 + 实板 `01/03` dump                                   | 能说出 6 个 IIO 设备各自干嘛                  |
| B   | 设备模型 | 本文 2 层；`drivers/of/platform.c`、`drivers/spi/spi.c` 匹配函数      | 能画 DT→device→match→probe            |
| C   | 控制面  | `ad9361_probe` 逐步；`ad9361_setup` 大纲                          | 能指出 setup 写了哪几类参数                   |
| D   | 握手   | `ad9361_register_axi_converter` + `axiadc_probe` 前半          | 能解释 spibus-connected + EPROBE_DEFER |
| E   | 数据面  | `axiadc_probe` 后半 + `axiadc_configure_ring_stream`           | 能画 buffer→dmaengine→IRQ 链           |
| F   | 动态验证 | QEMU+GDB 断 `ad9361_probe` / `axiadc_probe`；或板上 `iio_readdev` | 能在断点/中断计数里看到证据                      |

深读版（带精确行号、更细的调用链）见 [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]。

---

## 第 10 层：常见迷路点与勘误

1. **`ad9361-phy` 没有 `/dev` 节点** —— 它不是「没加载成功」，是 DIRECT_MODE 设备本来就不走 buffer。
2. **dtsi 写 ad9363a，dmesg 写 ad9364** —— 芯片 die 是 AD9363，驱动按 1R1T 配置，id_table 命中的是 modalias `ad9363a`，内部再按 Pluto 板型限成 1R1T。
3. **`ad9361_register_axi_converter` 不注册 IIO 设备** —— 名字容易误解，它只是填 converter 并 `spi_set_drvdata`。
4. **Rev 打印可能不准** —— `ad9361.c` 里 `rev = ret & REV_MASK` 用的是上一步返回值；你板上打 `Rev 0`，需对照主线确认。
5. **`lsmod` 为空** —— 这些驱动编译进内核（`=y`），不是模块，所以看不到。
6. **`CONFIG_CF_AXI_ADC` 不在 defconfig** —— 被 `CONFIG_ADMC=y` 间接 select。

---

## 第 11 层：sysfs 与 /dev（IIO 访问面）

| | `/sys` | `/dev` |
| --- | --- | --- |
| 是什么 | sysfs：内核对象的文件接口 | 设备节点（字符/块） |
| 核心动作 | `cat`/`echo` **查状态、改配置** | `open`/`read`/`write`/`mmap` **收发数据** |
| 驱动入口 | attribute show/store | `file_operations` |
| 类比 | 墙上仪表盘和旋钮 | 电话线（传业务数据） |

- `ad9361-phy`：只有 `/sys`（DIRECT_MODE，无 scan_elements/buffer）
- `cf-ad9361-lpc`：`/sys` 配旋钮 + `/dev/iio:device4` 传 IQ

**口诀：sysfs = 看和调；dev = 用和传。**

---

## 第 12 层：属性从哪来（不是设备树动态生成的）

`ad9361-phy` 的 185 条 sysfs 属性，源码里至少四处：

| 来源 | 源码位置（约） | 例子 |
| --- | --- | --- |
| ① `ad9361_phy_chan[]` 的 `info_mask` | `ad9361.c:8104` | `in_voltage0_hardwaregain`、`sampling_frequency` |
| ② chan 挂的 `ext_info[]` | `:7637/7844/7857` | `gain_control_mode`、`rssi`、LO 的 `frequency` |
| ③ `IIO_DEVICE_ATTR` + `ad9361_phy_attributes[]` | `:7217–7371` | `ensm_mode`、`calib_mode` |
| ④ bin 属性（probe 里单独 create） | `ad9361_probe` 末尾 | `filter_fir_config`、`gain_table_config` |
| ⑤ debugfs | `ad9361_register_debugfs` | 183 条 `adi,*` |

可选值字符串表：

- `ad9361_agc_modes[]`（7678）→ `gain_control_mode_available`
- `ad9361_rf_rx_port[]`（7720）→ `rf_port_select_available`
- `ad9361_ensm_states[]`（707）→ `ensm_mode_available`

设备树 `adi,*` **不直接变成 sysfs 文件**；`ad9361_phy_parse_dt()` 读进内存，setup 写进芯片；sysfs 当前值是驱动再读寄存器/时钟得到的。

### 设备量 vs channel 量

| | channel 量 | 设备量 |
| --- | --- | --- |
| 归属 | 某一路 | 整台设备 |
| 文件名 | 带 `in_voltage0_` 等前缀 | 无通道前缀 |
| 源码 | `chan[]` + `info_mask`/`ext_info` | `IIO_DEVICE_ATTR` 数组 |
| 例 | `in_voltage0_hardwaregain` | `ensm_mode` |

---

## 第 13 层：属性如何注册进 sysfs

驱动只填表，IIO 框架生成文件：

```text
ad9361_phy_chan[] / IIO_DEVICE_ATTR / ext_info
        ↓ probe
indio_dev->info = &ad9361_phy_info;   /* read_raw/write_raw + attrs */
indio_dev->channels = ad9361_phy_chan;
devm_iio_device_register()
        ↓ industrialio-core.c
iio_device_register_sysfs()   /* :1534 */
  ├─ 数 info->attrs，memcpy 进框架自建的大 attribute_group
  ├─ 遍历 channels，按 info_mask/ext_info 生成属性，追加
  └─ groups[] 记下
device_add()
  → sysfs_create_groups() → 长出 /sys/.../iio:device0/ 下全部文件
```

`info`（`iio_info`）是**能力表**（函数指针 + 属性组），`iio_dev` 是**设备实例**；`indio_dev->info = &ad9361_phy_info` 等同于字符设备的 `file->f_op = &my_fops`。

### 命名规则（industrialio-core.c）

四张表 + 拼接：

| 表 | 作用 | 例 |
| --- | --- | --- |
| `iio_direction[]` | in/out | `output=0` → `in` |
| `iio_chan_type_name_spec[]` | 物理量名 | `IIO_VOLTAGE` → `voltage` |
| `iio_chan_info_postfix[]` | info→后缀 | `HARDWAREGAIN` → `hardwaregain` |
| shared_by | 前缀要不要编号/类型 | SEPARATE → `in_voltage0_...` |

```text
BIT(IIO_CHAN_INFO_HARDWAREGAIN) + SEPARATE + indexed
  → in_voltage0_hardwaregain
BIT(IIO_CHAN_INFO_SAMP_FREQ) + SHARED_BY_TYPE
  → in_voltage_sampling_frequency（多路共享，同名 -EBUSY 跳过）
_available bit → 再生成 xxx_available
```

---

## 第 14 层：读写一条属性的调用链

以 `in_voltage0_hardwaregain` 为例：

```text
【读 cat】
sysfs → iio_read_channel_info()          industrialio-core.c:760
  → ad9361_phy_read_raw(chan, HARDWAREGAIN)   ad9361.c:7864
      → ad9361_get_rx_gain() → SPI

【写 echo】
sysfs → iio_write_channel_info()         industrialio-core.c:963
  → ad9361_phy_write_raw(chan, HARDWAREGAIN)  ad9361.c:7956
      → ad9361_set_rx_gain() → SPI
```

`read_raw/write_raw` 一个函数服务所有标准量，靠 mask 分支。  
扩展属性（`rssi`/`gain_control_mode`）走 ext_info 自己的 get/set；设备量走 `ad9361_phy_show/store`。

---

## 第 15 层：对象挂载关系（priv / parent / drvdata）

```text
iio_dev（内嵌 struct device）
  ├─ priv ──────────► ad9361_rf_phy     （iio_priv，与 iio_dev 连续分配）
  └─ dev.parent ────► &spi->dev         （父子设备，sysfs 可见）

spi_device spi0.0（内嵌 struct device）
  └─ dev.driver_data ─► axiadc_converter （只是指针，无 sysfs）
                          └─ phy ───────► 同一个 ad9361_rf_phy
```

| 机制 | 字段 | API | AD9361 放什么 |
| --- | --- | --- | --- |
| IIO 私有区 | `indio_dev->priv` | `iio_priv()` | `ad9361_rf_phy` |
| 总线私有指针 | `dev->driver_data` | `spi_set_drvdata` / `iio_device_set_drvdata` | `axiadc_converter` |
| 父子设备 | `dev->parent` | alloc 时传入 / `iio_device_set_parent` | `&spi->dev` |

关键 API：

```c
devm_iio_device_alloc(&spi->dev, sizeof(*phy));
/* 一次分配 iio_dev_opaque + priv 区；设 parent；devm 生命周期 */

phy = iio_priv(indio_dev);          /* 取 priv */

indio_dev->dev.parent = &spi->dev;  /* 明确父子 */

devm_iio_device_register(&spi->dev, indio_dev);  /* 出现 iio:device0 */

spi_set_drvdata(spi, conv);         /* converter 挂 SPI，不挂 phy */
```

**注意：`driver_data` 不在 `spi_device` 字段列表里，在内嵌的 `struct device` 里。**

lpc 取用：

```text
spibus-connected → 找到 spi0.0 → spi_get_drvdata → converter
```

不是「去 phy 结构体下面拿」。lpc 是独立 platform_device，对 spi0.0 只是引用/依赖，不是父子。

### 控制面是否同步到 FPGA

| 配置 | 落到哪 |
| --- | --- |
| LO/增益/带宽/端口 | 只芯片（SPI） |
| 采样率 | 芯片时钟树，节拍间接影响 FPGA |
| 1R1T、接口格式、IQ 校正 | 开机 `post_setup` + `dig_tune` **一次性**写 FPGA |
| scan enable | 数据面 `axiadc_update_scan_mode` 写 FPGA 通道 |

不是「每个寄存器都转发给 FPGA」。

### 为什么要连控制面和数据面

DMA 只会搬字节，不知道 IQ 格式、通道数、采样率。converter 提供 `chip_info`（12-bit、几路）、`post_setup`（写 HDL）、`clk`（采样时钟），保证样本语义正确。  
Pluto **不用 JESD**，走 CMOS/LVDS 并行口；`post_setup`/`dig_tune` 配的是并行接口，不是 JESD 链路。

---

## 第 16 层：initcall → probe 调用链（带位置）

```text
start_kernel                    init/main.c:936
  （ARM：head-common.S:121 b start_kernel；x86：head64.c:556）
rest_init                       :683
  kernel_init                   :1510
    do_initcalls                :1379

【DT populate】arch_initcall_sync
of_platform_default_populate_init     of/platform.c:517
  of_platform_populate                :465
    of_platform_bus_create            （simple-bus 递归）
      of_platform_device_create_pdata :167
        → cf-ad9361-lpc / dma 等 platform_device

【SPI 子设备】
spi_register_controller               spi.c:3183
  of_register_spi_devices             :3309/:2478
    of_register_spi_device            :2425
      of_modalias_node                of/base.c:1223
        "adi,ad9363a" → "ad9363a"
      spi_add_device → device_add

【匹配 probe】device_initcall / device_add
spi_match_device                      spi.c:375   （id_table 命中）
really_probe → call_driver_probe      dd.c:584/:553
  spi_probe                           spi.c:410
    ad9361_probe                      ad9361.c:9501

【数据面】
platform_match / platform_probe       platform.c:1331/:1375
  axiadc_probe                        cf_axi_adc_core.c:1061
```

驱动是内建（`module_spi_driver`），不是 insmod；`lsmod` 为空正常。

---

## 第 17 层：libiio（用户态 IIO 库）

- 本地路径：WSL `/home/congqiang/work/repo/libiio`（v0.26 已 clone）；官方 `analogdevicesinc/libiio`
- **local backend 本质**：按 IIO 命名规则拼 sysfs 路径 + `fopen`/`fread`/`fwrite`（`local.c:668/722`）
- 另有：设备发现（readdir 反解文件名）、短名映射、`ip:` 网络协议（iiod）、buffer

```text
iio_channel_attr_write_longlong(lo, "frequency", 2.4e9)
  → get_filename: "frequency" → "out_altvoltage0_frequency"
  → fopen("/sys/bus/iio/devices/iio:device0/out_altvoltage0_frequency")
  → 内核 ad9361_phy_write_raw → SPI
```

板上工具：`iio_info` / `iio_attr` / `iio_readdev` / `iio_reg` / `iiod`。

**统一多 RFIC 接口的业内做法**：上层 `radio_set_rx_freq()` 等语义 API → libradio.so → libiio/IIO；换芯片只换 backend，不打穿到裸 SPI。

---

## 第 18 层：采集 RX 的操作与代码流

```bash
echo 1 > .../iio:device4/scan_elements/in_voltage0_en
echo 1 > .../iio:device4/scan_elements/in_voltage1_en
echo 4096 > .../iio:device4/buffer/length
echo 1 > .../iio:device4/buffer/enable
iio_readdev -u local: -b 4096 cf-ad9361-lpc | xxd | head
echo 0 > .../iio:device4/buffer/enable
```

内核：`axiadc_update_scan_mode`（写 FPGA 通道使能）→ enable 时 `axiadc_hw_submit_block` → `iio_dmaengine_buffer_submit_block` → axi-dmac → 完成中断（`7c400000.dma`）→ 唤醒 read。

格式：`le:S12/16>>0`，I/Q 交错，30.72 Msps。

---

## 第 19 层：QEMU 里能看到这些驱动吗

**基本不能。** `tools/kernel-lab/build/linux-x86_64/.config`：

```text
CONFIG_X86=y
# CONFIG_SPI is not set
# CONFIG_IIO is not set
```

无 Zynq/无 AD9361 设备树/无硬件。QEMU 适合练 hello/VFS/GDB；看 AD9361 用真板 dump + 源码静态读。

---

## 关联

- [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]（深读版，带行号）
- [[资源-AD9361-寄存器文档]]（UG-570 / Datasheet / no-OS 与 Linux 寄存器头文件）
- [[概念-物理层射频驱动全景]]（RFIC/数据面/用户态分层）
- [[学习-Linux-学习路线]]（执行版阶段 5–6）
- [[学习-Linux-阶段0-源码地图与调试环境]]（QEMU+GDB 环境）
- [[MOC-Linux]]、[[MOC-射频]]、[[领域-L1物理层]]
