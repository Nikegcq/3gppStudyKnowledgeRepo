---
type: resource
tags: [Linux, 嵌入式, QEMU, GDB, kernel-lab, 9p, 模块, 驱动开发]
created: 2026-09-14
updated: 2026-09-14
status: active
source: plutosdr-fw kernel-lab
repo: /home/congqiang/work/repo/plutosdr-fw
---

# 学习：kernel-lab QEMU 使用流程（plutosdr-fw）

> **存档定位：** 本文只覆盖 QEMU / 9p / GDB **环境与操作**，不并入阶段 1 知识点。驱动闭环、VFS、`lab_chardev` 见 [[学习-Linux-阶段1-最小驱动闭环]]。

## 一句话总结

在 WSL 里用 QEMU + GDB 调试 x86_64 内核，并通过 **9p 共享目录** 把宿主机编译的 `.ko` 直接挂进 guest 加载——改完模块重编即可 `insmod`，不必每次重打 initramfs。代码载体是 `plutosdr-fw`，调试内核来自其 `linux` 子模块（6.1）。

## 1 目录布局

| 路径 | 用途 |
| --- | --- |
| `/home/congqiang/work/repo/plutosdr-fw/modules/` | 外部模块源码（`hello.c`、`lab_chardev.c`、`Makefile`）；9p 默认共享此目录 |
| `/home/congqiang/work/repo/plutosdr-fw/kernel-lab/` | 脚本：`env.sh`、`run_qemu.sh`、`stage1.sh`、`attach_gdb.sh`、`init` 等 |
| `/home/congqiang/work/repo/plutosdr-fw/linux` | 内核源码（调试用 x86_64 构建；Pluto 板为 ARM） |
| `/home/congqiang/work/repo/tools/kernel-lab/` | `LAB_ROOT`：QEMU/GDB 工具链、内核构建目录、initramfs、日志 |
| `knowledgeRepo/scripts/kernel-lab/` | 本知识库侧说明（脚本本体已迁入 plutosdr-fw） |

## 2 环境准备（每次新终端）

```bash
export LAB=/home/congqiang/work/repo/plutosdr-fw/kernel-lab
source $LAB/env.sh
```

`env.sh` 会设置：

- `LAB_ROOT` = `/home/congqiang/work/repo/tools/kernel-lab`
- `KERNEL_SRC` = `plutosdr-fw/linux`
- `KERNEL_BUILD` = `$LAB_ROOT/build/linux-x86_64`
- `PATH` / `LD_LIBRARY_PATH` / `QEMU_MODULE_DIR`（无 sudo 用户态工具链）

## 3 日常工作流（推荐：9p 共享）

```bash
export LAB=/home/congqiang/work/repo/plutosdr-fw/kernel-lab
source $LAB/env.sh

# 1) 编外部模块（产物落在 modules/*.ko）
bash $LAB/stage1.sh modules

# 2) 启动 QEMU（默认 SHARE=1，自动挂 9p）
bash $LAB/run_qemu.sh
```

guest 内：

```sh
# init 若已自动挂载，会看到：9P_SHARE_OK /mnt <- hostshare
ls /mnt
insmod /mnt/hello.ko
insmod /mnt/lab_chardev.ko
lsmod
cat /dev/lab0
echo hello-from-userspace > /dev/lab0
cat /dev/lab0
rmmod lab_chardev
rmmod hello
poweroff -f
```

改模块后的迭代：

```bash
# 宿主机
bash $LAB/stage1.sh modules
# guest（不必重启 QEMU）
rmmod lab_chardev
insmod /mnt/lab_chardev.ko
```

## 4 9p 共享参数

`run_qemu.sh` 默认注入：

```text
-virtfs local,path=/home/congqiang/work/repo/plutosdr-fw/modules,mount_tag=hostshare,security_model=none
```

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `SHARE` | `1` | 设为 `0` 可关闭共享 |
| `SHARE_DIR` | `plutosdr-fw/modules` | 宿主机共享目录 |
| `SHARE_TAG` | `hostshare` | guest 挂载名 |

guest 手动挂载（init 未自动挂时）：

```sh
mkdir -p /mnt
mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt
```

内核需具备：`CONFIG_NET_9P`、`CONFIG_NET_9P_VIRTIO`、`CONFIG_9P_FS`（本 lab 的 6.1 defconfig 已有）。

## 5 initramfs 方式（备选）

不走 9p 时，把 `.ko` 打进 initrd：

```bash
bash $LAB/stage1.sh modules
bash $LAB/stage1.sh pack      # 重建 initramfs.cpio.gz（含 /lib/modules/*.ko）
bash $LAB/run_qemu.sh         # 或 SHARE=0
```

guest：`insmod /lib/modules/hello.ko`

对比：

| 方式 | 优点 | 缺点 |
| --- | --- | --- |
| 9p 共享（默认） | 改 `.ko` 不用重打 initrd | 需 virtfs；guest 要能 mount 9p |
| initramfs 打包 | 启动即可见，无额外设备 | 每次改模块要 `pack` 重启 |

## 6 stage1.sh 子命令

```bash
bash $LAB/stage1.sh check     # CONFIG_MODULES / Module.symvers / busybox applets
bash $LAB/stage1.sh prepare   # modules_prepare + 从 vmlinux.symvers 恢复 Module.symvers
bash $LAB/stage1.sh modules   # make ... M=$MODDIR modules
bash $LAB/stage1.sh pack      # 重建 initramfs（可含 .ko）
bash $LAB/stage1.sh demo      # 非交互跑 insmod→cat/echo→rmmod 闭环
```

底层编译命令等价于：

```bash
make -C /home/congqiang/work/repo/plutosdr-fw/linux \
     O=/home/congqiang/work/repo/tools/kernel-lab/build/linux-x86_64 \
     ARCH=x86_64 \
     M=/home/congqiang/work/repo/plutosdr-fw/modules \
     modules
```

## 7 GDB 调试

### 7.1 启动与 attach

```bash
# 终端 A：进 guest shell（默认已带 -s，开放 TCP 1234）
bash $LAB/run_qemu.sh
# 或先暂停等 GDB：
PAUSE=1 bash $LAB/run_qemu.sh

# 终端 B
bash $LAB/attach_gdb.sh
# 自动执行：file vmlinux / target remote :1234 / break start_kernel
```

### 7.2 常用命令速查

| 命令                                     | 作用                          |
| -------------------------------------- | --------------------------- |
| `break 函数名` / `break 文件:行`             | 下断点                         |
| `break lab_read`                       | 断驱动函数（需先 `add-symbol-file`） |
| `break lab_read if count > 10`         | 条件断点                        |
| `continue` / `c`                       | 继续运行                        |
| `bt`                                   | 调用栈                         |
| `frame N`                              | 切到第 N 层栈帧                   |
| `info locals`                          | 当前帧局部变量                     |
| `print 变量` / `p *dev` / `x/s dev->buf` | 打印 / 解引用 / 按字符串看内存          |
| `list`                                 | 看源码                         |
| `next` / `n`                           | 单步（不进函数）                    |
| `step` / `s`                           | 单步（进函数）                     |
| `finish`                               | 执行到当前函数返回                   |
| `info breakpoints`                     | 列出断点（确认不是 pending）          |
| `info functions lab_`                  | 查符号是否已加载                    |
| `info registers rip`                   | 看寄存器                        |
| `delete N`                             | 删断点 N                       |
| `disconnect`                           | 断开，让 QEMU 继续跑               |
| `quit`                                 | 退出 GDB                      |

### 7.3 内核启动路径断点（阶段 0/2）

```gdb
break start_kernel
break do_initcalls
continue
bt
list
continue
```

### 7.4 调试外部模块（lab_chardev）

模块是 out-of-tree，`vmlinux` 里没有符号，需手动加载。

```sh
# 终端 A guest
insmod /mnt/lab_chardev.ko
cat /sys/module/lab_chardev/sections/.text   # 记下 .text 地址
```

```gdb
# 终端 B：地址用 guest 读到的值，不要猜
add-symbol-file /home/congqiang/work/repo/plutosdr-fw/modules/lab_chardev.ko 0xffffffffa0000000

# 函数名是 lab_ 不是 lad_（拼错会变 pending，永不命中）
break lab_read
break lab_write
break lab_open

info breakpoints    # 确认已有具体地址，不是 pending
continue
```

```sh
# guest 触发
cat /dev/lab0
echo xxx > /dev/lab0
```

命中 `lab_read` 后的预期栈：

```text
#0  lab_read
#1  vfs_read
#2  ksys_read
#3  __x64_sys_read
```

继续检查驱动状态：

```gdb
bt
list
print *file
next                      # 过 private_data 赋值
print *dev
x/s dev->buf
print dev->len
finish                    # 看返回值（拷贝字节数或 0=EOF）
```

### 7.5 命中现场注意点

`lab_read(file=..., buf=0x7fea..., count=65536, ...)` 里：

| 参数 | 可访问性 | 说明 |
| --- | --- | --- |
| `file` / `file->private_data` | 内核地址，可 `print` | 驱动私有状态 |
| `buf`（用户指针） | 常显示 `Cannot access memory` | **正常**：GDB 在内核态不能直接解引用用户地址；驱动用 `copy_to_user` 由内核拷贝 |
| `count=65536` | — | busybox `cat` 的一次 `read` 长度 |

### 7.6 一键演示

```bash
bash $LAB/run_qemu_gdb_demo.sh
```

自动断 `start_kernel` 并跑到用户态。日志：`$LAB_ROOT/gdb.log`、`$LAB_ROOT/serial.log`。

### 7.7 踩坑

| 现象 | 处理 |
| --- | --- |
| `Function "xxx" not defined` + pending | 拼写错误，或未 `add-symbol-file` / 未 `insmod` |
| 改 `.ko` 后断点失效 | guest `rmmod` + 重 `insmod`，GDB 重新 `add-symbol-file`（地址可能变） |
| `Remote connection closed` | QEMU 已退出或没加 `-s` |
| 端口 1234 占用 | `ps -ef \| grep qemu-system` 清残留 |

## 8 用户态如何调到驱动的 read/write

```text
echo xxx > /dev/lab0
  → write(2)
  → vfs_write
  → file->f_op->write  = lab_write
  → copy_from_user

cat /dev/lab0
  → read(2)
  → vfs_read
  → file->f_op->read   = lab_read
  → copy_to_user
```

驱动侧注册：

```c
static const struct file_operations lab_fops = {
    .open = lab_open, .read = lab_read,
    .write = lab_write, .release = lab_release,
};
misc_register(&lab->misc);   // 生成 /dev/lab0
```

## 9 构建产物与模块规则

- `.ko` 生成在 `M=` 目录（`plutosdr-fw/modules/`），不在 `O=` 目录。
- `.ko` 必须与**当前运行内核**（同一 `O=` 构建树）匹配，否则 `insmod` 报 vermagic/符号错误。
- 仅 `make bzImage` 时 `Module.symvers` 可能为空：`stage1.sh prepare` 会从 `vmlinux.symvers` 复制。
- out-of-tree 模块加载后内核显示 `Tainted: G`，属正常。

## 10 常见问题

| 现象 | 处理 |
| --- | --- |
| `9P_SHARE_NONE` | 确认 `run_qemu.sh` 未设 `SHARE=0`；guest 手动 mount 9p |
| `insmod` 报 Invalid module format | 用同一 `KERNEL_BUILD` 重编；跑 `stage1.sh prepare` |
| `Module.symvers` 缺失导致 modpost undefined | `cp $KERNEL_BUILD/vmlinux.symvers $KERNEL_BUILD/Module.symvers` |
| 端口 1234 占用 | `ps -ef \| grep qemu-system` 清残留 |
| `can't access tty` | initramfs 无控制终端，正常 |

## 关联

- [[学习-Linux-阶段1-最小驱动闭环]]（阶段 1 整合版：模块/VFS/G1/框架图）
- [[学习-Linux-阶段0-源码地图与调试环境]]
- [[学习-Linux-学习路线]]
- [[MOC-Linux]]
