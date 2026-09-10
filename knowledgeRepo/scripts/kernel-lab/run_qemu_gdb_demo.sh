#!/bin/bash
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh" >/dev/null
LAB_ROOT="${LAB_ROOT:-/home/congqiang/work/repo/tools/kernel-lab}"
KERNEL_BUILD="${KERNEL_BUILD:-$LAB_ROOT/build/linux-x86_64}"
QEMU="${QEMU:-qemu-system-x86_64}"
QEMU_DATA="$LAB_ROOT/root/usr/share/qemu"
SEABIOS="$LAB_ROOT/root/usr/share/seabios/bios-256k.bin"
SERIAL_LOG="$LAB_ROOT/serial.log"
GDB_LOG="$LAB_ROOT/gdb.log"
BZIMAGE="$KERNEL_BUILD/arch/x86/boot/bzImage"
VMLINUX="$KERNEL_BUILD/vmlinux"
INITRD="$LAB_ROOT/initramfs.cpio.gz"

if ! command -v "$QEMU" >/dev/null 2>&1; then
	echo "missing command: $QEMU" >&2
	exit 1
fi

for f in "$BZIMAGE" "$VMLINUX" "$INITRD" "$QEMU_DATA" "$SEABIOS"; do
	if [ ! -e "$f" ]; then
		echo "missing: $f" >&2
		exit 1
	fi
done

rm -f "$SERIAL_LOG" "$GDB_LOG"

"$QEMU" \
	-m 512M -smp 2 \
	-kernel "$BZIMAGE" \
	-initrd "$INITRD" \
	-append "console=ttyS0 nokaslr rdinit=/init" \
	-display none -vga none -net none -monitor none -serial "file:$SERIAL_LOG" \
	-no-reboot \
	-L "$QEMU_DATA" -bios "$SEABIOS" \
	-s -S &
QEMU_PID=$!

sleep 2
gdb -q -batch \
	-ex "file $VMLINUX" \
	-ex "target remote :1234" \
	-ex "break start_kernel" \
	-ex "continue" \
	-ex "info registers rip" \
	-ex "bt 5" \
	-ex "detach" > "$GDB_LOG" 2>&1

wait "$QEMU_PID" || true

echo "=== GDB (start_kernel breakpoint) ==="
tail -n 20 "$GDB_LOG"
echo "=== QEMU serial ==="
tail -n 20 "$SERIAL_LOG"
