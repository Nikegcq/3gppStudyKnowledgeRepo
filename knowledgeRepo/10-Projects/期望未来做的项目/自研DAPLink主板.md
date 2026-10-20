---
type: project
tags: [DAPLink, CMSIS-DAP, STM32F103, 嵌入式硬件, 固件]
created: 2026-10-20
updated: 2026-10-20
status: active
start: 2026-10-20
due:
repo: DAPLink
local_path: /home/congqiang/work/gitHubRepo/DAPLink
---

# 自研 DAPLink 主板（STM32F103CB）

## 目标

研究基于 STM32F103CB 的自研 DAPLink 主机板，梳理硬件可变项、DAPLink 软件适配入口、最小修改范围和固件编译边界。

本文只讨论 **DAPLink 主机板（HIC）**，暂不展开被调试目标板的 `target.c`、`flash_blob.c` 和 Family ID。

## 核心结论

- DAPLink 并非只支持一种 Flash；它通过预编译的 Flash 算法支持多种目标芯片。
- 主机板若保持 STM32F103CB、内置全速 USB、8 MHz HSE 和参考引脚分配，通常不需要重写 DAPLink 核心。
- 自研硬件最常修改的是引脚、时钟、USB 标识、Flash/RAM 分区和 HIC 兼容性 ID。
- Flash 命令集、页大小、编程宽度或控制器变化时，不能只改容量，必须适配 HAL 或重新实现 Flash 算法。
- 新增 HIC 应优先复制现有 `stm32f103xb` 适配目录，保留参考实现，避免直接破坏上游代码。

## 当前基线

| 项目 | 当前配置 |
| --- | --- |
| 主控 | STM32F103CB，Cortex-M3 |
| 系统时钟 | 72 MHz |
| HSE | 8 MHz，PLL×9 |
| Flash | 128 KB |
| RAM | 20 KB |
| USB | 内置全速 USB Device |
| USB 连接控制 | PA15 |
| SWCLK | PB13 |
| SWDIO 输出 | PB14 |
| SWDIO 输入 | PB12 |
| nRESET | PB0，开漏 |
| UART | USART2，TX=PA2，RX=PA3 |
| UART 预留流控 | CTS=PA0，RTS=PA1；当前未启用 |
| 目标时钟输出 | PA8，TIM1 输出 8 MHz |
| Connected LED | PB6，低有效 |
| Running/HID/CDC/MSC LED | 当前共用 PA9，低有效 |
| 目标电源使能 | PB15，低有效 |
| SWO/JTAG | 当前均未启用 |

HIC Flash 分区：

```text
Bootloader : 0x08000000
Interface  : 0x0800C000
Config     : 0x0801FC00
Flash 总量 : 0x00020000
RAM 总量   : 0x00005000
```

## 自研主板可能调整的硬件

| 硬件项目 | 典型变化 | 软件影响 |
| --- | --- | --- |
| 主控 MCU | F103CB 换 C8、RB、RC、ZE，或更换 MCU 系列 | Flash/RAM 配置必改；跨系列通常需要新建 HIC |
| MCU 封装 | LQFP48、QFN48 等 | 主要影响 PCB，软件取决于引脚复用 |
| Flash/RAM | 容量、页大小、双 Bank | 修改地址、分区、页大小和链接脚本 |
| HSE 时钟 | 8 MHz 改 12/16/25 MHz，或改外部有源时钟 | 修改 PLL、`HSE_VALUE`、Flash latency |
| USB 连接器 | Type-C、Micro-USB | 电气接口兼容时通常不改软件 |
| USB 保护器件 | ESD、TVS、限流、自恢复保险丝 | 通常不改软件 |
| USB 连接控制 | PA15 换脚，或取消软连接 | 修改 GPIO 定义和初始化 |
| USB 控制器 | 内置 FS USB 改外部 HS PHY | 必须新增 USB 硬件层驱动 |
| SWD 引脚 | PB13/PB14/PB12 换脚 | 修改引脚映射和 DAP GPIO 访问 |
| SWDIO 结构 | 独立输入/输出改单线双向 | 必须修改 `DAP_config.h` 中的输入、输出和方向控制 |
| nRESET | PB0 换脚、极性改变 | 修改引脚、开漏配置和复位函数 |
| 电平转换 | 3.3 V 改 1.8 V/5 V 目标接口 | 只换器件通常不改；增加方向使能脚需要改 |
| UART | USART2 改 USART1/3 | 修改串口实例、中断和 GPIO |
| UART 引脚 | TX/RX/CTS/RTS 改脚 | 修改 UART 初始化和引脚宏 |
| SWO | 增加 SWO 输入 | 当前关闭，需要新增驱动和引脚 |
| JTAG | 增加 TCK/TMS/TDI/TDO/nTRST | 当前不支持，需要实现 JTAG I/O |
| LED | 改脚、数量、极性 | 修改 IO 配置；极性变化修改 GPIO 函数 |
| 按键 | 增加用户、Boot 或复位按键 | 修改 GPIO 初始化和按键读取 |
| 目标供电 | 增加负载开关、限流、电压检测 | 修改电源使能脚或新增检测逻辑 |
| 目标时钟输出 | 更换输出脚或频率 | 修改 TIM 和 GPIO 配置 |
| 外部存储 | 增加 EEPROM、SPI Flash | 当前默认使用内部 Flash，需要新增存储后端 |
| Bootloader 分区 | 增大、缩小或取消 Bootloader | 修改 BL/IF 地址并重新编译两者 |
| 产品身份 | 新 VID/PID、厂商名、HIC ID | 修改 USB 描述符和兼容性 ID |

## 软件修改映射

| 软件文件 | 职责 | 何时修改 |
| --- | --- | --- |
| `source/hic_hal/stm32/stm32f103xb/IO_Config.h` | SWD、USB、LED、nRESET、电源使能引脚 | 引脚或有效电平变化 |
| `source/hic_hal/stm32/stm32f103xb/DAP_config.h` | CMSIS-DAP 能力、SWD/JTAG/SWO/UART、GPIO 访问 | 接口能力或 SWDIO 结构变化 |
| `source/hic_hal/stm32/stm32f103xb/gpio.c` | GPIO 初始化、LED、电源、PA8 时钟输出 | GPIO、极性或功能变化 |
| `source/hic_hal/stm32/stm32f103xb/uart.c` | UART 外设、中断、TX/RX/流控 | UART 实例或引脚变化 |
| `source/hic_hal/stm32/stm32f103xb/sdk.c` | HSE、PLL、系统时钟、HAL tick | 晶振或系统时钟变化 |
| `source/hic_hal/stm32/stm32f103xb/usb_config.c` | USB VID/PID、字符串、端点 | 产品身份或 USB 配置变化 |
| `source/hic_hal/stm32/stm32f103xb/usbd_STM32F103.c` | STM32F103 USB 硬件层 | USB 控制器或端点结构变化 |
| `source/hic_hal/stm32/stm32f103xb/daplink_addr.h` | Flash/RAM、BL/IF/Config 分区 | MCU 容量或固件布局变化 |
| `source/board/stm32f103xb_bl.c` | Bootloader 板级信息、Flash/RAM 范围 | 分区、Board/HIC 信息变化 |
| `records/hic_hal/stm32f103xb.yaml` | MCU 宏、HIC ID、源码和启动文件 | 新 HIC 或设备变化 |
| `records/board/stm32f103xb_bl.yaml` | Bootloader 板级源文件选择 | 新板级文件 |
| `projects.yaml` | HIC 模块和 BL/IF 工程组合 | 新 HIC、新板卡 |
| `source/daplink/daplink.h` | HIC ID 和构建兼容性 | 新硬件与旧固件不兼容 |
| `source/hic_hal/device.h` | HIC 宏到设备头文件映射 | 新增 `INTERFACE_*` 类型 |
| `test/info.py` | 固件、Bootloader、Board/Family ID 测试映射 | 新构建加入测试 |

## 最小修改路径

### 1. 电气接口完全兼容

只更换 PCB、连接器、TVS、限流和去耦器件时，通常只需处理产品身份：

```text
usb_config.c      # VID/PID、厂商名、产品名
source/board/*.c  # Board ID、HIC ID
projects.yaml     # 工程名称
test/info.py      # 测试登记
```

若电路拓扑和固件兼容性均未变化，可以继续使用现有 HIC ID。

### 2. 只改引脚

通常修改：

```text
IO_Config.h
DAP_config.h
gpio.c
uart.c
```

其中 SWDIO 如果改成单线双向，必须重写以下接口：

```text
PIN_SWDIO_IN
PIN_SWDIO_OUT
PIN_SWDIO_OUT_ENABLE
PIN_SWDIO_OUT_DISABLE
```

### 3. Flash、RAM 或 MCU 容量变化

必须同步修改：

```text
daplink_addr.h
source/board/..._bl.c
records/hic_hal/*.yaml
CMSIS 设备头文件
启动文件
链接脚本所依赖的地址宏
```

如果 BL/IF 地址不兼容：

```text
DAPLINK_HIC_ID
IO_Config.h 中的 HIC ID 断言
test/info.py
```

Bootloader 和 Interface 必须成对重新编译。

### 4. 时钟变化

必须修改：

```text
sdk.c
stm32f1xx_hal_conf.h
records/hic_hal/*.yaml 中的 OS_CLOCK
```

当前软件按 8 MHz HSE、PLL×9、72 MHz 运行。更换晶振后，还要同步调整 PLL 倍频、AHB/APB 分频和 Flash latency。

### 5. USB 能力变化

- 仅换连接器和保护器件：通常不用改。
- 改 VID/PID、产品名或厂商名：修改 `usb_config.c`。
- 改 HID/WinUSB/Bulk/CDC 组合：同时检查 `usb_config.c`、`DAP_config.h` 和工程模块。
- 改 USB 控制器或增加外部 HS PHY：修改 `usbd_STM32F103.c`，必要时新增 USB 硬件层。

## 推荐的新 HIC 组织方式

建议为自研主板新建独立 HIC，而不是直接覆盖参考实现：

```text
source/hic_hal/stm32/<custom_hic>/
records/hic_hal/<custom_hic>.yaml
records/board/<custom_hic>_bl.yaml
source/board/<custom_hic>_bl.c
```

然后在 `projects.yaml` 中新增：

```text
module_hic_<custom_hic>
<custom_hic>_bl
<custom_hic>_if
```

如果硬件与现有 STM32F103CB 方案不兼容，应分配新的 HIC ID，避免 Bootloader 与 Interface 跨硬件误刷。

## 编译范围

STM32F103CB 专属 HIC 目录共有 47 个文件，其中包含 24 个头文件、13 个 HAL 源文件、CMSIS 系统文件、HIC 适配源文件和工具链启动文件。

实际参与 GCC 编译的芯片适配单元为 22 个：

```text
7 个 HIC 本地 C 文件
1 个 CMSIS system_stm32f1xx.c
13 个 STM32F1 HAL C 文件
1 个 GCC startup_stm32f103xb.S
```

官方固件目标：

```text
stm32f103xb_bl     Bootloader
stm32f103xb_if     通用 Interface
```

GCC 编译示例：

```bash
python tools/progen_compile.py -t make_gcc_arm stm32f103xb_bl
python tools/progen_compile.py -t make_gcc_arm stm32f103xb_if
```

## 代码审查项

- [ ] 修改 Flash 容量后，核对 `DAPLINK_ROM_SIZE`、BL/IF 地址和最后一个配置扇区。
- [ ] `EraseChip()` 当前页数计算使用取模 `%`，疑似应改为除法 `/`，整片擦除前必须验证。
- [ ] 自研板若使用低有效 LED，保持现有 GPIO 函数；高有效时必须同步修改。
- [ ] `gpio_set_board_power()` 当前为空。如果需要运行时控制目标电源，必须实现电源开关逻辑。
- [ ] 当前三个状态 LED 共用 PA9；若拆分到不同引脚，检查所有 LED 初始化。
- [ ] 当前 UART 已配置 CTS/RTS 引脚，但流控固定为无；若启用硬件流控需补齐配置。
- [ ] SWO、JTAG 当前关闭；新增硬件接口后修改能力宏并实现 DAP 访问函数。
- [ ] 修改 HIC ID 后，确认 BL、IF 和打包测试使用同一个 ID。
- [ ] 修改 BL/IF 分区后，禁止新旧固件混刷。

## 待确定

- [ ] 最终 MCU 型号、封装、Flash 和 RAM 容量
- [ ] HSE 频率及晶振/有源时钟方案
- [ ] USB 连接控制方式和 VID/PID
- [ ] SWD、UART、LED、电源、目标时钟输出最终引脚
- [ ] 是否需要 JTAG、SWO、硬件流控和目标电压检测
- [ ] Bootloader 是否保留及最终分区
- [ ] 是否需要新 HIC ID

## 边界说明

本文不涉及被调试目标板的 Flash 驱动。目标板适配属于另一条链路：

```text
source/board/<target_board>.c
source/family/<vendor>/<target>/target.c
source/family/<vendor>/<target>/flash_blob.c
records/board/<target_board>.yaml
```

## 关联

- [[MOC-C++与软件]]
- [[MOC-RTOS]]
