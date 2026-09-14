---
type: resource
tags: [Linux, 嵌入式, 内核, QEMU, GDB, 源码地图, 调试环境]
created: 2026-09-10
updated: 2026-09-10
status: active
source: plutosdr-fw linux 6.1.0-gf3da30df6004
repo: /home/congqiang/work/repo/plutosdr-fw
---

# 学习：Linux 阶段 0 —— 源码地图与 QEMU+GDB 调试环境

## 一句话总结

执行版阶段 0 已完成：在 WSL 里用**无 sudo 的用户态工具链**搭起了可断点调试的 x86_64 内核环境（QEMU 6.2 + GDB 12.1 + 6.1 内核），GDB 已实测断在 `start_kernel`，QEMU 已实测跑到用户态 initramfs 并正常关机；同时产出了 plutosdr-fw 的源码地图与构建产物链。

## 1 完成清单

- [x] WSL 构建依赖：`flex` / `bison` / `bc` / `libelf-dev` 用户态解包可用（不需要 sudo）。
- [x] QEMU/GDB：`qemu-system-x86_64 6.2.0`、`gdb 12.1` 可用，TCG 加速器模块路径已配置。
- [x] 调试内核：用本地 6.1 源码独立构建 `bzImage` + `vmlinux`（DWARF4 调试信息 + GDB scripts，关闭 KASLR/ORC）。
- [x] initramfs：静态 busybox，挂载 proc/sys/dev，打印启动信息后自动关机。
- [x] 动态验证：GDB 断在 `init/main.c:937 start_kernel`，QEMU 串口打印 `INITRAMFS_OK` / `USERSPACE_READY` 后 `Power down`。
- [x] 源码地图：内核顶层目录职责 + plutosdr-fw 关键代码锚点（见第 5 节）。
- [x] 产物链：源码组件 → 构建 → 产物 → 运行时启动链（见第 6 节）。

## 2 环境总览

| 项 | 值 |
| --- | --- |
| 发行版 | Ubuntu 22.04.5 LTS（WSL2） |
| CPU/内存/磁盘 | 8 vCPU / 15 GiB / 根分区约 527 GiB 可用 |
| 内核源码 | `/home/congqiang/work/repo/plutosdr-fw/linux`（6.1.0-gf3da30df6004） |
| Lab 根目录 | `/home/congqiang/work/repo/tools/kernel-lab`（约 2.6 GiB） |
| 内核构建目录 | `$LAB_ROOT/build/linux-x86_64`（约 2.5 GiB） |
| QEMU / GDB / flex / bison / bc | 6.2.0 / 12.1 / 2.6.4 / 3.8.2 / 1.07.1 |
| 关键产物 | `bzImage` 9.8 MiB、`vmlinux` 356 MiB、`initramfs.cpio.gz` 1.1 MiB |

为什么不用 sudo：本机 `sudo` 需要密码，因此把 apt 包下载后 `dpkg-deb -x` 解包到
`$LAB_ROOT/root`，再通过环境变量注入：

- `PATH`：`$LAB_ROOT/root/usr/bin`
- `LD_LIBRARY_PATH`：`$LAB_ROOT/root/usr/lib/x86_64-linux-gnu`
- `CPATH` / `LIBRARY_PATH`：给 objtool 用 libelf 头/库
- `BISON_PKGDATADIR`：bison 的数据文件
- `QEMU_MODULE_DIR`：QEMU 的 `accel-tcg-x86_64.so` 等模块

## 3 复现命令

脚本已固化到 `plutosdr-fw/kernel-lab/`（2026-09-11 从知识库迁入 WSL）：

```bash
cd /home/congqiang/work/repo/plutosdr-fw
export LAB=/home/congqiang/work/repo/plutosdr-fw/kernel-lab

source $LAB/env.sh
bash $LAB/make_initramfs.sh
bash $LAB/run_qemu_gdb_demo.sh
```

直接进入 QEMU 交互 shell（推荐日常使用）：

```bash
source $LAB/env.sh
bash $LAB/run_qemu.sh            # 直接启动，同时开放 GDB stub :1234
# 另开终端：bash $LAB/attach_gdb.sh
# 想先停在启动前：PAUSE=1 bash $LAB/run_qemu.sh
# 退出 QEMU：Ctrl-A 再按 X；或在 guest 里 poweroff -f
```

本机实测：进入 guest 后 `uname -a` 返回 `Linux (none) 6.1.0-gf3da30df6004`，
`cat /proc/cmdline` 可见 `nokaslr rdinit=/init debugshell`；`poweroff -f` 后正常回到宿主。

构建内核（已执行过一次，重装环境时才需要）：

```bash
source $LAB/env.sh
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 defconfig
"$KERNEL_SRC/scripts/config" --file "$KERNEL_BUILD/.config" \
    -e DEBUG_INFO_DWARF4 -e GDB_SCRIPTS \
    -d UNWINDER_ORC -e UNWINDER_FRAME_POINTER -d RANDOMIZE_BASE
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 olddefconfig
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 -j"$(nproc)" bzImage
```

## 4 实测证据

GDB 断点（`gdb.log`）：

```text
Breakpoint 1 at 0xffffffff82ae9ca4: file /home/congqiang/work/repo/plutosdr-fw/linux/init/main.c, line 937.
Thread 1 hit Breakpoint 1, start_kernel () at .../init/main.c:937
rip  0xffffffff82ae9ca4  <start_kernel>
#0  start_kernel ()
#1  x86_64_start_reservations (...) at arch/x86/kernel/head64.c:556
#2  x86_64_start_kernel (...) at arch/x86/kernel/head64.c:537
#3  secondary_startup_64 () at arch/x86/kernel/head_64.S:358
```

QEMU 串口（`serial.log`）：

```text
Run /init as init process
INITRAMFS_OK
kernel: 6.1.0-gf3da30df6004
cmdline: console=ttyS0 nokaslr rdinit=/init
USERSPACE_READY
reboot: Power down
```

这证明：内核启动 → GDB 停机/查看调用栈 → 继续运行 → 用户态 initramfs 都通了。

## 5 源码地图（阶段 0 产出版）

通用目录职责与阅读方法见 [[学习-Linux-内核源码阅读与驱动学习法]]；P 线实际代码锚点：

| 位置 | 作用 |
| --- | --- |
| `arch/arm/boot/dts/zynq-pluto-sdr*.dts/.dtsi` | Pluto 设备树：ad9361-phy、cf-ad9361-lpc、两路 AXI DMA |
| `arch/arm/mach-zynq/` | Zynq 平台初始化、SMP、SLCR |
| `drivers/iio/adc/ad9361.c` | AD9361 SPI 控制面驱动（probe 9501、IIO 注册 9634、converter 注册 9637） |
| `drivers/iio/adc/ad9361_conv.c` | AD9361 ↔ cf_axi_adc 适配层（converter 726、post_setup 647） |
| `drivers/iio/adc/cf_axi_adc_core.c` | AXI ADC 数据面（probe 1061、buffer 128、IIO 注册 1236） |
| `drivers/iio/frequency/cf_axi_dds.c` | TX DDS 数据面 |
| `drivers/dma/dma-axi-dmac.c` | AXI DMAC 的 dmaengine provider |
| `drivers/spi/spi.c`、`drivers/of/platform.c`、`drivers/base/dd.c` | SPI modalias、DT populate、driver probe 机制 |
| `init/main.c` | `start_kernel()`（本次断点位置，6.1 在 937 行） |

## 6 plutosdr-fw 构建产物链

```text
源码组件                          构建                               产物
──────────────────────────────────────────────────────────────────────────────
hdl/projects/pluto        ──(Vivado/source)──▶  system_top.bit / system_top.xsa
linux (6.1 ADI)           ──(make zImage)────▶  zImage
                          ──(dtc)────────────▶  zynq-pluto-sdr{,-revb,-revc}.dtb
u-boot-xlnx (pluto)       ──(make)───────────▶  u-boot.elf
scripts/get_default_envs.sh + mkenvimage ───▶  uboot-env.bin / uboot-env.dfu
buildroot                 ──(make)───────────▶  rootfs.cpio.gz

scripts/pluto.its + mkimage ───────────────▶  build/pluto.itb
    images: fpga@1 (load=0xF000000) + linux_kernel@1 (0x8000) + fdt@1..3 + ramdisk@1

build/sdk/fsbl/Release/fsbl.elf + u-boot.elf + boot.bif ──(bootgen)──▶ build/boot.bin
build/pluto.itb  + dfu-suffix ──▶ build/pluto.dfu    + md5 ──▶ build/pluto.frm
build/boot.bin   + uboot-env.bin ──▶ build/boot.dfu / build/boot.frm
```

运行时启动链：

```text
Zynq BootROM → FSBL → u-boot
    → bootm ${fit_load_address}#${fit_config}
    → FIT 先加载 FPGA bitstream(0xF000000)，再加载 zImage/fdt/ramdisk
    → Linux start_kernel → initramfs/rootfs → libiio / iiod 用户态
```

u-boot 环境与 FIT 细节见 [[学习-Linux-学习路线]] 详细参考 3 的阶段 1。

## 7 阶段 0 验收

- [x] 能启动 QEMU 并 attach GDB。
- [x] 能在 `start_kernel` 下断、查看寄存器与调用栈。
- [x] 能看到内核启动到用户态（initramfs）的完整日志。
- [x] 有源码地图（通用 + pluto 锚点）与产物链图。

下一步：进入执行版**阶段 1（最小驱动闭环）**或继续阶段 2 的 `do_initcalls` / 模块断点调试。

## 关联

- [[学习-Linux-学习路线]]（执行版 9 阶段）
- [[学习-Linux-内核源码阅读与驱动学习法]]（T 线方法）
- [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]（阶段 5 深读）
- [[MOC-Linux]]
