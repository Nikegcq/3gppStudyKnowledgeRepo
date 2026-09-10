#!/bin/bash
# Boot the debug kernel directly into an interactive guest shell.
#
# Usage:
#   bash scripts/kernel-lab/run_qemu.sh          # direct boot + gdbstub on :1234
#   PAUSE=1 bash scripts/kernel-lab/run_qemu.sh  # wait for GDB before booting
#
# Exit QEMU: Ctrl-A then X   (or run "poweroff -f" inside the guest)
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh" >/dev/null

LAB_ROOT="${LAB_ROOT:-/home/congqiang/work/repo/tools/kernel-lab}"
KERNEL_BUILD="${KERNEL_BUILD:-$LAB_ROOT/build/linux-x86_64}"
QEMU="${QEMU:-qemu-system-x86_64}"
QEMU_DATA="$LAB_ROOT/root/usr/share/qemu"
SEABIOS="$LAB_ROOT/root/usr/share/seabios/bios-256k.bin"
BZIMAGE="$KERNEL_BUILD/arch/x86/boot/bzImage"
INITRD="$LAB_ROOT/initramfs.cpio.gz"
PAUSE="${PAUSE:-0}"

for f in "$BZIMAGE" "$INITRD" "$QEMU_DATA" "$SEABIOS"; do
	if [ ! -e "$f" ]; then
		echo "missing: $f" >&2
		exit 1
	fi
done

PAUSE_ARGS=()
if [ "$PAUSE" = "1" ]; then
	PAUSE_ARGS=(-S)
	echo "QEMU is paused; attach GDB: bash $HERE/attach_gdb.sh"
fi

exec "$QEMU" \
	-m 512M -smp 2 \
	-kernel "$BZIMAGE" \
	-initrd "$INITRD" \
	-append "console=ttyS0 nokaslr rdinit=/init debugshell" \
	-nographic -vga none -net none -no-reboot \
	-L "$QEMU_DATA" -bios "$SEABIOS" \
	-s "${PAUSE_ARGS[@]}"
