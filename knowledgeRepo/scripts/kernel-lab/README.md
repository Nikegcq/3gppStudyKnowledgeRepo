# kernel-lab（知识库侧说明）

调试脚本与模块源码已迁入 WSL 的 plutosdr-fw；完整 QEMU 使用流程见知识库笔记：

- **[[学习-Linux-kernel-lab-QEMU使用流程]]**（主文档：9p / initramfs / stage1 / GDB）
- [[学习-Linux-阶段0-源码地图与调试环境]]
- [[学习-Linux-阶段1-最小驱动闭环]]

## 路径速查

| 内容 | 路径 |
| --- | --- |
| 脚本（env / QEMU / GDB / stage1） | `/home/congqiang/work/repo/plutosdr-fw/kernel-lab/` |
| 外部模块源码 | `/home/congqiang/work/repo/plutosdr-fw/modules/` |
| 构建产物 / initramfs / 日志 | `/home/congqiang/work/repo/tools/kernel-lab/`（`LAB_ROOT`） |
| 9p 默认共享目录 | `plutosdr-fw/modules` → guest `/mnt`（`mount_tag=hostshare`） |

## 日常三行

```bash
export LAB=/home/congqiang/work/repo/plutosdr-fw/kernel-lab
source $LAB/env.sh
bash $LAB/stage1.sh modules && bash $LAB/run_qemu.sh
```

guest：`insmod /mnt/hello.ko` → `insmod /mnt/lab_chardev.ko` → `cat /dev/lab0`
