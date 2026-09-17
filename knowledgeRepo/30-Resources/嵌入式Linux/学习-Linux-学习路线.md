---
type: resource
tags: [Linux, 嵌入式, 学习计划, u-boot, 内核, 驱动开发, DMA]
created: 2026-09-09
updated: 2026-09-14
status: active
---

# Linux 学习路线（嵌入式系统软件）

> **范围说明（2026-09-17）**：本文是「通用内核 + PlutoSDR 全链」的**长期详细路线**（T/P 线全文）。进度请挂到对应计划，不要在本文直接当周计划用：
> - 进行中：[[计划-2026Q4-双主线学习-O-DU-L1与嵌入式系统]] —— RFIC 使用（R0–R4），**不含**通用内核闸门；
> - 独立延后：[[计划-独立线-Linux通用内核机制]] —— K1–K6 / G1–G5，**不在 Q4 八周内**。
> 通用机制问题在 RFIC 计划中只作「按需回查本文」，不计任一计划进度。

## 一句话总结

参照通信知识（L1）的学习结构：**阶段化学习计划 + 「主读材料」映射表 + 概念 / 学习笔记 + 进度勾选**。通信学习里「规范章节」的位置，这里换成「代码文件 + 内核 / 厂商文档」；目标不是泛读，而是让 PlutoSDR 这条真实链路（RF → FPGA → DMA → Linux → 用户态）的每一步都能讲清楚、有代码证据。

## 优化整合版执行路线（2026-09-10，以此为准）

设计原则：**一条主线、三个地基、两次验证、一个真实落点**。

- 一条主线：PlutoSDR 真实链路（u-boot → 设备树 → ad9361 → cf_axi_adc → DMA → 用户态）。
- 三个地基：源码地图与工具、最小驱动闭环（模块 + 字符设备）、QEMU+GDB 动态调试。
- 两次验证：静态验证（画出调用链、标出文件 / 函数 / 行）+ 动态验证（断点单步，或板上 `dmesg` / sysfs / libiio）。
- 一个真实落点：每个通用内核概念都要落到 AD9361 / PlutoSDR 的具体代码上。

### 执行版总览

| 阶段  | 目标            | 关键任务                                                                                                 | 产出 / 验收                                                            | 建议投入  | 对应旧编号            |
| --- | ------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----- | ---------------- |
| 0   | 环境与源码地图       | WSL 构建依赖、QEMU+GDB、elixir/cscope/ctags；plutosdr-fw 目录与产物地图                                            | 能启动 QEMU 并 attach GDB；画出源码树 + 产物链 → 成果见 [[学习-Linux-阶段0-源码地图与调试环境]] | 1 天   | T0 + P0          |
| 1   | 最小驱动闭环        | hello 模块；misc 字符设备；`file_operations → VFS`；`copy_*_user`、`container_of`、`class_create/device_create` | 完成 `insmod → cat/echo → dmesg → rmmod`；写 VFS 调用链笔记                 | 2–3 天 | T1 + T2          |
| 2   | QEMU+GDB 动态调试 | 断 `start_kernel`、`do_initcalls`、自己的 `open/read`；单步与变量观察                                              | GDB 调试小抄 + 一次完整断点记录                                                | 1–2 天 | T3               |
| 3   | 设备模型与总线匹配     | `drivers/base/{bus,dd,platform}.c`、`drivers/of/platform.c`、SPI modalias                              | 「DT node → device → bus match → probe」图；用 pluto dtsi 举例            | 1–2 天 | T5 + P2          |
| 4   | Pluto 构建与启动链  | `pluto.its`、FIT、`bootm`、uboot env、DT 传递                                                              | 启动链图 + `pluto.its` 逐段注释                                            | 2 天   | P0 + P1          |
| 5   | 控制面驱动与 IIO    | `xilinx-xadc` 热身 → ad9361 probe/时钟/setup/converter/IIO                                               | 更新 [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]；能讲双 IIO 设备分工              | 3–5 天 | T4 + P3          |
| 6   | 数据面与用户态       | cf_axi_adc probe、IIO dmaengine buffer、`dma-axi-dmac`、mmap/libiio                                     | 端到端数据通路图 + buffer→DMA→用户态调用链                                       | 3–5 天 | P4 + T6(IIO/DMA) |
| 7   | 中断、并发与实时性     | PL IRQ → threaded/workqueue/waitqueue；spinlock/mutex；对照 RTOS                                         | 中断时间线 + Linux vs RTOS 对照图                                          | 1–2 天 | P5               |
| 8   | 综合实践与 RAN 映射  | 板上 libiio 收发；srsRAN/OAI 的 radio 抽象；复盘                                                                | 端到端图 + 「嵌入 Linux 视角看 RAN 数据通路」小结                                   | 2–3 天 | P6               |

### 执行闸门（gate）

- [x] G1：完成阶段 1+2，能在 QEMU+GDB 里断住自己写的 `open/read`，并解释用户态 `read()` 到驱动回调的路径。—— 2026-09-14 已断住 `lab_read`（栈：lab_read→vfs_read→ksys_read），详见 [[学习-Linux-阶段1-最小驱动闭环]]；阶段 2 的 do_initcalls 启动断点仍待做。
- [ ] G2：完成阶段 3，能画出「DT node → device → bus match → driver.probe」通用链，并能指出 SPI 与 platform 匹配方式的差异。
- [ ] G3：进入阶段 5 前，先断在 `ad9361_probe` 与 `axiadc_probe`（或至少静态指出两者先后与 `EPROBE_DEFER` 条件）。
- [ ] G4：完成阶段 6，能画出 AD9363 → axi_ad9361 → axi_dmac → DDR → IIO buffer → mmap/libiio 的完整图。

### 跨主题协同（与知识库其他 MOC 的结合）

| Linux 阶段 | 协同主题 | 具体结合点 |
| --- | --- | --- |
| 阶段 4 | [[MOC-FPGA]] | bitstream 何时加载、PS-PL 接口、AXI 地址映射 |
| 阶段 5 | [[MOC-射频]]、[[领域-L1物理层]] | AD9361 采样率/带宽/RF 端口与 L1 参数的关系 |
| 阶段 6 | [[MOC-FPGA]]、[[MOC-C++与软件]] | `axi_dmac`/cpack 数据打包、libiio 用户态、零拷贝 |
| 阶段 7 | [[MOC-RTOS]] | 中断响应与任务唤醒：Linux threaded IRQ/workqueue vs RTOS ISR→队列→任务 |
| 阶段 8 | [[MOC-O-RAN开源]]、[[领域-L1物理层]] | srsRAN/OAI radio 抽象、采样流与 PHY 的接口 |

### 推荐学习节奏

- 单次闭环（60–90 min）：读 1 个入口函数 / 结构体 → 静态画调用链 → 断点或日志验证 → 更新笔记 → 写 Journal 一两行。
- 每周一次回访（30 min）：随机挑一个函数，不看笔记画出它的调用链；讲不清的地方转成下一周任务。
- 阶段 0–2 建议连续完成，不要提前跳进 ad9361；阶段 5 之后每个阶段都要有一个可展示产物（图 / 笔记 / 实验记录）。
- 版本策略：阶段 0–3 可配一份接近 mainline 6.x 的源码（配合 elixir 与 docs.kernel.org）学通用机制；阶段 4–8 回到 plutosdr-fw `linux @ f3da30df` 查实际行号。

### 执行版与详细参考的对应

| 执行阶段 | 详细参考位置 |
| --- | --- |
| 0 | 本文「详细参考 1」的 T0 + 「详细参考 3」阶段 0 |
| 1–2 | T1–T3；方法细节见 [[学习-Linux-内核源码阅读与驱动学习法]] |
| 3 | T5 + 阶段 2；内核机制见 AD9361 笔记第 2 节 |
| 4 | 阶段 0/1 |
| 5 | T4 + 阶段 3；深读见 [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]] |
| 6 | 阶段 4 + T6 |
| 7 | 阶段 5 |
| 8 | 阶段 6 |

## 本地代码与状态（截至 2026-09-10）

| 载体 | 本地路径 | 状态 |
| --- | --- | --- |
| plutosdr-fw | `/home/congqiang/work/repo/plutosdr-fw` | 顶层 Makefile / scripts ✓；四个子模块已按锁定 commit 初始化（2026-09-09，经 ghfast.top 镜像）：`buildroot @ e783aadc`、`hdl @ 065c8f18`、`linux @ f3da30df`（ADI 2018_R1）、`u-boot-xlnx @ 90401ce9`（pluto） |

子模块初始化命令（换新环境时执行；本机 GitHub 直连不可用时加镜像前缀）：

```bash
cd /home/congqiang/work/repo/plutosdr-fw
git submodule update --init hdl linux u-boot-xlnx buildroot
```

说明：2026-09-09 前 `hdl/` 是非正规状态（有文件但缺 `.git` 元数据），本次已重拉为正规 submodule；旧的未管理 hdl 内容备份在 `/home/congqiang/work/repo/_plutosdr_submodule_backup_20260909/hdl-unmanaged-20260909`，确认不需要后可删除。

## 详细参考 1：T 线 × P 线任务拆分

> 2026-09-10 整合：原阶段 0–6 是 **P 线**（PlutoSDR 真实链路）；新增 **T 线**（通用内核源码阅读、最小驱动、QEMU+GDB、设备模型）作为地基。T 线不替代 P 线，而是让 P 线的每一步都有全局认知和动态验证能力；方法细节见 [[学习-Linux-内核源码阅读与驱动学习法]]。

| 线 | 目标 | 阶段划分 |
| --- | --- | --- |
| T（通用地基） | 会读、会写、会调内核驱动 | T0 源码地图与工具 → T1 最小模块闭环 → T2 字符 / 杂项设备 → T3 QEMU+GDB 动态调试 → T4 对照内核自带驱动 → T5 设备模型 → T6 真实子系统 |
| P（真实链路） | 讲清 PlutoSDR 从 RF 到用户态的每一步 | 原有阶段 0–6（u-boot → 设备树 → IIO → DMA → 中断 → 综合） |

推荐穿插顺序（最小闭环优先）：

- [ ] T0 → T1 → T3（先能断点）→ P0 / P1 / P2 → T2 / T4 / T5（与 P3 并行）→ P3–P5 → T6 / P6
- [ ] 硬性检查点：进入 P3（ad9361）之前，至少完成 T1 + T2 + T3，能在 QEMU+GDB 里断住自己写的 `open` / `read`。
- [ ] 版本策略：T 线建议另备一份接近 mainline 6.x 的源码（配合 elixir 与 docs.kernel.org）学通用机制；P 线继续用 plutosdr-fw 的 `linux @ f3da30df` 查行号，两者不要混着引用。

### T 线任务清单

- [x] T0 源码地图与工具：记住 `arch/`、`drivers/`、`fs/`、`kernel/`、`mm/`、`include/`、`init/`、`Documentation/` 的职责；会用 elixir.bootlin.com + cscope/ctags/`rg`；产出「源码地图 + 入口函数导航模板」→ 见 [[学习-Linux-阶段0-源码地图与调试环境]]
- [x] T1 最小模块闭环：写 hello 模块 + Makefile，走通 `insmod` → `lsmod` → `dmesg` → `rmmod`；读 `include/linux/module.h`，理解 `module_init/exit` 不是 `main`。→ [[学习-Linux-阶段1-最小驱动闭环]]
- [x] T2 字符 / 杂项设备：读 `include/linux/fs.h` 的 `struct file_operations` 与 `fs/read_write.c` 的 `vfs_read`；用 misc 字符设备自动建节点（lab_chardev）；练 `copy_to_user/copy_from_user`、`private_data + container_of`、mutex 保护；对照 `drivers/char/misc.c`。→ [[学习-Linux-阶段1-最小驱动闭环]]
- [ ] T3 QEMU+GDB 动态调试：环境与 `start_kernel` 断点已通（见 [[学习-Linux-阶段0-源码地图与调试环境]]）；余 `do_initcalls`、自己的 `open/read`，之后可断在 `ad9361_probe`、`axiadc_probe`、`iio_device_register` 动态核对 P 线调用链。
- [ ] T4 对照内核自带驱动：选一个 `drivers/char/` 简单驱动对照自己的代码；选一个简单 IIO 驱动（如 `xilinx-xadc.c`）建立 `iio_dev → channels → sysfs` 直觉，为 P3 铺路。
- [ ] T5 设备模型：读 `drivers/base/{bus,dd,platform}.c` 与 `drivers/of/platform.c`，能画「DT node → device → bus match → driver.probe」，理解 `-EPROBE_DEFER` 与 device link。
- [ ] T6 真实子系统：在 IIO / SPI / USB char / dmaengine 中选一条深入；建议先 IIO（与 P3/P4 重叠最多），USB 作为第二子系统。

## 详细参考 2：P 线阶段速览

| 阶段 | 主题与核心问题 | 主读：代码 / 文件 | 配套资料 | 练习 / 产出 |
| --- | --- | --- | --- | --- |
| 0 | 全景与仓库地图：plutosdr-fw 整个工程在编什么、产物长什么样 | `README.md`、`Makefile`（产物：`boot.bin` = FSBL + u-boot.elf、`uboot-env.dfu`、`pluto.dfu`、`pluto.itb`）、`scripts/pluto.mk`（`zynq-pluto-sdr{,-revb,-revc}.dtb`）、`hdl/projects/pluto/{README,system_bd.tcl,system_top.v}` | 构建 Wiki（wiki.analog.com Building the image） | 仓库地图笔记；画「构建产物与启动链」图（对应通信学习里的总体架构一步） |
| 1 | u-boot 启动：复位之后、内核接管之前发生什么；FPGA bitstream 何时加载 | `u-boot-xlnx/`（待 init，ADI pluto 分支）：u-boot 源码树（arch/arm、board/zynq、include/configs）；根工程 `scripts/pluto.its`（FIT 描述：**先加载 FPGA（bitstream @0xF000000）再启动 zImage + fdt + ramdisk**）；Makefile 里 `uboot-env` 相关目标 | u-boot 官方文档 / 源码注释 | 笔记「学习-u-boot-启动与FIT」；能逐段解释 `pluto.its` 的 image 与 configuration |
| 2 | Linux 内核启动与设备树：内核怎么知道有什么硬件、平台驱动怎么 probe | `linux/`（待 init，ADI 2018_R1）：`arch/arm/boot/dts/zynq-pluto-sdr*.dts`、`drivers/of/`、`drivers/base/`（bus/device/driver 模型） | devicetree.org 规范；内核 `Documentation/devicetree` | 笔记「概念-设备树与平台设备」；把 dts 里 ad9361 / axi-dma 节点与 `system_bd.tcl` 的 IP 对应起来 |
| 3 | 设备驱动与 IIO 框架（驱动开发主战场）：真实 RF 芯片驱动如何注册、如何出数 | `linux/drivers/iio/adc/ad9361.c`、`cf_axi_adc.c`、`drivers/iio/dac/cf_axi_dds.c`（ADI 分支路径，init 后以实际为准）；驱动骨架：`module_init` / probe / `file_operations` | 内核 `Documentation/driver-api`；《Linux Device Drivers》等参考书 | 笔记「学习-Linux-驱动开发-从框架到IIO」；能说清 ad9361 驱动与 IIO buffer 的注册链 |
| 4 | DMA 与数据通路：高速数据怎么从 PL（FPGA）进内存再到用户态 | `hdl/projects/pluto/system_bd.tcl`（`axi_ad9361_adc_dma` / `axi_ad9361_dac_dma`，看 `DMA_TYPE_SRC/DEST`、`CYCLIC` 参数）；`linux/drivers/dma/axi-dmac.c`（待 init）；dmaengine / dma-mapping API；用户态 mmap / libiio | 内核 DMA-API 文档；ADI HDL 文档 | 画「AD9361 RX → axi_ad9361 → axi_dmac → Linux → libiio」通路图；笔记「概念-DMA与零拷贝」 |
| 5 | 中断与内核并发：数据到了怎么及时响应又不卡死 | Linux：`request_threaded_irq` / bottom-half / workqueue / spinlock（结合 IIO 驱动看）；对照 RTOS 的 `xQueueSendFromISR`（见 [[MOC-RTOS]]） | 内核 interrupts / locking 文档 | 笔记「学习-中断与并发-Linux vs RTOS」 |
| 6 | 综合实践（可选进阶）：把整条链跑通并对照 RAN 工程 | 上板跑 libiio 收发；改 dts / 驱动验证；对照 srsRAN / OAI 的 RU（radio / IIO 后端）怎么组织数据通路 | [[MOC-O-RAN开源]] 相关仓库笔记 | 产出端到端通路图与「嵌入 Linux 视角看 RAN 数据通路」小结 |

## 详细参考 3：P 线逐阶段任务与验收

阅读约定：
- 本节沿用原表阶段 0–6；每阶段给「能回答的问题 → 任务清单 → 练习/产出 → 完成标准」。
- 代码锚点以 `linux/`、`u-boot-xlnx/`、`buildroot/` 子模块 init 后的实际 checkout 为准；文末「实测与勘误」按 2026-09-09 的锁定 commit 做过一轮路径核对，init 后建议再确认一次。
- 每个阶段做完，按原「每个阶段的收尾动作」建笔记、写 Journal、更新本清单与 [[MOC-Linux]]。

### 阶段 0：全景与仓库地图

**学完能回答的问题**
1. `plutosdr-fw` 由哪几个仓库组成，各自分支 / 锁定状态是什么？
2. `build/` 里每份产物由哪条 Makefile 依赖链生成，烧到板的哪一段？
3. 复位后到 Linux 用户态大体分几段？（这阶段只要宏观对，细节留给阶段 1/2）

**任务清单**
- [ ] T0.1 在 WSL 顶层目录跑 `git submodule status` 与 `git status --short --branch`，把 4 个子模块状态记进笔记。2026-09-09 实测：`linux/`、`buildroot/` 未取内容；`u-boot-xlnx/` 半初始化；`hdl/` 有文件但缺 `.git` 元数据；另有一个未跟踪的嵌套 `plutosdr-fw/` 副本，先不动。
- [ ] T0.2 读 README 的 "Build Artifacts" 与顶层 Makefile，填「产物映射表」（模板见下），重点分清 `boot.bin / boot.dfu / boot.frm / uboot-env.dfu / pluto.dfu / pluto.frm / pluto.itb` 的包含内容与用途边界。
- [ ] T0.3 从 Makefile 逆推三条关键依赖链：
    - `pluto.itb`：zImage + rootfs.cpio.gz + 3 个 dtb + system_top.bit → `scripts/pluto.its` → `u-boot-xlnx/tools/mkimage`；
    - `boot.bin`：FSBL + u-boot.elf → `boot.bif` → bootgen；
    - `uboot-env.*`：`scripts/get_default_envs.sh` 提取默认环境 → `mkenvimage` → `dfu-suffix`。
- [ ] T0.4 读 `scripts/pluto.mk`（TARGET_DTS_FILES、VID/PID）与 `hdl/projects/pluto/` 文件清单（README、system_bd.tcl、system_top.v、Makefile），先登记 PL 侧 IP 与地址段，阶段 2/4 要一一对应。
- [ ] T0.5 对照 README 构建前置（Vivado、经 buildroot 的 Linaro toolchain、dfu-util、device-tree-compiler 等），在 WSL 里确认哪些能跑、哪些还缺。
- [ ] T0.6 收尾：建 / 更新「仓库-plutosdr-fw」地图笔记；画一张「源码 → 构建产物 → 烧录/启动链」图。

**产物映射表（自己补全后收进仓库地图笔记）**

| 产物 | 包含 | 构建入口 | 用途 |
| --- | --- | --- | --- |
| `build/boot.bin` | FSBL + u-boot.elf | 见 Makefile 的 `build/boot.bin` 目标 | 早期启动镜像（Zynq BootROM 之后） |
| `build/boot.dfu` / `boot.frm` | 同上（+环境，frm 用于 MSD） | DFU 目标 | 更新 u-boot 本身 |
| `build/uboot-env.dfu` | u-boot 默认环境 | `mkenvimage` + `dfu-suffix` | 更新默认环境 |
| `build/pluto.itb` | fpga bitstream + zImage + ramdisk + 3 个 dtb | `mkimage -f scripts/pluto.its` | 主固件：先 FPGA 后 Linux |
| `build/pluto.dfu` / `pluto.frm` | pluto.itb（frm 附带 md5） | DFU / MSD 打包 | 用户升级固件 |

**完成标准**
- [ ] 能不看文档解释每份产物的组成与边界；能指出“先 FPGA、后内核”的顺序定义在 `scripts/pluto.its`。

### 阶段 1：u-boot 启动与 FIT

**学完能回答的问题**
1. Zynq 复位后 BootROM → FSBL → u-boot → 内核，各段做什么；bitstream 是谁、在什么时候加载？
2. `pluto.its` 的 images / configurations 怎么读？`bootm ${fit_load_address}#${fit_config}` 实际做了什么？
3. `uboot-env.txt / uboot-env.dfu` 从哪来、和默认环境怎么关联？

**任务清单**
- [ ] T1.1 先做不依赖源码的部分：精读顶层 `scripts/pluto.its`，逐 image 注释：`fpga@1`（type=fpga、load=`0xF000000`）→ `linux_kernel@1`（load/entry=`0x8000`）→ `fdt@1..3`（三块硬件版本）→ `ramdisk@1`；configuration 决定默认选哪组 fdt。注意该文件里多个 configuration 共用同一 fpga+kernel+ramdisk，只换 fdt。
- [ ] T1.2（u-boot init 后）读 `configs/zynq_pluto_defconfig`，找 `CONFIG_FIT`、`CONFIG_BOOTCOMMAND`、`CONFIG_SYS_CONFIG_NAME` 等开关；AD pluto 分支的板级配置实际经 `include/configs/zynq_zc70x.h` 引入 `include/configs/zynq-common.h`，不是单独一个 `zynq_pluto.h`。
- [ ] T1.3 在 `zynq-common.h` 的 `CONFIG_EXTRA_ENV_SETTINGS` 里做「环境变量 → 作用 → 用它的命令」表，重点：`fit_load_address`、`fit_config`、`fit_size`、`modeboot`、`bootargs`、`dfu_alt_info`、`fdt_high/initrd_high`。
- [ ] T1.4 找出并比较 boot 路径：`ramboot_verbose`（DFU 拷 RAM）、`qspiboot(_verbose)`（从 QSPI 读 ITB）、`usbboot`（传统 uImage，作对照）、`dfu_sf`（失败兜底进 DFU）。
- [ ] T1.5 理解 `adi_loadvals_pluto`：启动前用 `fdt set / fdt rm` 改设备树（refclk、model、attr、mode），再 `bootm`——这是「u-boot 改 DT → 内核看到」的真实例子，给阶段 2 打伏笔。
- [ ] T1.6 追 uboot-env 生成链：`get_default_envs.sh`（objcopy 提取 `.rodata.default_environment`）→ txt → `mkenvimage` → bin → DFU。

**练习 / 产出**
- [ ] 「学习-u-boot-启动与FIT」笔记：启动链图、`pluto.its` 逐段注释、环境变量表。
- [ ] 口头能解释 `bootm ${fit_load_address}#${fit_config}` 的每个部分。

**完成标准**
- [ ] 能回答：bitstream 在哪个阶段、由谁、从哪个地址加载；只换 FPGA 版本时，改 `pluto.its` 还是改 dtb？

### 阶段 2：Linux 内核启动与设备树

**学完能回答的问题**
1. u-boot 怎么把控制权交给内核；内核从哪里知道“板上有什么硬件”？
2. dts / dtsi / dtb、compatible、phandle、reg、chosen 分别指什么？
3. `zynq-pluto-sdr.dts/.dtsi` 里的 ad9361、DMA、串口节点，如何与 HDL 工程 IP 一一对应？
4. Linux 的 bus / device / driver 怎么通过 compatible 走到 probe？

**任务清单**
- [ ] T2.1 背景速读：u-boot 设 `bootargs`；ARM 启动时把 DT 地址交给内核并 unflatten；只读到能解释 `chosen/bootargs/stdout-path` 即可，不追内核早期汇编。材料：内核 `Documentation/devicetree/usage-model.txt`、devicetree.org 规范。
- [ ] T2.2 语法与工具：会用 `dtc -I dts -O dtb` 编译；能读 dtsi 的 `/include/` 与覆盖写法；能解释 `#address-cells/#size-cells`、`reg`、`phandle/&label`、`interrupts`、`clocks`。
- [ ] T2.3（源码就绪后）读 `linux/arch/arm/boot/dts/zynq-pluto-sdr.dts` + `.dtsi`，对照 `hdl/projects/pluto/system_bd.tcl` 的 IP：地址/中断是否与 dtsi 的 `fpga_axi` 节点一致（实测见 `dma@7c400000`、`dma@7c420000`、`cf-ad9361-lpc@79020000`、`cf-ad9361-dds-core-lpc@79024000`）。
- [ ] T2.4 建关键节点表：SPI 下 `ad9361-phy@0`（`adi,ad9363a`）、RX 数据通路 `cf-ad9361-lpc`、TX `cf-ad9361-dds-core-lpc`、`rx_dma/tx_dma`（`adi,axi-dmac-1.00.a`）、`chosen`。这张表是阶段 3/4 的入口。
- [ ] T2.5 设备模型骨架：`drivers/of/`（解析）、`drivers/base/dd.c`（probe / deferred probe）、platform bus 与 `of_platform`。目标只是能画“compatible → driver 匹配 → probe”。
- [ ] T2.6 可选（上板后）：`ls /sys/firmware/devicetree/base/`、`/proc/device-tree` 与 boot log 的 `Machine model:` 互相验证。

**练习 / 产出**
- [ ] 「概念-设备树与平台设备」：语法小抄 + 术语表。
- [ ] “HDL IP ↔ dts 节点 ↔ compatible ↔ 基址/中断”对照表。

**完成标准**
- [ ] 能对着 `zynq-pluto-sdr.dtsi` 说出内核为什么知道板上有 AD9363、两路 AXI DMA、串口在哪。

### 阶段 3：设备驱动与 IIO 框架

**学完能回答的问题**
1. Linux 驱动“注册 → 匹配 → probe → remove”的骨架是什么？`module_init` / `platform_driver` 怎么组织？
2. ad9361（RF 控制）和 cf_axi_adc / cf_axi_dds（数据通路）为什么分成两类驱动？各注册成什么？
3. IIO 的 device / channel / buffer / trigger 分别对应 Pluto 里的什么？

**任务清单**
- [ ] T3.1 先完成 T 线地基 T1/T2/T3：写完 hello 模块的加载/卸载闭环，用 QEMU+GDB 断住自己的 `open`/`read`；再读一个简单 IIO 驱动（如 `xilinx-xadc`）建立「chan_spec → sysfs → iio_dev」手感，最后进 ad9361。
- [ ] T3.2 已按锁定 commit 核对 `drivers/iio/adc/` 文件组织：ad9361 主源是 `ad9361.c`，与 `ad9361_conv.c` 合成 `ad9361_drv`；RX 数据通路是 `cf_axi_adc_core.c`（编成 `cf_axi_adc`）；TX 数据通路是 `drivers/iio/frequency/cf_axi_dds.c`（不是 `drivers/iio/dac/`）。
- [ ] T3.3 给 ad9361 驱动做“入口函数地图”：probe（SPI、时钟、校准）、`iio_info`、`iio_chan_spec` 数组、属性读写、调试接口。文件很大，用 `rg` / ctags 追主干，不顺序通读。
- [ ] T3.4 回答“控制面 vs 数据面”：`ad9361-phy` 管 RF 参数（频率 / 增益 / 滤波 / 校准 / 状态机）；`cf-ad9361-lpc` 管样本流（对接 DMA 与 IIO buffer）；两者靠 dtsi 的 `spibus-connected` 这类属性建立关系。在 `cf_axi_adc_core.c` 的 probe 与 IIO 注册处验证。
- [ ] T3.5 IIO 抽象：iio_dev / channel / attribute、buffer 与 trigger 的分工；材料：内核 `Documentation/driver-api/iio/` 或 docs.kernel.org/driver-api/iio/。先能说出“样本从哪进 buffer、trigger 干嘛用”。
- [ ] T3.6 用户态对照：读 ADI libiio 文档 / 仓库，弄清 `iio_context / iio_device / iio_channel / iio_buffer` 与内核 sysfs、字符设备、mmap 的关系（mmap 细节留给阶段 4）。
- [ ] T3.7 动态验证：在 T3 的 QEMU+GDB 环境里断住 `ad9361_probe` 与 `axiadc_probe`，观察 SPI 侧先 set drvdata、platform 侧再 `to_converter()` 的握手顺序（对照 [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]）。

**练习 / 产出**
- [ ] 「学习-Linux-驱动开发-从框架到IIO」：入口函数地图 + 控制面/数据面拆分图。
- [ ] 能解释：ad9361 为什么注册 IIO 设备而不是普通字符设备；sysfs 里的频率 / 增益属性对应哪个 channel。
- [x] 已沉淀详细调用流程：[[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]（dtsi → SPI/platform 匹配 → ad9361_probe → converter 握手 → cf_axi_adc → IIO DMA buffer）

**完成标准**
- [ ] 能画出 ad9361 与 cf_axi_adc 的注册链（compatible → of_match → probe → `iio_device_register`），并指出 IIO buffer 与阶段 4 DMA 的接缝。

### 阶段 4：DMA 与数据通路

**学完能回答的问题**
1. 样本从 AD9363 / FPGA 到 DDR、再到用户态，经过哪些模块？每段是数据面还是控制面？
2. HDL 的 `axi_dmac` 参数与内核 `dma-axi-dmac` 驱动各承担什么？
3. “cyclic DMA”为什么适合 SDR？Pluto 的 RX / TX 哪个用 cyclic，为什么？

**任务清单**
- [ ] T4.1 HDL 侧（本地已有源码）：读 `hdl/projects/pluto/system_bd.tcl` 的 DMA 实例参数。2026-09-09 实测：
    - RX `axi_ad9361_adc_dma`：`DMA_TYPE_SRC=2`、`DMA_TYPE_DEST=0`、`CYCLIC=0`；
    - TX `axi_ad9361_dac_dma`：`DMA_TYPE_SRC=0`、`DMA_TYPE_DEST=1`、`CYCLIC=1`；
    - 数据宽度 64、`SYNC_TRANSFER_START=1`，TX 还接到 `axi_tdd_0` 的 sync。
    - 取值含义可在 `hdl/library/axi_dmac/axi_dmac.v` 的 localparam 找（本地新版 HDL：0=AXI-MM、1=AXI-Stream、2=FIFO）；对照 dtsi 的 `adi,*-bus-type` 时注意 HDL 与内核/设备树可能来自不同版本，先以本仓库锁定 commit 为准。
- [ ] T4.2 数据组织：对照 dtsi 里 `dma@7c400000`（RX）/ `dma@7c420000`（TX）的 `adi,source/destination-bus-type` 与 `adi,cyclic`，把「HDL 参数 ↔ dts 属性 ↔ 驱动行为」对上。
- [ ] T4.3 内核 DMA 框架：docs.kernel.org 的 driver-api/dmaengine 与 core-api/dma-api；分清 provider / consumer、`dma_request_chan`、`dmaengine_prep_dma_*`、`dma_async_issue_pending`、完成回调；再看 `dma-axi-dmac.c` 怎么实现 provider。
- [ ] T4.4（源码就绪后）在 `cf_axi_adc_core.c` 找 consumer 侧：怎么申请 DMA channel、怎么准备 buffer/cyclic、中断完成后怎么让 IIO buffer 可读。
- [ ] T4.5 用户态 mmap / 零拷贝：libiio buffer 的 `iio_buffer_refill` / mmap；理解“DMA 写 DDR → IIO buffer → mmap 映射给应用”这条不经过用户态 memcpy 的路径。
- [ ] T4.6 画通路图：AD9363 → `axi_ad9361`（LVDS/CMOS）→ 抽取 / FIFO / cpack → `axi_ad9361_adc_dma` → DDR → `cf_axi_adc` IIO buffer → mmap / libiio；TX 反向同理。

**练习 / 产出**
- [ ] 「概念-DMA与零拷贝」：dmaengine API、cyclic 语义、mmap 链路。
- [ ] 端到端通路图（阶段 6 复用）。

**完成标准**
- [ ] 能指着 system_bd.tcl 与 dtsi 说明 RX/TX DMA 各做什么、TX 为什么配 `CYCLIC`；能画出到用户态的整条路径。

### 阶段 5：中断与内核并发

**学完能回答的问题**
1. PL 的中断怎么进 CPU（GIC / IRQ_F2P），dtsi 的 `interrupts` 三元组怎么写？
2. Linux 里“中断 → 延迟处理 → 唤醒用户态”的常用路径有哪些？和 RTOS 的 ISR → 队列 → 任务怎么对照？
3. 自旋锁 / 互斥锁各在什么场景用，驱动里哪些临界区需要锁？

**任务清单**
- [ ] T5.1 对照 dtsi：`interrupts = <0 57 0>` 这类三元组与 `system_bd.tcl` 的 `ad_cpu_interrupt …` / IRQ_F2P 连接怎么对上。
- [ ] T5.2 学中断 API 图谱：`request_irq` / `request_threaded_irq`、硬中断 top-half、threaded IRQ、workqueue、waitqueue；对照 RTOS 块计划产出的「学习-RTOS-中断与临界区」（ISR → `xQueueSendFromISR` → 任务）。
- [ ] T5.3（源码就绪后）精读 `dma-axi-dmac.c`：IRQ handler、完成回调、保护 descriptor 链的锁；标出哪些在中断上下文、哪些推到回调 / 线程做。
- [ ] T5.4 并发原语怎么选：spinlock（中断 / 短临界区）、`spin_lock_irqsave`、mutex（可睡眠 / 长临界区）、原子变量；可顺带了解 lockdep。
- [ ] T5.5 画时间线：DMA 完成中断 → provider 回调 → cf_axi_adc 更新 IIO buffer → wake_up → 用户态 `read/poll/epoll` 返回；与 FreeRTOS 路径并排。

**练习 / 产出**
- [ ] 「学习-中断与并发-Linux vs RTOS」笔记 + 对照图。

**完成标准**
- [ ] 能讲清“中断上下文里只能做什么”，并用同一张图对比 RTOS 的队列唤醒方式。

### 阶段 6：综合实践（可选进阶）

**学完能回答的问题**
1. 一条真实 IQ 流从天线到应用层经过哪些交接点，延迟 / 拷贝 / 同步各由谁负责？
2. 想在 srsRAN / OAI 里接 Pluto 这类设备，radio 层要提供什么（采样率、样本格式、时间戳、时序）？
3. Linux 与 RTOS 在“数据到达 → 处理”上的分工差异，哪里是实时性关键路径？

**任务清单（按硬件条件选做）**
- [ ] T6.1 有板：按 ADI wiki "Building the image" 构建并烧 `pluto.dfu` / `pluto.frm`；用 libiio 例子或 `iio_readdev` 收一段 IQ，验证阶段 4 的通路图。
- [ ] T6.2 有板：改 dts / 驱动后看 `dmesg`、`/sys/bus/iio/devices/`、debugfs，确认 probe 与 buffer 行为。
- [ ] T6.3 无板（当前 WSL 环境）：把阶段 0–5 的图、笔记、Journal 串成一次“纸上端到端”：pluto.its 启动顺序 → dts → 驱动 probe → DMA → libiio。
- [ ] T6.4 对照 RAN：读 srsRAN / OAI 的 radio / RU 抽象（IIO / UHD / Soapy 等后端思路），标出采样率、IQ 格式、帧定时从哪来；产出「嵌入 Linux 视角看 RAN 数据通路」小结。

**完成标准**
- [ ] 有一张覆盖阶段 0–5 的端到端图；在 Journal 记下仍模糊的环节，转成新疑问。

### 实测与勘误（2026-09-09，WSL）

- Linux 子模块锁定 commit（外层 `git submodule status`）：`f3da30df…`；该 commit 下 `drivers/iio/adc/` 实际组织与早期笔记不完全一致，init 后请再校对：
    - `cf_axi_adc`：源码是 `cf_axi_adc_core.c`（编成 `cf_axi_adc`），不是单文件 `cf_axi_adc.c`；
    - `ad9361`：主源 `ad9361.c` + `ad9361_conv.c`，合成 `ad9361_drv`；
    - TX DDS：`drivers/iio/frequency/cf_axi_dds.c`，不是 `drivers/iio/dac/cf_axi_dds.c`；
    - DMA 驱动：`drivers/dma/dma-axi-dmac.c`（编成 `dma-axi-dmac`），不是 `axi-dmac.c`。
- u-boot：pluto defconfig 在 `configs/zynq_pluto_defconfig`，板级配置经 `include/configs/zynq_zc70x.h` 引入 `include/configs/zynq-common.h`；默认环境与 boot 命令定义都在 `zynq-common.h`。
- 顶层现状（已处理）：`hdl`、`linux`、`u-boot-xlnx`、`buildroot` 已于 2026-09-09 按锁定 commit 完成初始化；镜像远端统一为 ghfast.top，后续更新不需要 VPN。
- 本机 GitHub 直连不可用（2026-09-09 实测）；`ghfast.top` / `gh-proxy.com` 镜像可走 git 与 raw，详见待办中的初始化命令。

## 每个阶段的收尾动作（沿用通信学习习惯）

1. 建「学习-<主题>」笔记并勾选进度；
2. 关键概念沉淀为「概念-<主题>」笔记并互链；
3. 代码锚点记录到文件 / 函数 / 行；
4. 复盘写入当日 `50-Journal`；
5. 更新本清单与 [[MOC-Linux]]。

## 学习进度

**执行版进度（以此为准）**

- [x] 阶段 0：环境与源码地图
- [x] 阶段 1：最小驱动闭环 → [[学习-Linux-阶段1-最小驱动闭环]]
- [ ] 阶段 2：QEMU+GDB 动态调试
- [ ] 阶段 3：设备模型与总线匹配
- [ ] 阶段 4：Pluto 构建与启动链
- [ ] 阶段 5：控制面驱动与 IIO（ad9361）——静态深读已完成并沉淀为 [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]，余 xilinx-xadc 热身 + QEMU 动态断点验证
- [ ] 阶段 6：数据面与用户态（cf_axi_adc / DMA / libiio）
- [ ] 阶段 7：中断、并发与实时性
- [ ] 阶段 8：综合实践与 RAN 映射

**详细拆分进度（T/P，作为细项参考）**

**T 线：通用内核地基**

- [ ] T0：源码地图与阅读工具
- [x] T1：最小模块闭环
- [x] T2：字符 / 杂项设备
- [ ] T3：QEMU+GDB 动态调试
- [ ] T4：对照内核自带驱动
- [ ] T5：设备模型
- [ ] T6：真实子系统（建议 IIO）

**P 线：Pluto 真实链路**

- [ ] 阶段 0：全景与仓库地图
- [ ] 阶段 1：u-boot 启动与 FIT
- [ ] 阶段 2：内核启动与设备树
- [ ] 阶段 3：设备驱动与 IIO 框架
- [ ] 阶段 4：DMA 与数据通路
- [ ] 阶段 5：中断与内核并发
- [ ] 阶段 6：综合实践（可选）

## 待办 / 疑问

- [x] 初始化 `plutosdr-fw` 四个子模块（hdl / linux / u-boot-xlnx / buildroot）——2026-09-09 已通过 ghfast.top 镜像完成，均检出到锁定 commit
- [ ] 子模块 init 后：按「实测与勘误」逐条校对 `drivers/iio/adc/`、`drivers/dma/`、u-boot 配置的实际锚点并更新本笔记
- [x] `hdl/` 已重拉为正规 submodule（旧未管理内容备份在仓库外 `_plutosdr_submodule_backup_20260909/`）
- [ ] 是否有 PlutoSDR / Zynq 板可做端到端验证（决定 DMA 与用户态阶段能否上板）
- [ ] 资料收藏：是否把 kernel / u-boot 官方文档入口收进「参考网站」目录，方便引用
- [ ] T 线环境：WSL 补齐 flex / bison 等内核构建依赖；搭好 QEMU+GDB（`osmten/qemu-kernel-dbg` 或手工），确保能断住自己写的 `open`/`read`
- [x] 执行版阶段 0：补 WSL 依赖 → 搭 QEMU+GDB → 建源码地图 + plutosdr-fw 产物链图；成果见 [[学习-Linux-阶段0-源码地图与调试环境]]
- [x] 执行版阶段 1：最小驱动闭环（hello 模块 + misc 字符设备 + VFS 调用链）→ [[学习-Linux-阶段1-最小驱动闭环]]
- [ ] T 线版本策略：另备一份接近 mainline 6.x 的内核源码配合 elixir / docs.kernel.org 学通用机制；P 线继续用 plutosdr-fw `linux @ f3da30df`，避免行号混淆
- [ ] T4 / T6 选型：对照驱动先选一个 `drivers/char/` 简单驱动 + `xilinx-xadc`；子系统建议先 IIO，USB 作为第二

新环境 / 需要重拉时使用（本机 GitHub 直连不可用；2026-09-09 已完成过一次，子模块远端也已统一为 ghfast.top 镜像）：

```bash
git -c submodule.linux.url=https://ghfast.top/https://github.com/analogdevicesinc/linux \
    -c submodule.u-boot-xlnx.url=https://ghfast.top/https://github.com/analogdevicesinc/u-boot-xlnx.git \
    -c submodule.buildroot.url=https://ghfast.top/https://github.com/analogdevicesinc/buildroot.git \
    submodule update --init linux u-boot-xlnx buildroot
```

注意：`u-boot-xlnx/` 当前是半初始化状态，若上述命令因目录状态失败，先 `git -C u-boot-xlnx status` 查看再决定处理方式，不要直接删除。

## 关联

- [[MOC-Linux]]（模块主页）
- [[学习-Linux-内核源码阅读与驱动学习法]]（T 线方法与资源）
- [[学习-Linux-阶段0-源码地图与调试环境]]（阶段 0 成果与复现命令）
- [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]（阶段 3 详细调用流程）
- [[书籍-Linux内核设计与实现（LKD）]]（概念书，配合阶段 0–3 阅读）
- [[MOC-RTOS]]（平行对照块）
- [[MOC-FPGA]]、[[MOC-射频]]、[[MOC-O-RAN开源]]、[[MOC-C++与软件]]
- [[领域-L1物理层]]
- [[Home]]
