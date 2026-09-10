---
type: resource
tags: [Linux, 嵌入式, 驱动开发, IIO, 设备树, AD9361, SPI, DMA]
created: 2026-09-10
updated: 2026-09-10
status: active
source: plutosdr-fw（linux @ f3da30df）
repo: /home/congqiang/work/repo/plutosdr-fw
---

# 学习：Linux 驱动开发 —— AD9361 从 dtsi 到驱动调用流程

## 一句话总结

PlutoSDR 的 AD9361 不是“一个驱动干到底”，而是**控制面 + 数据面**两套驱动协作：`ad9361.c`（SPI 从设备驱动）负责 RF 芯片配置并注册成 IIO 设备 `ad9361-phy`；`cf_axi_adc_core.c`（platform 驱动）负责 AXI 数据通路，它通过 dtsi 的 `spibus-connected` 找到 SPI 侧驱动，取出 `axiadc_converter` 结构，再把 AXI DMA 缓冲注册成第二个 IIO 设备 `cf-ad9361-lpc`。整条链是：**dtb 节点 → 设备模型匹配 → probe → converter 握手 → IIO 注册 → DMA buffer**。

## 阅读基线

| 文件 | 作用 |
| --- | --- |
| `arch/arm/boot/dts/zynq-pluto-sdr.dts` | Rev A 入口，`#include "zynq-pluto-sdr.dtsi"`，另加电流监测、LED、按键 |
| `arch/arm/boot/dts/zynq-pluto-sdr.dtsi` | ad9361-phy / cf-ad9361-lpc / cf-ad9361-dds / 两路 AXI DMA 节点 + 全部 `adi,*` 初始化参数 |
| `drivers/iio/adc/ad9361.c` | SPI 控制面驱动，9681 行；probe 在 9501，注册 IIO 在 9634 |
| `drivers/iio/adc/ad9361_conv.c` | AD9361 ↔ cf_axi_adc 的适配层：channel 表、`post_setup`、converter 注册 |
| `drivers/iio/adc/ad9361.h` / `ad9361_private.h` / `ad9361_regs.h` | 时钟枚举、平台数据结构、寄存器与 SPI 命令字定义 |
| `drivers/iio/adc/cf_axi_adc_core.c` | AXI ADC 数据面 platform 驱动，probe 在 1061 |
| `drivers/iio/adc/cf_axi_adc.h` | `axiadc_converter` / `axiadc_chip_info` 跨驱动接口 |
| `drivers/dma/dma-axi-dmac.c` | AXI DMAC 的 dmaengine provider |
| `drivers/iio/buffer/industrialio-buffer-dmaengine.c` | IIO buffer 与 dmaengine 的桥 |
| `drivers/spi/spi.c`、`drivers/of/base.c`、`drivers/base/dd.c`、`drivers/base/platform.c` | 设备创建、总线匹配、probe 的内核机制 |

## 0 总览：两条主线一个握手

```text
控制面（CS）：
  dtsi: spi0/ad9361-phy@0  compatible = "adi,ad9363a"
      → SPI controller probe → of_register_spi_device → modalias = "ad9363a"
      → ad9361_driver.id_table 命中 → ad9361_probe()
      → IIO 设备 ad9361-phy（DIRECT_MODE，寄存器/属性访问）
      → ad9361_register_axi_converter() 把 axiadc_converter 存进 spi drvdata

数据面（数据流）：
  dtsi: fpga-axi/cf-ad9361-lpc@79020000  compatible = "adi,axi-ad9361-6.00.a"
      → simple-bus 递归 populate → platform_device → axiadc_of_match 命中
      → axiadc_probe()
      → 通过 spibus-connected 找到 SPI 设备，取它的 drvdata = converter
      → 用 converter->post_setup 初始化 HDL 通道；注册 IIO 设备
        cf-ad9361-lpc（INDIO_BUFFER_HARDWARE + dmaengine buffer "rx"）
```

关键点：**两个 IIO 设备的语义不同**。`ad9361-phy` 是控制面（频率、增益、滤波器、ENSM 等），`cf-ad9361-lpc` 是数据面（样本流、DMA buffer）。把这两个混在一起读，是初读 AD9361 驱动最容易迷路的地方。

## 1 dtsi 里写了什么

### 1.1 控制面节点：`ad9361-phy@0`

位置：`zynq-pluto-sdr.dtsi:185` 起，挂在 `&spi0` 下。

| 属性 | 作用 |
| --- | --- |
| `compatible = "adi,ad9363a"` | 决定 SPI 侧匹配到 `ad9361_id[]` 里的 `ad9363a`（见第 2.3 节） |
| `reg = <0>` | SPI 片选号（CS0） |
| `spi-cpha`、`spi-max-frequency = <10000000>` | SPI 时钟相位与最高 10 MHz，驱动 `ad9361_spi_check()` 会读实际 effective speed |
| `clocks = <&ad9364_clkin 0>`、`clock-names = "ad9364_ext_refclk"` | 40 MHz 参考时钟（dtsi 顶部 `ad9364_clkin` 节点） |
| `#clock-cells = <1>`、`clock-output-names = ...` | 该 SPI 设备同时是**时钟提供者**：驱动内部创建一整套时钟树，DDS 节点用 `<&adc0_ad9364 13>` 引用 |
| `en_agc-gpios`、`reset-gpios` | 可选 GPIO：EN_AGC、硬复位 |
| `adi,frequency-division-duplex-mode-enable` | FDD 模式；驱动据此选合成器表与 ENSM 状态 |
| `adi,rx-rf-port-input-select` / `adi,tx-rf-port-input-select` | RF 端口选择（RXA/RXB/RXC 等） |
| `adi,rf-rx-bandwidth-hz` / `adi,tx-attenuation-mdB` 等 | RF 带宽、TX 衰减、RX/TX 本振频率 |
| `adi,rx-path-clock-frequencies` / `adi,tx-path-clock-frequencies` | 6 级时钟链频率（BBPLL→ADC/DAC→…→采样时钟），解析失败驱动直接返回 NULL/-EINVAL |
| `adi,gc-rx1-mode`、`adi,mgc-*`、`adi,agc-*`、`adi,fagc-*` | 增益控制模式与参数（MGC / 慢速 AGC / 混合 AGC / 快速 AGC） |
| `adi,rssi-*`、`adi,temp-sense-*`、`adi,aux-dac*` | RSSI、温度传感、辅助 DAC 初始化 |

### 1.2 数据面节点

位置：`zynq-pluto-sdr.dtsi:94` 的 `fpga_axi: fpga-axi@0`（`compatible = "simple-bus"`）下。

| 节点 | compatible | 关键属性 | 谁消费 |
| --- | --- | --- | --- |
| `cf-ad9361-lpc@79020000` | `adi,axi-ad9361-6.00.a` | `dmas = <&rx_dma 0>`、`dma-names = "rx"`、`spibus-connected = <&adc0_ad9364>`、`adi,axi-decimation-core-available` | `cf_axi_adc_core.c` 的 `axiadc_probe` |
| `cf-ad9361-dds-core-lpc@79024000` | `adi,axi-ad9364-dds-6.00.a` | `clocks = <&adc0_ad9364 13>`、`dmas = <&tx_dma 0>`、`dma-names = "tx"` | `cf_axi_dds.c` |
| `rx_dma: dma@7c400000` | `adi,axi-dmac-1.00.a` | `interrupts = <0 57 ...>`；源 bus 32-bit type 2，目的 64-bit type 0 | `dma-axi-dmac.c` |
| `tx_dma: dma@7c420000` | `adi,axi-dmac-1.00.a` | `interrupts = <0 56 ...>`；源 64-bit type 0，目的 32-bit type 2 | 同上 |

三点要记住：

1. `spibus-connected` 是 ADI 自定义属性，不是通用总线属性：它把“谁配置 RF 芯片”告诉数据面驱动。
2. `dma-names` 是内核通用属性：数据面驱动用 `dma_request_chan(dev, "rx"/"tx")` 按名字取 DMA channel，正好对上。
3. TX DDS 节点用 `clocks = <&adc0_ad9364 13>`：索引 13 是 `ad9361.h` 枚举里的 `TX_SAMPL_CLK`（从 0 数：BB_REFCLK=0 … TX_SAMPL_CLK=13）。

### 1.3 为什么 defconfig 里看不到 `CONFIG_CF_AXI_ADC`

`zynq_pluto_defconfig:236` 有 `CONFIG_ADMC=y`；`drivers/iio/adc/Kconfig:593-596` 的 `config ADMC` 带 `select CF_AXI_ADC`，而 `CF_AXI_ADC`（Kconfig:449-453）又 `select IIO_BUFFER / IIO_BUFFER_HW_CONSUMER / IIO_BUFFER_DMAENGINE`。所以数据面驱动是被 `ADMC` **间接选中的**，不在 defconfig 里显式出现。读 Kconfig 时别只看显式行。

## 2 从 dtb 到 device：内核设备模型怎么走

### 2.1 platform 设备创建

- 内核启动后，`drivers/of/platform.c:517` 的 `of_platform_default_populate_init()`（`arch_initcall_sync`）调用 `of_platform_default_populate(NULL, ...)`。
- `of_platform_populate()` 递归遍历 DT 子节点，对匹配总线（含 `simple-bus`）的节点调用 `of_platform_device_create` 建 `platform_device`。
- 因此 `fpga-axi@0` 下的 `cf-ad9361-lpc`、`dma@7c400000` 等都变成 platform device；SPI 控制器本身也是 platform device（amba 总线部分同理）。

### 2.2 SPI 子设备创建

- SPI 控制器驱动 probe 后调用 `spi_register_controller`，其中 `drivers/spi/spi.c:3309` 调 `of_register_spi_devices(ctlr)`。
- `of_register_spi_device()`（spi.c:2439）执行 `of_modalias_node(nc, spi->modalias, ...)`；`drivers/of/base.c:1223` 的实现是：取 `compatible` 第一项，**剥掉厂商前缀**（去掉 `adi,`），得到 `ad9363a` 作为 `spi->modalias`。

### 2.3 总线匹配与 probe

**ad9361（SPI 总线）**

- 驱动定义：`ad9361.c:9670` 的 `struct spi_driver ad9361_driver`，只有 `.id_table`，**这个版本没有 `.of_match_table`**；`module_spi_driver()` 在 9677 展开为注册。
- 匹配：`drivers/spi/spi.c:375 spi_match_device()` 先试 OF 匹配；没有 `of_match_table` 时落到 `spi_match_id(sdrv->id_table, spi->modalias)`（spi.c:393）。`ad9361_id[]`（ad9361.c:9661）里有 `{"ad9363a", ID_AD9363A}`，命中。
- probe：总线封装 `spi_probe()`（spi.c:410）做时钟默认值、IRQ 等准备，然后调用 `sdrv->probe(spi)`，即 `ad9361_probe()`。

**cf_axi_adc（platform 总线）**

- 驱动定义：`cf_axi_adc_core.c:1268` 的 `platform_driver axiadc_driver`，`.of_match_table = axiadc_of_match`。
- 匹配：`drivers/base/platform.c:1331 platform_match()` 先走 `of_driver_match_device()`，用 `compatible = "adi,axi-ad9361-6.00.a"` 命中 `axiadc_of_match[]`（cf_axi_adc_core.c:967）。
- probe 调用链：设备核心 `drivers/base/dd.c:584 really_probe()` → `call_driver_probe()` → 总线 probe 包装 → `platform_driver.probe`（`axiadc_probe`）。

**EPROBE_DEFER**：probe 返回 `-EPROBE_DEFER` 时，设备核心把它放回 deferred list，等依赖就绪后自动重试。AD9361 与 cf_axi_adc 的时序问题就是靠这个机制解决的（见第 5.1 节）。

## 3 控制面：`ad9361_probe()` 逐步拆解

函数位置 `ad9361.c:9501`。顺序和每一步的意义：

1. `devm_clk_get(&spi->dev, NULL)`（9515）：取 dtsi 的第一个 clock（40 MHz `ad9364_clkin`）。若时钟 provider 还没就绪，返回 `-EPROBE_DEFER`。
2. `devm_iio_device_alloc(&spi->dev, sizeof(*phy))`（9520）：分配 IIO 设备，private data 是 `struct ad9361_rf_phy`；随后 `devm_kzalloc` 分配 `ad9361_rf_phy_state`，`phy->state = st`、`phy->spi = spi`、`phy->clk_refin = clk`，初始化 `mutex`。
3. `ad9361_phy_parse_dt()`（9534，函数体 8594）：把 dtsi 的几十个 `adi,*` 属性翻译成 `struct ad9361_phy_platform_data`。分类记忆：工作模式 / 数字接口与延迟 / RF 端口 / 时钟链 / 增益与 AGC / RSSI / 辅助 DAC-ADC / 温度 / GPIO。`rx/tx-path-clock-frequencies` 是必需项，缺了直接返回 NULL → probe `-EINVAL`。
4. 可选 GPIO：`reset`、`sync`、`cal-sw1/sw2`（9540 起），都用 `devm_gpiod_get_optional`。
5. `ad9361_register_ext_band_control()`：外部频段控制（低通/带通滤波器切换），失败只告警不致命。
6. `ad9361_reset(phy)`（9572，函数 934）+ `ad9361_spi_check(spi)`（9575，函数 9460）：硬复位后读 `REG_PRODUCT_ID`，校验 `PRODUCT_ID_9361 (0x08)`，返回 SPI 实际有效速率。**阅读疑点**：9579 的 `rev = ret & REV_MASK` 用的是上一步的返回值而不是刚读到的 ID，这个版本打印的 Rev 可能不可信，值得和主线驱动对比确认。
7. `INIT_WORK` + `init_completion`（9586 起）：为后续异步/校准状态机做准备。
8. `register_clocks(phy)`（9589，函数 6646）：创建并注册整套内部时钟，例如 `tx_refclk / rx_refclk / bb_refclk / bbpll_clk / adc_clk / … / rx_sampl_clk / … / tx_sampl_clk`。每个时钟的 `clk_ops` 最终都会落到 SPI 寄存器写（如 `ad9361_set_clk_scaler`）。**这是“DT 时钟”和“芯片寄存器”的转换层**。
9. `ad9361_setup(phy)`（9592，函数 4946）：真正把 dtsi 参数写进 AD9361。主顺序（对照 `ad9361.c:4946-5254`）：
   - 带宽合法性检查、辅助 DAC/GPO；
   - 使能 CTRL/bandgap、DCXO 调谐、参考分频、打开时钟；
   - `clk_set_rate(BB_REFCLK)`、`ad9361_set_trx_clock_chain_default()` 配时钟链；
   - RX/TX 通道开关与 RF 端口；
   - 辅助 ADC、控制输出、`txrx_synth_cp_calib`、RX/TX RFPLL 频率与使能；
   - mixer GM 表、增益控制表（`ad9361_gc_setup`）、RX/TX 模拟滤波器校准、TIA/ADC 设置、DC offset 校准、TX quadrature 校准、tracking；
   - 最后设 ENSM 模式（FDD/TDD）与 TX 衰减。
10. `of_clk_add_provider()`（9598）：把第 8 步注册的时钟树暴露给 DT，于是 DDS 节点的 `clocks = <&adc0_ad9364 13>` 能解析成 `TX_SAMPL_CLK`。
11. 注册 IIO 设备（9628-9634）：`indio_dev->info = &ad9361_phy_info`、`modes = INDIO_DIRECT_MODE`、`channels = ad9361_phy_chan`（8104 起：温度、RX/TX LO、RX1/RX2/TX1/TX2、AUXADC/DAC），`num_channels` 在 1R1T 模式下减 2；`devm_iio_device_register()` 创建 sysfs/chrdev（内核侧实现见 `drivers/iio/industrialio-core.c:1937`）。
12. `ad9361_register_axi_converter()`（9637）：见第 4 节，这是与数据面握手的关键。
13. 创建 `filter_fir_config`、`gain_table_config` 两个 sysfs bin 文件，注册 debugfs。

### 3.1 SPI 寄存器访问细节

驱动所有配置最终走两层：

- **命令字**（`ad9361_regs.h:2765`）：bit15 读写（`AD_WRITE=1<<15`）、bit14:12 数据长度-1（`AD_CNT`）、bit9:0 寄存器地址（`AD_ADDR`）。即 16-bit 命令 + N 字节数据。
- **传输**：
  - 读：`spi_write_then_read(spi, cmd[2], 2, rbuf, num)`，见 `ad9361_spi_readm()`（712）。
  - 写：`spi_write_then_read(spi, cmd[2]+data, num+2, NULL, 0)`，见 `ad9361_spi_write()`（791）/`writem()`（852）。
  - 读-改-写位域：`__ad9361_spi_writef`（804）。
- dtsi 的 `spi-cpha`（clock phase）就是为这种“命令字在前、数据在后”的时序服务的；`spi-max-frequency` 决定初始速率。

## 4 跨驱动握手：`axiadc_converter`

这是整条链最需要理解的设计。

在 `ad9361_conv.c:726`（`#if IS_ENABLED(CONFIG_CF_AXI_ADC)` 分支）：

1. `devm_kzalloc` 出 `struct axiadc_converter`；
2. 读 `REG_PRODUCT_ID` 再校验；
3. `conv->chip_info = &axiadc_chip_info_tbl[ID_AD9361 / ID_AD9364 / ID_AD9361_2]`，其中 AD9361 项（`ad9361_conv.c:236`）定义 4 个通道、12-bit signed、16-bit storage、可用 scan mask；
4. `conv->write_raw/read_raw = ad9361_write_raw/read_raw`、`conv->post_setup = ad9361_post_setup`；
5. `conv->clk = phy->clks[RX_SAMPL_CLK]`（752）、`conv->adc_clk = clk_get_rate(conv->clk)`；
6. `spi_set_drvdata(spi, conv)`（755）：**把 converter 挂到 SPI 设备上**。

数据面 `axiadc_probe` 随后用同一个 SPI 设备（`spibus-connected` 指定）通过 `to_converter()`（cf_axi_adc_core.c:68，内部就是 `spi_get_drvdata()`）把它取回来。这样 RF 控制驱动和 AXI 数据驱动就通过 `struct axiadc_converter` 解耦地连起来了。

注意：`ad9361_register_axi_converter()` 这个名字容易误解——它不注册 IIO 设备，只是填充 converter 并挂 drvdata。

## 5 数据面：`axiadc_probe()` 逐步拆解

函数位置 `cf_axi_adc_core.c:1061`。

### 5.1 先解决依赖：`spibus-connected` + `EPROBE_DEFER`

- `of_match_node(axiadc_of_match, pdev->dev.of_node)`（1077）取到 core info（版本）。
- `of_parse_phandle(..., "spibus-connected", 0)`（1089）拿到 `ad9361-phy@0` 的 device_node。
- `bus_for_each_dev(&spi_bus_type, NULL, axiadc_spidev, axiadc_attach_spi_client)`（1097）：遍历 SPI 总线上的设备，回调（847）只接受 `of_node` 相同且 `dev->driver` 已绑定的设备。
- 如果没找到（ad9361 还没 probe 完），返回 `-EPROBE_DEFER`；等 SPI 驱动 probe 成功并设置 drvdata 后，内核自动重试。
- 找到后 `try_module_get`、`get_device`、`device_link_add(..., DL_FLAG_AUTOREMOVE_SUPPLIER)`：锁住依赖关系（probe 顺序、卸载顺序、电源管理）。

### 5.2 硬件与 IIO 初始化

1. `devm_iio_device_alloc`，`iio_priv` 是 `struct axiadc_state`（1093）。
2. `devm_jesd204_dev_register`（1096）：AD9361 走的是非 JESD 路径，这里只是统一框架。
3. `platform_get_resource(IORESOURCE_MEM, 0)` + `devm_ioremap_resource`：把 dtsi 的 `reg = <0x79020000 0x6000>` 映射成 `st->regs`，之后 `axiadc_read/write` 都是 `ioread32/iowrite32`。
4. `conv = to_converter(st->dev_spi)`（1124）：从 SPI 侧取 converter；`iio_device_set_drvdata(indio_dev, conv)`、`conv->indio_dev = indio_dev`，两边互指。
5. 复位 HDL 核：`axiadc_write(ADI_REG_RSTN, 0)` → `ADI_MMCM_RSTN` → `ADI_RSTN | ADI_MMCM_RSTN`（1157 起），每次间隔 10 ms。
6. 读 `ADI_AXI_REG_VERSION`，比对 `of_match` 的版本（major 不能高于驱动预期）。
7. `indio_dev->available_scan_masks = conv->chip_info->scan_masks`；`axiadc_channel_setup()`（788）把 `conv->chip_info->channel[]` 拷贝到 `st->channels[]`，并设置 `indio_dev->channels/num_channels`。
8. `conv->post_setup(indio_dev)`：对 AD9361 就是 `ad9361_post_setup()`（ad9361_conv.c:647，注册在 748），它会把 AD9361 的 1R1T/2R2T、I/Q 通道使能、格式、DC 滤波、I/Q 校正写进 HDL 寄存器，并做数字接口 tune（`ad9361_dig_tune`）。**这是控制面配置真正落到数据面 HDL 的时刻**。
9. `axiadc_configure_ring_stream(indio_dev, NULL)`（1212 起，函数 128）：因为 dtsi 有 `dmas`，这里创建 DMA 型 IIO buffer。
10. `devm_iio_device_register()`（1236）：注册第二个 IIO 设备 `cf-ad9361-lpc`，模式是 `INDIO_BUFFER_HARDWARE`。

### 5.3 buffer → dmaengine 的具体调用

`axiadc_configure_ring_stream` → `devm_iio_dmaengine_buffer_alloc(dev, "rx", &axiadc_dma_buffer_ops, indio_dev)`（136）：

- `industrialio-buffer-dmaengine.c:209` 用 `dma_request_chan(dev, "rx")` 申请 DMA，名字对上 dtsi 的 `dma-names = "rx"`；
- `dma_request_chan` 经 of_dma 解析 `dmas = <&rx_dma 0>`，落到 `dma-axi-dmac.c` 的 `of_dma_xlate`/`axi_dmac_alloc_chan_resources`；
- buffer 的模式是 `INDIO_BUFFER_HARDWARE`，`mmap` 由 `iio_dma_buffer_mmap` 提供（`iio_dmaengine_buffer_ops`）。

## 6 一次采样在内核里怎么流动

以 RX（`cf-ad9361-lpc`）为例：

1. 用户态通过 sysfs 打开 `buffer/enable`、设置 `buffer/length`、使能 `scan_elements/in_voltageN_en`（触发 `axiadc_update_scan_mode()`，758，把 scan_mask 写进各通道 `ADI_REG_CHAN_CNTRL` 的 `ADI_ENABLE`）。
2. 应用向 `/dev/iio:deviceX` 提交/等待 buffer block；IIO DMA buffer 队列调用 `axiadc_hw_submit_block()`（109）。
3. `axiadc_hw_submit_block` 先调 `iio_dmaengine_buffer_submit_block()`（`industrialio-buffer-dmaengine.c:61`）：
   - `dmaengine_prep_slave_single(chan, phys_addr, bytes, direction, DMA_PREP_INTERRUPT)`；
   - 设置 `desc->callback_result = iio_dmaengine_buffer_block_done`；
   - `dmaengine_submit()` → `dma_async_issue_pending()`。
4. `dma-axi-dmac.c` 把描述符写进 DMAC 寄存器；HDL 的 `axi_ad9361_adc_dma` 以 `DMA_TYPE_SRC=2(FIFO) → DMA_TYPE_DEST=0(AXI-MM)` 把样本写成 DDR 里的 buffer。
5. DMAC 产生中断 → 驱动 IRQ handler → `iio_dmaengine_buffer_block_done` 标记 block 可用 → 用户态 `read/mmap/poll` 返回数据。
6. 采样节拍来自 `RX_SAMPL_CLK`（`conv->clk`）；TX 方向用 DDS 节点 DT 里解析出的 `TX_SAMPL_CLK`（clock index 13）。

## 7 两个 IIO 设备对照

| 维度 | `ad9361-phy` | `cf-ad9361-lpc` |
| --- | --- | --- |
| 驱动 / 总线 | `ad9361.c`，SPI | `cf_axi_adc_core.c`，platform |
| DT 匹配 | SPI `id_table` + modalias | `of_match_table`（`axiadc_of_match`） |
| 内核对象 | `iio_dev` + `ad9361_rf_phy` | `iio_dev` + `axiadc_state`（drvdata 是 converter） |
| IIO modes | `INDIO_DIRECT_MODE` | `INDIO_BUFFER_HARDWARE` |
| channels | 温度 / LO / RX/TX 增益 / AUXADC-DAC | 4× `IIO_VOLTAGE`（12-bit signed，16-bit storage，scan_index 0-3） |
| 数据流 | 无（只做寄存器与属性读写） | DMA：FIFO ↔ DDR，mmap 给用户态 |
| 主要用途 | 频率、带宽、增益、校准、ENSM | IQ 采样流 |

TX 数据面是第三个 IIO 设备 `cf-ad9361-dds-core-lpc`，由 `drivers/iio/frequency/cf_axi_dds.c` 驱动，buffer 名为 `"tx"`。

## 8 上板可验证的观察点

- `dmesg | grep -i -e ad9361 -e axi`：应看到 AD936x 初始化、AIM probed ADC 的打印。
- `cat /sys/bus/iio/devices/iio:device*/name`：应看到 `ad9361-phy`、`cf-ad9361-lpc`。
- `ls /sys/bus/iio/devices/iio:device*/`：控制面设备有 `in_voltage*`、`out_altvoltage*`、`ensm_mode` 等；数据面设备有 `buffer/`、`scan_elements/`。
- `iio_info -u ip:...` 或 libiio 工具：能看到两个 device 的 channels 与 attrs，正好对应第 7 节。

## 9 待深挖 / 疑点

- `ad9361.c:9579 rev = ret & REV_MASK` 疑似用了旧变量，Rev 打印可能恒为 0；建议对照主线/新分支确认。
- `spibus-connected` 这种自定义 phandle 连接的通用替代方案（`device_link` + `devm_` 生命周期）值得单独整理。
- `ad9361_post_setup` 里对 HDL 通道寄存器的写入（R1_MODE、RATE、FORMAT、IQCOR）可单独做一张“AD9361 配置寄存器 ↔ AXI 数据通路寄存器”对照表。
- TX 侧 `cf_axi_dds` 的 DDS buffer 与 cyclic DMA 尚未细读，留到阶段 4。

## 关联

- [[学习-Linux-学习路线]]（阶段 3 主战场）
- [[MOC-Linux]]（模块主页）
- [[概念-物理层射频驱动全景]]（RFIC 驱动 / 数据面 / 用户态 / L1 功能全景）
