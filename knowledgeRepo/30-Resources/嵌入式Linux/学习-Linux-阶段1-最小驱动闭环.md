---
type: resource
tags: [Linux, 嵌入式, 内核, 驱动开发, 模块, 字符设备, file_operations, VFS, lab_chardev, syscall, entry_SYSCALL_64, 用户态, 内核态]
created: 2026-09-11
updated: 2026-09-14
status: active
source: plutosdr-fw modules (hello + lab_chardev), linux 6.1
repo: /home/congqiang/work/repo/plutosdr-fw/modules
---

# 学习：Linux 阶段 1 —— 最小驱动闭环（整合版）

## 一句话总结

阶段 1 完成两个外部模块的完整闭环：`insmod → lsmod → dmesg → /dev 读写 → rmmod`。`hello` 验证 `module_init/exit` 不是 `main`；`lab_chardev` 用 `miscdevice + file_operations` 把用户态 `cat/echo` 接到内核回调。本文整合：代码位置、构建、**用户态 `syscall` → 入口汇编 → VFS** 完整调用链（含内核源码行号）、`insmod` 前置路径、GDB（G1）、用户态/内核态隔离要点、实测证据。QEMU/9p 环境细节见 [[学习-Linux-kernel-lab-QEMU使用流程]]（独立存档，不并入本文）。

## 0 框架图

![[图-设备驱动框架-lab_chardev.svg]]

可编辑源：[[图-设备驱动框架-lab_chardev.excalidraw]]

| 层 | 内容 |
| --- | --- |
| 用户空间 | `open/read/write/close`；Pthread/QT 只是不同调用方 |
| 硬件入口 | `syscall` 指令（Ring3→Ring0）→ `entry_SYSCALL_64` |
| 系统调用分发 | `do_syscall_64` → `sys_call_table[]` → `__x64_sys_*` |
| 内核 VFS | `vfs_read` / `vfs_write` → `file->f_op` |
| file_operations | `.open=lab_open` 等 |
| module | `insmod`/`rmmod` → `lab_chardev.ko` |
| 硬件 | 寄存器 / PA；驱动常用 `ioremap(PA)→VA` |

## 1 完成清单

- [x] T1 最小模块：`hello.c`（`module_init/exit` + `pr_info`）
- [x] T2 杂项字符设备：`lab_chardev.c`（misc + fops + `copy_*_user` + `container_of` + mutex）
- [x] 外部模块构建：`make ... M=modules`；`Module.symvers` 从 `vmlinux.symvers` 恢复
- [x] 进 QEMU：9p 共享（推荐）或 initramfs 打包
- [x] 动态验证：`insmod → cat/echo → rmmod` 全链 dmesg
- [x] G1：GDB 断住 `lab_read`，栈含 `vfs_read` / `ksys_read`（已实测）
- [x] 静态补全：用户态 `syscall` → `entry_SYSCALL_64` → `do_syscall_64` 入口层

## 2 代码与脚本位置

| 路径 | 作用 |
| --- | --- |
| `/home/congqiang/work/repo/plutosdr-fw/modules/hello.c` | 最小模块 |
| `/home/congqiang/work/repo/plutosdr-fw/modules/lab_chardev.c` | misc 字符设备 |
| `/home/congqiang/work/repo/plutosdr-fw/modules/Makefile` | `obj-m += hello.o lab_chardev.o` |
| `/home/congqiang/work/repo/plutosdr-fw/kernel-lab/stage1.sh` | `check/prepare/modules/pack/demo` |
| `/home/congqiang/work/repo/plutosdr-fw/kernel-lab/run_qemu.sh` | QEMU + 9p（见独立 QEMU 文档） |

符号行号（`lab_chardev.c`）：

| 符号 | 行 |
| --- | --- |
| `lab_open` | 33 |
| `lab_release` | 43 |
| `lab_read` | 54 |
| `lab_write` | 87 |
| `lab_fops` | 117 |
| `misc.fops = &lab_fops` | 146 |
| `misc_register` | 149 |
| `lab_chardev_init` | 126 |
| `lab_chardev_exit` | 160 |

## 3 构建与运行（阶段 1 范围）

```bash
export LAB=/home/congqiang/work/repo/plutosdr-fw/kernel-lab
source $LAB/env.sh

bash $LAB/stage1.sh check     # CONFIG_MODULES / busybox / 构建树
bash $LAB/stage1.sh prepare   # modules_prepare + Module.symvers
bash $LAB/stage1.sh modules   # 产出 modules/*.ko
bash $LAB/run_qemu.sh         # 9p 共享 modules → guest /mnt（细节见 QEMU 文档）
```

guest：

```sh
insmod /mnt/hello.ko
insmod /mnt/lab_chardev.ko
ls -l /dev/lab0
cat /dev/lab0
echo hello-from-userspace > /dev/lab0
cat /dev/lab0
rmmod lab_chardev; rmmod hello
```

底层编译：

```bash
make -C /home/congqiang/work/repo/plutosdr-fw/linux \
     O=/home/congqiang/work/repo/tools/kernel-lab/build/linux-x86_64 \
     ARCH=x86_64 \
     M=/home/congqiang/work/repo/plutosdr-fw/modules \
     modules
```

`.ko` 生成在 `M=` 目录旁，不在 `O=`。

## 4 hello 模块要点

- `module_init(hello_init)` / `module_exit(hello_exit)`：不是 `main`；内核在装载/卸载时调用。
- `init` 返回非 0 → `insmod` 失败并带 errno。
- out-of-tree 加载后 `lsmod` 显示 `Tainted: G`，正常。

## 5 lab_chardev 数据结构

```c
#define LAB_BUF_SIZE 128

struct lab_dev {
    char buf[LAB_BUF_SIZE];   // 最后一次 write 的内容
    size_t len;
    struct mutex lock;        // 可睡眠；不能用于 IRQ
    struct miscdevice misc;   // 嵌入，供 container_of
};
```

设备状态就是内核里一块内存 + 一把锁，不是硬件寄存器。

## 6 file_operations 与「挂给 VFS」

```c
static const struct file_operations lab_fops = {
    .owner   = THIS_MODULE,      // 引用计数，防 rmmod 卸载仍在用的代码
    .open    = lab_open,
    .release = lab_release,
    .read    = lab_read,
    .write   = lab_write,
    .llseek  = default_llseek,
};
```

挂载路径：

```text
lab_chardev_init
  misc.fops = &lab_fops
  misc_register
      → cdev_add / devtmpfs → /dev/lab0
open /dev/lab0
  do_dentry_open
  misc_open                 // major=10 统一入口
      private_data = &misc
      replace_fops → file->f_op = lab_fops
      lab_open()
```

对象关系：

```text
struct file
  ├─ f_op ─────────────► lab_fops
  └─ private_data ─────► lab_dev { buf, len, lock, misc }
```

`container_of(private_data, lab_dev, misc)`：misc_open 先填的是 `miscdevice*`，open 里换算成完整 `lab_dev*` 再写回。

## 7 完整调用链：入口汇编 + VFS + 内核源码锚点（linux 6.1）

### 7.0 硬件入口（`entry_64.S`，2026-09-14 WSL 实读）

`read(2)` 在用户态只是个薄包装：把 `__NR_read=0` 放进 `rax`，再执行 **`syscall` 指令**。CPU 将 RIP 改写为 `MSR_LSTAR` 启动时写入的地址，即 `entry_SYSCALL_64`。

源码锚点（`arch/x86/entry/`）：

| 位置 | 内容 |
| --- | --- |
| `entry_64.S:87` | `SYM_CODE_START(entry_SYSCALL_64)` |
| `entry_64.S:89` | `swapgs`：用户 GS → 内核 GS |
| `entry_64.S:90–94` | 暂存用户 RSP → 切内核 CR3（PTI）→ 切内核栈 |
| `entry_64.S:100–110` | 压 `pt_regs`（ss/sp/flags/cs/ip/orig_ax） |
| `entry_64.S:112` | `PUSH_AND_CLEAR_REGS`，`rax` 预置 `-ENOSYS` |
| `entry_64.S:116–117` | `rdi=&pt_regs`，`rsi=nr`（系统调用号） |
| `entry_64.S:120` | **`call do_syscall_64`** |
| `entry_64.S:226` | `sysretq`：快路径降回 Ring 3 |
| `common.c:73` | `do_syscall_64(struct pt_regs *regs, int nr)` |
| `common.c:50` | `regs->ax = sys_call_table[unr](regs)` |
| `syscalls/syscall_64.tbl:11` | `0  common  read  sys_read` |
| `syscall_64.c` | `sys_call_table[]` 由 tbl/头文件生成 |

`entry_SYSCALL_64` 汇编骨架（节选，已对照源码）：

```asm
SYM_CODE_START(entry_SYSCALL_64)
	swapgs
	movq	%rsp, PER_CPU_VAR(cpu_tss_rw + TSS_sp2)  ; 存用户 RSP
	SWITCH_TO_KERNEL_CR3 scratch_reg=%rsp
	movq	PER_CPU_VAR(cpu_current_top_of_stack), %rsp
	pushq	$__USER_DS          ; pt_regs->ss
	pushq	PER_CPU_VAR(cpu_tss_rw + TSS_sp2)
	pushq	%r11                ; flags
	pushq	$__USER_CS
	pushq	%rcx                ; 用户返回 RIP
	pushq	%rax                ; orig_ax（系统调用号）
	PUSH_AND_CLEAR_REGS rax=$-ENOSYS
	movq	%rsp, %rdi
	movslq	%eax, %rsi
	call	do_syscall_64
	; ... 条件检查 ...
	sysretq
```

`do_syscall_64`（`common.c:73`）核心逻辑：

```c
nr = syscall_enter_from_user_mode(regs, nr);
if (!do_syscall_x64(regs, nr) && !do_syscall_x32(regs, nr) && nr != -1)
	regs->ax = __x64_sys_ni_syscall(regs);   // 无效号 → -ENOSYS
syscall_exit_to_user_mode(regs);
// do_syscall_x64: regs->ax = sys_call_table[unr](regs);
```

查看命令（WSL）：

```bash
less +87 /home/congqiang/work/repo/plutosdr-fw/linux/arch/x86/entry/entry_64.S
less +73 /home/congqiang/work/repo/plutosdr-fw/linux/arch/x86/entry/common.c
# GDB: disassemble entry_SYSCALL_64 / break do_syscall_64
```

### 7.1 read（`cat /dev/lab0`）

```text
cat /dev/lab0
  busybox: open → loop{ read; write(1,…) } → close
  read(2) 包装: rax=0(__NR_read), rdi=fd, rsi=buf, rdx=count
  syscall 指令                         ← 用户态结束 / 内核态开始
    entry_SYSCALL_64                   entry_64.S:87
      swapgs / 切内核栈 / 压 pt_regs
    call do_syscall_64                 entry_64.S:120 → common.c:73
      sys_call_table[0] = __x64_sys_read
    __x64_sys_read / SYSCALL_DEFINE3(read)     fs/read_write.c
    ksys_read                                  :602
    vfs_read                                   :450
        if (file->f_op->read)
            ret = file->f_op->read(...)        ★ lab_read
    lab_read → copy_to_user
    sysretq                                    entry_64.S:226
```

### 7.2 write

```text
write(2)
  SYSCALL_DEFINE3(write) → ksys_write        :626
  vfs_write                                  :564
      file->f_op->write → lab_write
  copy_from_user
```

### 7.3 open

```text
open(2)
  SYSCALL_DEFINE3(open)                      fs/open.c:1330
  do_sys_openat2                             :1294
  do_filp_open → do_dentry_open              :826
      f->f_op = fops_get(inode->i_fop)
      open = f->f_op->open
  misc_open                                  drivers/char/misc.c:100
      replace_fops; file->f_op->open = lab_open
  lab_open
```

### 7.4 close

```text
close(2) SYSCALL_DEFINE1(close)              fs/open.c:1437
  filp_close                                 :1410
  fput                                       fs/file_table.c:369
  __fput                                     :294
      file->f_op->release → lab_release
```

### 7.5 lseek

```text
vfs_llseek                                   fs/read_write.c:285
  file->f_op->llseek = default_llseek
```

### 7.6 对照表

| 用户态 | syscall | VFS | fops | 驱动 |
| --- | --- | --- | --- | --- |
| open | `__x64_sys_open` | `do_dentry_open` / `misc_open` | `.open` | `lab_open` |
| read | `__x64_sys_read` | `vfs_read` | `.read` | `lab_read` |
| write | `__x64_sys_write` | `vfs_write` | `.write` | `lab_write` |
| lseek | `__x64_sys_lseek` | `vfs_llseek` | `.llseek` | `default_llseek` |
| close | `__x64_sys_close` | `filp_close`/`__fput` | `.release` | `lab_release` |

`struct file_operations` 定义：`include/linux/fs.h:2103`。

### 7.7 SYSCALL_DEFINE（简要）

`SYSCALL_DEFINE3(write, unsigned int, fd, const char __user *, buf, size_t, count)` 展开后概念上：

```text
sys_write          ← alias
__x64_sys_write    ← syscall 表入口
__se_sys_write     ← 参数按 long 接入再转换
__do_sys_write     ← 函数体：ksys_write(...)
```

x86_64 `sys_call_table[]` 定义在 `arch/x86/entry/syscall_64.c`，条目由 `arch/x86/entry/syscalls/syscall_64.tbl` 生成；分发在 `arch/x86/entry/common.c:50`（`sys_call_table[unr](regs)`）。`read` 编号为 0，`write` 编号为 1。

### 7.8 实测 GDB 栈（read）

```text
#0  lab_read          modules/lab_chardev.c:57
#1  vfs_read          fs/read_write.c
#2  ksys_read
#3  __x64_sys_read
```

## 8 lab_read / lab_write 逻辑

### lab_read

```text
1. mutex_lock_interruptible → 失败 -ERESTARTSYS
2. *ppos >= len → 0（EOF，cat 退出）
3. count 裁剪为剩余
4. copy_to_user → 失败 -EFAULT
5. *ppos += n; return n
```

| 返回值 | 用户态 |
| --- | --- |
| `>0` | 读到 n 字节 |
| `0` | EOF |
| 负 errno | `read` → -1 |

### lab_write

```text
1. 加锁
2. count>=128 截断为 127
3. copy_from_user
4. 补 '\0'；去 echo 末尾换行
5. return count；只保留最后一次写入
```

`buf` 在 GDB 里显示 `Cannot access memory` 属正常（用户地址，内核态不能直接解引用）。

## 9 insmod 到 lab_chardev_init 的前置链

`lab_chardev_init` **不是** `insmod` 直接调的：

```text
insmod
  → finit_module(fd,...)          kernel/module/main.c:2916
  → load_module                   :2671
       module_sig_check
       elf_validity_check
       setup_load_info
       layout_and_allocate        // module_alloc + 拷贝
       simplify_symbols
       apply_relocations
       parse_args / mod_sysfs_setup
       complete_formation
  → do_init_module                :2440
       do_mod_ctors
       do_one_initcall(mod->init) init/main.c:1293
  → lab_chardev_init              modules/lab_chardev.c:126
```

`module_init(initfn)`（`include/linux/module.h:129`）把函数 **alias 成 ELF 符号 `init_module`**，装载器填进 `mod->init`。

`/sys/module/<name>/sections/.text` **只在 insmod 成功后存在**（运行时地址）；之前只有磁盘上的 ELF 偏移（`readelf -S`）。

## 10 G1：GDB 断住自己的 open/read

**必须先 insmod**，再读段地址、`add-symbol-file`。

```text
# 终端 A
bash $LAB/run_qemu.sh
# guest: insmod /mnt/lab_chardev.ko
# guest: cat /sys/module/lab_chardev/sections/.text

# 终端 B
bash $LAB/attach_gdb.sh
add-symbol-file /home/congqiang/work/repo/plutosdr-fw/modules/lab_chardev.ko <text>
break lab_read
break lab_write
info breakpoints          # 确认非 pending
continue

# guest: cat /dev/lab0  → 命中 lab_read
# GDB: bt / list / print *file / next
```

踩坑：函数名是 `lab_*` 不是 `lad_*`；拼错会变 pending。改 `.ko` 后要 `rmmod`+`insmod` 并重新 `add-symbol-file`。GDB 命令速查见 [[学习-Linux-kernel-lab-QEMU使用流程]] §7。

## 11 实测证据（2026-09-11）

```text
insmod hello.ko
  hello: module loaded
  lsmod → hello  Tainted: G

insmod lab_chardev.ko
  lab: char device /dev/lab0 registered (minor=125)
  ls -l /dev/lab0 → crw-rw-rw- 10, 125

cat /dev/lab0
  lab: open / read 18 bytes / lab-chardev-ready / release

echo hello-from-userspace > /dev/lab0
  lab: write 21 bytes -> "hello-from-userspace"

rmmod both → unregistered / unloaded
```

要点：misc major=10；EOF 对应 `*ppos>=len` 返回 0。

## 12 问答：从 `cat` 到内核态（2026-09-14）

> 以下问题来自本阶段深入讨论，答案与 §7 源码锚点一一对应。

### Q1：`entry_64.S` 怎么看？函数入口在哪？`cat /dev/lab0` 怎么调到 `do_syscall_64`？

- 文件在 WSL：`/home/congqiang/work/repo/plutosdr-fw/linux/arch/x86/entry/entry_64.S`
- 用户态系统调用的**唯一入口符号**是 `entry_SYSCALL_64`（`entry_64.S:87`）；启动时 MSR `LSTAR` 写入该地址。
- 它做完 `swapgs`、切栈、压 `pt_regs` 后，在 `entry_64.S:120` **`call do_syscall_64`**。
- `do_syscall_64` 是 **C 函数**（`common.c:73`），不在 `.S` 里；再经 `sys_call_table[nr]` 调到 `__x64_sys_read`。

### Q2：`cat /dev/lab0` 怎么“去到” syscall？

```text
cat → busybox 代码
  open("/dev/lab0") → 得到 fd
  loop: n = read(fd, buf, count)   ← C 函数（libc/busybox 包装）
        write(1, buf, n)
  close(fd)
```

`read()` 包装**不是**系统调用本身，它只做：填寄存器约定（`rax=__NR_read=0`，`rdi/rsi/rdx=参数`）→ 执行 **`syscall` 机器指令**。  
CPU 收到该指令后：Ring3→Ring0，RIP ← `entry_SYSCALL_64`。用户态到此结束。

### Q3：为什么从 busybox 的 C 代码“直接”跳到汇编？

不是 C 愿意跳汇编，而是 **硬件强制**：

1. 用户态不能 `call` 内核函数（权限与地址空间都不允许）。
2. `call` 只能在**同一特权级**内转移；跨 Ring 必须用 `syscall`/中断/异常这类 **CPU 指令**。
3. 进门后必须先切内核栈、`SWAPGS`、精确保存 `pt_regs`——这些是特权/寄存器级操作，C 编译器无法保证，只能汇编。

前门用 C 是为了好写；门框用汇编是 CPU 规定；进门后再回 C 是为了好维护。

### Q4：为什么要分用户态/内核态？为什么之间只能靠硬件转发？为什么转接处必须汇编？

**分态**：不可信程序与可信内核共存。用户态不能随便读写任意内存、关中断、改页表；内核只开放少数入口并校验。

**硬件转发**：提权/降权本身是特权操作。CPU 只认固定路径（`syscall`、中断、异常），并强制切到启动时登记的入口、保存返回点。软件不能伪造任意跳转的提权通道。

**转接处汇编**：刚跨过 `syscall` 时，用户栈、用户 GS、寄存器现场都不符合 C ABI；`swapgs`、换栈、压/弹 `pt_regs`、`sysretq` 必须用汇编做完，再 `call` 进 C。

### Q5：用户态仍然可以调 `syscall` 进内核，隔离还有意义吗？

有意义。**能进门 ≠ 能为所欲为**：

| 能力 | 说明 |
| --- | --- |
| 能进 `entry_SYSCALL_64` | 故意开放；否则无法 read/write |
| 不能执行任意内核指令 | 进门后跑的是**内核写好的**系统调用代码 |
| 白名单 | 只有 `sys_call_table[]` 里列出的服务；无效号 → `-ENOSYS` |
| 每项再校验 | fd 权限、路径、`copy_*_user` 拒绝内核指针等 |
| 用完即走 | `sysretq` 降回 Ring 3 |

隔离拦的是“任意执行、任意访问”，不是“完全禁止进入”。真正攻击面是内核接口**实现写错**（参数未校验、UAF 等），不是“存在 syscall”。

### 完整链路（一图）

```text
cat /dev/lab0
  → busybox read()
  → syscall 指令 (rax=0)
  → entry_SYSCALL_64          entry_64.S:87
  → call do_syscall_64        entry_64.S:120 / common.c:73
  → sys_call_table[0]         __x64_sys_read
  → ksys_read → vfs_read
  → lab_read → copy_to_user
  → sysretq                   entry_64.S:226
```

## 13 概念对照

| 方式 | 优点 | 本阶段 |
| --- | --- | --- |
| `register_chrdev`+cdev | 完全控制 | 样板多 |
| `misc_register` | 动态 minor、自动 `/dev` | ✓ |
| `cdev`+`class/device_create` | 自定义 sysfs 类 | 练习扩展 |

边界拷贝：`copy_to_user` / `copy_from_user`；禁止直接解引用用户指针。

## 14 构建踩坑

1. 仅 `make bzImage` 时 `Module.symvers` 可能为空。
2. `cp $KERNEL_BUILD/vmlinux.symvers $KERNEL_BUILD/Module.symvers`。
3. 空 symvers → modpost 报 `_printk`/`mutex_*`/`misc_*` undefined。
4. busybox 需带 `insmod/rmmod/lsmod`（`stage1.sh pack` 已处理）。
5. `.ko` 必须与当前 `O=` 内核配置匹配，否则 vermagic/符号错误。

## 15 学完应能回答

1. `file_operations` 如何与用户态 `read`/`write` 接上？
2. 为什么必须 `copy_to_user`？
3. `container_of` 从谁换算回谁？
4. 为何选 `misc_register`？
5. `lab_read` 返回 0 / 负数时用户态看到什么？
6. GDB 里用户指针不可访问是否驱动有 bug？
7. `insmod` 到 `lab_chardev_init` 之间内核做了哪些事？
8. 为何必须 insmod 后才有 `sections/.text`？
9. `entry_SYSCALL_64` 在哪个文件？哪一行 `call do_syscall_64`？
10. 用户态 `read()` 包装和 `syscall` 指令的区别是什么？
11. 为什么用户态不能直接 `call lab_read`？
12. 用户态都能 `syscall`，内核隔离还防什么？（见 §12 Q5）

## 16 与路线对应

| 项 | 状态 |
| --- | --- |
| 执行版阶段 1 / T1+T2 | 完成 |
| G1 闸门 | 完成（断 `lab_read` + 解释调用链） |
| 入口层（syscall→entry→do_syscall_64） | 静态完成（§7.0 + §12 问答，2026-09-14） |
| 下一步 | 阶段 2：`do_initcalls` / 启动路径 GDB；或对入口再做 GDB 动态核对 |

## 关联

- [[学习-Linux-kernel-lab-QEMU使用流程]]（**独立**：9p / initramfs / GDB 操作）
- [[学习-Linux-阶段0-源码地图与调试环境]]
- [[学习-Linux-学习路线]]
- [[学习-Linux-内核源码阅读与驱动学习法]]
- [[MOC-Linux]]
