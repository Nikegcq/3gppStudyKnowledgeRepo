# kernel-lab：QEMU + GDB 内核调试环境

这是 Linux 学习路径「执行版阶段 0」的配套环境：在 WSL 里无 sudo 搭起一个可断点调试的 x86_64 内核（QEMU 6.2 + GDB 12.1 + Linux 6.1）。

本文把常用 **QEMU 操作命令**集中在一处，可直接复制执行。

## 0. 一次性准备

```bash
cd /home/congqiang/work/repo/plutosdr-fw

export LAB=/mnt/c/Users/gaooocon/study/3gppStudyKnowledgeRepo/knowledgeRepo/scripts/kernel-lab
source $LAB/env.sh

# 首次使用，或修改过 init 脚本后：生成 initramfs
bash $LAB/make_initramfs.sh
```

`env.sh` 会注入 QEMU/flex/bison/bc 的用户态工具路径，以及 `QEMU_MODULE_DIR`（QEMU 的 TCG 模块目录）。

## 1. QEMU 操作总览

| 操作 | 命令 | 说明 |
| --- | --- | --- |
| 直接进入 guest shell | `bash $LAB/run_qemu.sh` | 默认模式；同时开放 GDB stub `:1234` |
| 先暂停、等 GDB 连上 | `PAUSE=1 bash $LAB/run_qemu.sh` | QEMU 以 `-S` 暂停，连上 GDB 后 `continue` |
| 自动演示：断点 + 跑到用户态 | `bash $LAB/run_qemu_gdb_demo.sh` | 无需人工操作，输出 GDB 与串口日志 |
| 连接已在运行的 QEMU | `bash $LAB/attach_gdb.sh` | 自动加载 `vmlinux`、连 `:1234`、断 `start_kernel` |
| 重新生成 initramfs | `bash $LAB/make_initramfs.sh` | 改过 `init` 或 Applet 列表后执行 |

## 2. 直接进入 QEMU（交互 shell）

```bash
cd /home/congqiang/work/repo/plutosdr-fw
export LAB=/mnt/c/Users/gaooocon/study/3gppStudyKnowledgeRepo/knowledgeRepo/scripts/kernel-lab
source $LAB/env.sh

bash $LAB/run_qemu.sh
```

进入 guest 后可以看到：

```text
INITRAMFS_OK
kernel: 6.1.0-gf3da30df6004
cmdline: console=ttyS0 nokaslr rdinit=/init debugshell
DEBUGSHELL: dropping to /bin/sh
/ #
```

guest 内常用命令：

```sh
uname -a                 # 内核版本与编译信息
cat /proc/cmdline        # 内核命令行（确认 nokaslr / rdinit / debugshell）
cat /proc/version
ls /proc                 # 查看进程
cat /proc/meminfo | head # 内存信息
ls /sys
dmesg | tail             # 内核日志
poweroff -f              # 退出 QEMU
```

提示：`/bin/sh: can't access tty; job control turned off` 是 initramfs 里没有控制终端的正常提示，不影响使用。

退出方式：

- guest 内执行 `poweroff -f`
- 或按 `Ctrl-A`，松手后再按 `X`（`-nographic` 的 QEMU 退出快捷键）

## 3. GDB 断点调试

### 3.1 先启动 QEMU，再单独连 GDB

终端 A（保持运行）：

```bash
source $LAB/env.sh
bash $LAB/run_qemu.sh
```

终端 B：

```bash
source $LAB/env.sh
bash $LAB/attach_gdb.sh
```

`attach_gdb.sh` 会自动执行：

```gdb
file $KERNEL_BUILD/vmlinux
target remote :1234
break start_kernel
```

之后在 GDB 里输入 `continue`，内核继续启动。

### 3.2 先暂停、再连 GDB

```bash
# 终端 A
source $LAB/env.sh
PAUSE=1 bash $LAB/run_qemu.sh

# 终端 B
source $LAB/env.sh
bash $LAB/attach_gdb.sh
```

### 3.3 自动演示（不需要人工交互）

```bash
source $LAB/env.sh
bash $LAB/run_qemu_gdb_demo.sh
```

输出会包含 `start_kernel` 命中记录、寄存器、调用栈，以及 QEMU 串口日志。

### 3.4 GDB 常用命令

```gdb
break start_kernel          # 在 start_kernel 下断点
break do_initcalls          # initcall 机制入口
break ad9361_probe          # P 线：AD9361 SPI 驱动 probe
break axiadc_probe          # P 线：AXI ADC 数据面 probe
continue                    # 继续运行
bt                          # 查看调用栈
info registers rip          # 查看寄存器
list                        # 查看源码
next / step                 # 单步（不进入 / 进入函数）
print 变量名                 # 查看变量
disconnect                  # 断开连接，让 QEMU 继续运行
quit                        # 退出 GDB
```

## 4. QEMU 启动参数说明

`run_qemu.sh` 实际执行的核心参数：

```bash
qemu-system-x86_64 \
    -m 512M -smp 2 \
    -kernel "$KERNEL_BUILD/arch/x86/boot/bzImage" \
    -initrd "$LAB_ROOT/initramfs.cpio.gz" \
    -append "console=ttyS0 nokaslr rdinit=/init debugshell" \
    -nographic -vga none -net none -no-reboot \
    -L "$LAB_ROOT/root/usr/share/qemu" \
    -bios "$LAB_ROOT/root/usr/share/seabios/bios-256k.bin" \
    -s
```

关键点：

- `nokaslr`：关闭内核地址随机化，便于 GDB 断点。
- `rdinit=/init`：用 initramfs 里的 `/init` 启动。
- `debugshell`：让 `/init` 挂载 proc/sys/dev 后进入交互 shell。
- `-s`：开放 GDB stub（TCP 1234）；`PAUSE=1` 时会再加 `-S` 暂停。
- `-vga none -net none`：避免去加载宿主机不存在的 VGA/NIC ROM（用户态解包环境里常见的 `romfile` 报错）。

## 5. 常用操作速查

```bash
# 准备环境
cd /home/congqiang/work/repo/plutosdr-fw
export LAB=/mnt/c/Users/gaooocon/study/3gppStudyKnowledgeRepo/knowledgeRepo/scripts/kernel-lab
source $LAB/env.sh

# 重建 initramfs
bash $LAB/make_initramfs.sh

# 直接进 QEMU
bash $LAB/run_qemu.sh

# 暂停启动 + GDB
PAUSE=1 bash $LAB/run_qemu.sh
bash $LAB/attach_gdb.sh

# 自动跑一遍断点演示
bash $LAB/run_qemu_gdb_demo.sh

# 看 QEMU / GDB 日志
tail -n 40 /home/congqiang/work/repo/tools/kernel-lab/serial.log
tail -n 40 /home/congqiang/work/repo/tools/kernel-lab/gdb.log

# 找残留 QEMU 进程
ps -ef | grep qemu-system | grep -v grep
```

## 6. 常见问题

| 现象 | 处理 |
| --- | --- |
| `failed to find romfile "vgabios-stdvga.bin"` / `"efi-e1000.rom"` | 用 `run_qemu.sh`（已带 `-vga none -net none`）；不要去掉这两个参数 |
| `accel_init_ops_interfaces: assertion failed` | 没设置 `QEMU_MODULE_DIR`；先 `source $LAB/env.sh` |
| `missing: .../bzImage` | 先按第 7 节构建内核 |
| `missing: .../initramfs.cpio.gz` | 先运行 `bash $LAB/make_initramfs.sh` |
| `flex: command not found` / bison 报错 | 先 `source $LAB/env.sh`；必要时检查 `$LAB_ROOT/root/usr/share/bison/m4sugar/m4sugar.m4` |
| `Address already in use` / 端口 1234 被占用 | `ps -ef | grep qemu-system`，结束残留 QEMU 后再启动 |
| GDB 提示 `Remote connection closed` | QEMU 已退出或没加 `-s`；确认 QEMU 还在运行 |

## 7. 构建内核（已构建过，重装环境时才需要）

```bash
source $LAB/env.sh
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 defconfig
"$KERNEL_SRC/scripts/config" --file "$KERNEL_BUILD/.config" \
    -e DEBUG_INFO_DWARF4 -e GDB_SCRIPTS \
    -d UNWINDER_ORC -e UNWINDER_FRAME_POINTER -d RANDOMIZE_BASE
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 olddefconfig
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 -j"$(nproc)" bzImage
```

## 8. 目录假设与依赖

- 内核源码：`/home/congqiang/work/repo/plutosdr-fw/linux`（6.1）
- 用户态工具与构建产物：`/home/congqiang/work/repo/tools/kernel-lab`
- 可用环境变量覆盖：`LAB_ROOT`、`KERNEL_SRC`、`KERNEL_BUILD`、`QEMU`

WSL 无 sudo 时，`flex`、`bison`、`bc`、`libelf-dev`、`qemu-system-x86` 等包用
`apt-get download` + `dpkg-deb -x` 解包到 `$LAB_ROOT/root`，再由 `env.sh` 注入
`PATH` / `LD_LIBRARY_PATH` / `CPATH` / `LIBRARY_PATH` / `BISON_PKGDATADIR` / `QEMU_MODULE_DIR`。

## 9. 改动内核代码后如何重新编译

### 9.1 x86_64 调试内核（当前 QEMU 用的就是它）

改完 `$KERNEL_SRC` 里的内核源码后，执行增量编译：

```bash
cd /home/congqiang/work/repo/plutosdr-fw
export LAB=/mnt/c/Users/gaooocon/study/3gppStudyKnowledgeRepo/knowledgeRepo/scripts/kernel-lab
source $LAB/env.sh

make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 -j"$(nproc)" bzImage
```

- `O="$KERNEL_BUILD"`：继续用原来的独立构建目录，已有产物会做增量编译，只重编改动过的文件。
- `env.sh` 必须 source：否则会缺 `flex` / `bison` / `libelf` 或 `BISON_PKGDATADIR`。
- 不要省略 `O=`：否则会在源码树里做 in-tree 构建，污染 plutosdr-fw 的源码目录。

编译完成后重启 QEMU 即可用上新内核：

```bash
bash $LAB/run_qemu.sh
```

GDB 会自动使用同一构建目录里的新 `vmlinux`，无需额外操作。

### 9.2 改了 Kconfig / .config

```bash
source $LAB/env.sh

# 用 scripts/config 打开/关闭某个配置项，例如：
"$KERNEL_SRC/scripts/config" --file "$KERNEL_BUILD/.config" -e DEBUG_INFO_DWARF4

# 让新增/修改的配置项生效
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 olddefconfig

# 重新编译
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 -j"$(nproc)" bzImage
```

### 9.3 改了外部模块（阶段 1 的 hello/misc 驱动）

外部模块不编进 `bzImage`，单独编译：

```bash
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 M=/path/to/your-module modules
```

产物是该目录下的 `*.ko`。要让 guest 能 `insmod`，需要把它放进 initramfs（可扩展
`make_initramfs.sh` 复制 `.ko`），或者给 QEMU 加 `-virtfs` 目录共享后在 guest 里
`mount -t 9p` 访问。这个部分在阶段 1 落地时再补脚本。

### 9.4 改了 ARM / Pluto 固件内核（zImage + dtb）

当前 lab 只编译了 x86_64；Pluto 固件内核需要 ARM 交叉工具链和另一套构建目录：

```bash
# 需要先具备 arm-linux-gnueabihf- 交叉编译器
make -C "$KERNEL_SRC" O="$LAB_ROOT/build/linux-arm-pluto" \
    ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- zynq_pluto_defconfig

make -C "$KERNEL_SRC" O="$LAB_ROOT/build/linux-arm-pluto" \
    ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j"$(nproc)" zImage dtbs
```

注意：

- **不要和 x86_64 共用同一个 `O=` 目录**，ARCH/配置不同会互相覆盖。
- `zynq_pluto_defconfig` 里 AD9361 / CF_AXI_ADC 等 Pluto 驱动才会被启用；x86_64 配置里没有它们。
- 编译产物是 `zImage` 与 `zynq-pluto-sdr*.dtb`，要上真实 Pluto 板（或 Zynq QEMU，但 PL/AD9361 不被模拟）验证才有意义。

### 9.5 什么时候需要 clean

```bash
# 一般不需要；增量 make 会处理头文件依赖
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 clean

# 极端情况（架构/工具链切换、配置大改）才考虑 mrproper，它会连 .config 一起删
# make -C "$KERNEL_SRC" O="$KERNEL_BUILD" ARCH=x86_64 mrproper
```

推荐做法：**不同 ARCH / 不同用途用不同 `O=` 目录**，正常改代码只做增量 `make`，
不要随意 `clean`，否则每次都是全量编译，浪费时间。
