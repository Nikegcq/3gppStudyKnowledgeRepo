---
type: resource
tags: [Linux, 嵌入式, 内核, 驱动开发, QEMU, GDB, 学习计划]
created: 2026-09-10
updated: 2026-09-10
status: active
source: GitHub 内核学习资源 + 本地 plutosdr-fw/linux
repo: /home/congqiang/work/repo/plutosdr-fw
---

# 学习：Linux 内核源码阅读与驱动学习法（T 线）

## 一句话总结

把“会在命令行里用 Linux”升级为“能拆 Linux 内核源码”：先建源码树地图，再写一个最小模块跑通加载/卸载闭环，接着用 QEMU+GDB 把静态阅读变成动态调试，最后沿设备模型向真实子系统延伸。方法本身是通用的（T 线）；本仓库把它落在 PlutoSDR/AD9361 这条真实链路（P 线，见 [[学习-Linux-学习路线]]）上。

## 1 源码树地图：先记职责，不背细节

| 目录 | 职责 | 与驱动的关系 |
| --- | --- | --- |
| `arch/` | 体系结构相关（`arm/`、`arm64/`、`x86/`） | 板级初始化、中断控制器、`of_platform_populate` 等调用点 |
| `drivers/` | 所有设备驱动，主战场 | 按 `char/`、`block/`、`net/`、`iio/`、`spi/`、`usb/` 等分类 |
| `fs/` | 文件系统与 VFS | 字符设备的 `file_operations` 最终被 VFS 调用 |
| `kernel/` | 调度、时间、中断、模块加载等核心 | `module_init`、`do_initcalls`、中断线程化等机制 |
| `mm/` | 内存管理 | `kmalloc`、`vmalloc`、`mmap`、DMA 映射的底层 |
| `include/` | 内核头文件 | `#include <linux/...>` 的源头 |
| `init/` | 内核启动入口 | `start_kernel()` 在 `init/main.c` |
| `lib/` | 通用库函数（`printk`、`kfifo` 等） | 驱动常用的基础设施 |
| `Documentation/` | 内核自带文档 | `driver-api/`、`devicetree/` 是驱动学习的官方材料 |

阅读工具与用法：

- 在线交叉引用：https://elixir.bootlin.com/linux/latest/source （查函数定义、引用、结构体成员最快）。
- 本地索引：cscope / ctags / `rg`。建议对 `linux/` 建一次 cscope 数据库，查 `->probe`、`of_match_table` 这类符号很快。
- 导航三步法：**先找入口函数（probe / init）→ 再找结构体定义 → 最后找回调注册点**。不要按文件顺序通读。

## 2 最小模块闭环：先跑通，再理解

目标：亲手完成“编写 → 编译 → `insmod` → 看 `dmesg` → `rmmod`”。最小骨架（只保留结构，实际练习时自己敲一遍）：

```c
#include <linux/module.h>
#include <linux/kernel.h>

static int __init hello_init(void)
{
	pr_info("hello: loaded\n");
	return 0;
}

static void __exit hello_exit(void)
{
	pr_info("hello: unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);
MODULE_LICENSE("GPL");
```

Makefile 骨架（`KDIR` 指向目标内核，可为本地 `linux` 源码）：

```make
obj-m += hello.o
KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	make -C $(KDIR) M=$(PWD) modules
clean:
	make -C $(KDIR) M=$(PWD) clean
```

要拆的点：

- `module_init` / `module_exit` 在 `include/linux/module.h`，展开后涉及模块加载系统调用与 initcall 机制；入口函数在模块插入时被调用，不是进程概念里的 `main`。
- `MODULE_LICENSE` 决定是否使用 GPL-only 符号；`insmod`/`modprobe`、`lsmod`、`dmesg -w`、`rmmod` 是最小闭环工具。

## 3 从系统调用到驱动：`file_operations` 这条链

用户态 `read()` 进内核后，大致路径是：

```text
read() 系统调用 → ksys_read() → vfs_read() → file->f_op->read / read_iter
                                             ↑
                                 驱动注册的 struct file_operations
```

对照阅读：

- `include/linux/fs.h` 的 `struct file_operations`：驱动暴露给 VFS 的函数表（`open/read/write/release/poll/mmap/ioctl` 等）。
- `fs/read_write.c` 的 `vfs_read()`：VFS 如何检查权限、取 `file->f_op` 并调用驱动回调。
- `drivers/char/misc.c`：misc 设备框架，展示了 `file_operations` 如何被注册与转发；可以作为从 hello 模块过渡到真实字符驱动的第一站。

从 hello 到“像样的字符设备”，要补四个模式：

1. **自动创建设备节点**：`class_create()` + `device_create()`，而不是手动 `mknod`。
2. **用户/内核数据拷贝**：`copy_to_user()` / `copy_from_user()`，不能直接解引用用户指针。
3. **私有数据**：`file->private_data` 保存设备结构体指针，配合 `container_of()` 从内嵌成员反推外层结构体。
4. **并发保护**：字符设备被多个进程同时 open 时，用 `mutex` 或 `spinlock` 保护共享状态。

练习：写成 `drivers/char` 里的一个 misc 设备，用户态 `cat`/`echo` 触发读写，`dmesg` 看路径；然后改成用 `private_data + container_of` 的版本。

## 4 QEMU + GDB：把“看代码”变成“停下来看”

`printk` 只能看到发生了什么；GDB 断点能让你停在 `open`/`read`/`probe` 里逐行走。推荐环境：

- https://github.com/osmten/qemu-kernel-dbg （脚本化完成内核下载、编译、rootfs、QEMU 启动和 GDB 连接）
- 需要的内核配置：`CONFIG_DEBUG_INFO`、`CONFIG_GDB_SCRIPTS`、`CONFIG_DEBUG_INFO_DWARF4` 等（按项目说明）。

本机已搭好一套无 sudo 的可用环境（QEMU 6.2 + GDB 12.1 + 6.1 调试内核），复现命令与实测证据见 [[学习-Linux-阶段0-源码地图与调试环境]]。

最小调试流程：

1. 启动 QEMU（带 `-s -S`，等待 GDB）；
2. `gdb vmlinux` → `target remote :1234`；
3. 在 `start_kernel`、`do_initcalls` 打断点，观察启动流程；
4. 加载自己的模块后，对 `hello_init`、`hello_open`、`hello_read` 打断点，用用户态程序触发并单步；
5. 进入 P 线后，同样可以对 `ad9361_probe`、`axiadc_probe`、`iio_device_register` 打断点，动态核对调用链（见 [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]）。

注意：WSL 里目前缺少 `flex`/`bison` 等内核构建依赖，需要先补齐；QEMU/GDB 环境建议单独建目录，不要污染 plutosdr-fw 工程。

## 5 对照内核自带驱动：模仿是最好的入门

完成 hello 闭环后，立即找内核里的“同类但完整”驱动对照：

- `drivers/char/misc.c`：misc 设备框架本身的实现。
- `drivers/char/` 下选择一个简单 misc 驱动，观察它如何处理 `open/read/write`、`copy_*_user`、`class_create/device_create`。
- `drivers/iio/adc/xilinx-xadc.c`：比 ad9361 小得多的 IIO 驱动，适合先建立 `iio_dev → channels → sysfs` 的直觉，再进 P 线阶段 3。

方法：先对照骨架写出“差异点清单”，再在自己的驱动里模仿；每改一次就编译、加载、观察行为。

## 6 设备模型：从“字符设备”上到“总线-设备-驱动”

真实硬件驱动运行在设备模型之上。阅读顺序建议：

- `drivers/base/bus.c`：`bus_register()`。
- `drivers/base/dd.c`：`device_register()`、`driver_register()`、`really_probe()`、`-EPROBE_DEFER`。
- `drivers/base/platform.c`：`platform_match()`、`of_driver_match_device()`。
- `drivers/of/platform.c`：DT 节点如何被 populate 成 platform device。

验收：能画出“DT node → device → bus match → driver.probe”的通用链路，并能说出 SPI 与 platform 总线匹配方式的不同（P 线阶段 2/3 的实例见 AD9361 笔记）。

## 7 延伸到真实子系统：T6 选型

设备模型之后，选一条子系统纵向深入（与 P 线对齐选效果最好）：

| 选项 | 入口 | 与 P 线的衔接 |
| --- | --- | --- |
| IIO | `drivers/iio/industrialio-core.c`、`drivers/iio/adc/` | 直接服务 P 线阶段 3/4（ad9361、cf_axi_adc） |
| SPI | `drivers/spi/spi.c`（匹配、modalias、`of_register_spi_devices`） | 服务 P 线阶段 1/3（AD9361 是 SPI 设备） |
| USB char | `drivers/usb/core/`、`drivers/usb/class/` | 服务 Plutosdr 的 DFU、iiod over USB 的理解 |
| dmaengine | `drivers/dma/dma-axi-dmac.c`、`industrialio-buffer-dmaengine.c` | 服务 P 线阶段 4（样本流） |

建议先选 **IIO**（与现有 P 线重叠最多），USB 作为第二个子系统。

## 8 资源与用法

- `0xAX/linux-insides`：https://github.com/0xAX/linux-insides —— 读内核概念卡住时查（启动、中断、内存管理等）。
- `linux-kernel-labs-zh/docs-linux-kernel-labs-zh-cn`：https://github.com/linux-kernel-labs-zh/docs-linux-kernel-labs-zh-cn —— 带实验的内核课程，模块/驱动实验与 T1–T4 直接对应。
- `shizhengLi/linux-kernel-learning`：https://github.com/shizhengLi/linux-kernel-learning —— 结构化路线参考，适合看“阶段二：设备驱动”如何组织。
- `osmten/qemu-kernel-dbg`：https://github.com/osmten/qemu-kernel-dbg —— QEMU+GDB 调试环境。
- 《Linux 内核设计与实现（LKD）》：见 [[书籍-Linux内核设计与实现（LKD）]]——概念导览，按 T 线章节顺序配合实践。
- 本地源码：`/home/congqiang/work/repo/plutosdr-fw/linux`（P 线主线，commit `f3da30df`）。
- 在线文档：https://docs.kernel.org/driver-api/index.html 、https://elixir.bootlin.com/linux/latest/source 。

GitHub 直连在本机不可用时，克隆可加镜像前缀：`https://ghfast.top/https://github.com/<owner>/<repo>.git`。

## 9 两条线怎么配合

本仓库已把 T/P 两线合并为 [[学习-Linux-学习路线]] 顶部的「优化整合版执行路线（9 阶段）」；下面的对照表用于理解每个 T 任务在 P 线上的落点。

| T 线（通用地基） | P 线（Pluto 真实链路） |
| --- | --- |
| T0 源码地图 | P0 仓库地图（plutosdr-fw 产物链） |
| T1 最小模块闭环 | P1 u-boot/启动（先建立“读入口函数”的手感） |
| T2 字符/杂项设备 | P2 设备树与 platform 匹配 |
| T3 QEMU+GDB | 动态验证 P1/P2/P3 的调用链 |
| T4 对照自带驱动 | P3 ad9361 + cf_axi_adc 的对照阅读 |
| T5 设备模型 | P2/P3 的机制层 |
| T6 真实子系统（IIO） | P3–P6 的纵深化 |

推荐顺序：**T0 → T1 → T3（先能断点）→ P0/P1/P2 → T2/T4/T5（与 P3 并行）→ P3–P5 → T6/P6**。

## 关联

- [[学习-Linux-学习路线]]（P 线主清单，含 T 线穿插顺序）
- [[学习-Linux-驱动开发-AD9361-从dtsi到驱动调用流程]]（T5/T6 的真实案例）
- [[MOC-Linux]]
