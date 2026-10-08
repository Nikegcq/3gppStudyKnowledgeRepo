---
type: note
tags: [ZynqMP, RPU, AMP, remoteproc, OpenAMP, rpmsg, bootgen, ZCU670, 实践]
layer: L1
created: 2026-10-08
updated: 2026-10-08
status: active
source: AMD UG1085 / UG1186 / UG1137 + 本机 bootgen.bif、system.dtb、PetaLinux BSP 配置
---

# 实践：ZCU670 上 Linux 与 RPU 同时运行（AMP）

## 一句话总结

可以同时跑：APU 四核 A53 跑 Linux，RPU 双核 R5F 跑 FreeRTOS/裸机，两者独立电源域、独立时钟，这叫 **AMP**。启用方式只有两条路——**开机由 FSBL 静态加载**，或**Linux 起来后用 remoteproc 动态加载**。

## 1 本机现状（2026-10-08，动手前先确认）

| 检查项 | 现状 | 含义 |
| --- | --- | --- |
| `~/work/repo/yocto/images/bootgen.bif` | 只有 FSBL / pmufw.elf / system.bit / bl31 / system.dtb / u-boot，**无 RPU 分区** | 当前是纯 Linux + PL |
| `system.dtb` | 无 `r5fss` / `remoteproc` 节点 | Linux 看不到 R5 |
| `luxshare-n78-bsp-project/.../configs/config` | `# CONFIG_SUBSYSTEM_ENABLE_OPENAMP_DTSI is not set` | OpenAMP 设备树未生成 |
| `.../configs/rootfs_config` | `openamp-fw-*`、`rpmsg-*` 全部 `is not set` | 无 RPU 固件与 rpmsg 测试工具 |

结论：**RPU 目前处于未启用（关机 + 无固件）状态**，要用必须补上固件与设备树。

## 2 方式 A：开机静态加载（最省事，适合常驻实时任务）

把 RPU 固件作为 BOOT.BIN 的一个分区，FSBL 在拉起 U-Boot 之前加载它并释放 R5 复位，R5 先于 Linux 开始工作。

```
the_ROM_image:
{
    [bootloader, destination_cpu=a53-0]   zynqmp_fsbl.elf
    [pmufw_image]                         pmufw.elf
    [destination_device=pl]               system.bit
    [destination_cpu=r5-0]                rpu_app.elf        # ← 新增
    [destination_cpu=r5-1]                rpu_app_1.elf      # ← 可选，split 双核
    [destination_cpu=a53-0, exception_level=el-3, trustzone]  bl31.elf
    [destination_cpu=a53-0, load=0x00100000]  system.dtb
    [destination_cpu=a53-0, exception_level=el-2]  u-boot.elf
}
```

```
bootgen -image bootgen.bif -arch zynqmp -o BOOT.BIN -w on
```

要点：**RPU 分区必须排在 U-Boot 之前**；R5 固件启动地址由 ELF 段决定；lockstep 配置下只要 r5-0。

## 3 方式 B：Linux 动态加载（remoteproc，可单独上下电）

```bash
# 前提：内核开启 R5 remoteproc（linux-xlnx 里是 CONFIG_XLNX_R5_REMOTEPROC，
#       用 grep -i remoteproc .config 确认你的树里的名字），
#       设备树补上 r5fss 节点（xlnx,zynqmp-r5fss / xlnx,zynqmp-r5f），
#       固件放到 /lib/firmware

echo rpu_app.elf > /sys/class/remoteproc/remoteproc0/firmware
echo start        > /sys/class/remoteproc/remoteproc0/state
cat  /sys/class/remoteproc/remoteproc0/state     # running / offline
echo stop         > /sys/class/remoteproc/remoteproc0/state   # 单独下电，不用重启整机
```

## 4 RPU 固件怎么写（Vitis）

1. Vivado 导出 **XSA**（含 PS 配置）
2. Vitis → New Platform Project（基于该 XSA）→ 平台自动出现 `psu_cortexa53_0`（Linux domain）与 `psu_cortexr5_0`（standalone 或 FreeRTOS domain）
3. 基于 r5 domain 建 Application Project，可直接选官方模板：
   - **OpenAMP Echo Test**：Linux ↔ R5 回环，验证通路
   - **DMA Proxy**：大块数据搬运（本机 `~/work/repo/dma-proxy` 就是这个例子的 Yocto recipe）
4. 编译得到 `rpu_app.elf` → 按第 2 或第 3 节加载
5. 调试：JTAG attach 到 R5，Vitis 里单步

BSP 选择：裸机用 `standalone`；要任务调度/网络用 **FreeRTOS + lwIP**（配 [[MOC-RTOS]] 的学习线）。

## 5 Linux ↔ RPU 通信

标准做法是 **OpenAMP（rpmsg）**：

```bash
/dev/rpmsg_ctrl0   # 创建通道
/dev/rpmsg0        # 收发端点
```

底层是 **IPI 中断 + 共享内存环（vring）**。若不想引入 OpenAMP，可自己定共享内存 + IPI，实现更简单可控。

## 6 资源划分的四个坑

1. **内存**：给 RPU 的 DDR 区必须在 DTB 里用 `reserved-memory` 从 Linux 内存挖出去，否则被当成空闲页分配掉
2. **外设归属**：RPU 要用的 UART/SPI/I2C/QSPI 在 DTB 里 `status = "disabled"`（QSPI 最典型，两个 OS 抢同一个控制器必炸）
3. **Cache 一致性**：TCM 不走 cache（免维护）；共享 DDR 建议 non-cacheable 或收发前后 flush/invalidate，Linux 侧优先用 `dma_alloc_coherent`
4. **中断**：GIC 中断按核分配；**lockstep 模式中断只能发给 CPU0**（UG1085 要求在 reset handler 里配好）

## 7 验证清单

```bash
dmesg | grep -i remoteproc                 # 驱动是否 probe 成功
ls /sys/class/remoteproc/                  # 是否出现 remoteproc0
cat /sys/class/remoteproc/remoteproc0/state
ls /dev/rpmsg*                             # rpmsg 通道
cat /proc/interrupts | grep -i ipi         # IPI 是否在跑
```

## 相关笔记

- [[概念-ZynqMP-PS-APU与RPU]]（RPU 是什么）
- [[概念-高端radio软件架构-Linux与RTOS分工]]（到底要不要引入 RPU）
- [[ZCU670-PL-PS-参数]]、[[luxshare-zcu670]]
- [[MOC-RTOS]]、[[MOC-Linux]]
