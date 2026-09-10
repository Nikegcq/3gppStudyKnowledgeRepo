#!/bin/bash
# Attach GDB to a running QEMU (-s / gdbstub on :1234).
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh" >/dev/null

KERNEL_BUILD="${KERNEL_BUILD:-$LAB_ROOT/build/linux-x86_64}"
VMLINUX="$KERNEL_BUILD/vmlinux"

gdb -q \
	-ex "file $VMLINUX" \
	-ex "target remote :1234" \
	-ex "break start_kernel" \
	"$@"
