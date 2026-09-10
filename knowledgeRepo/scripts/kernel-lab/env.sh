#!/bin/bash
# Kernel lab environment (stage 0 of the Linux learning path).
# Source this file before building/running the debug kernel:
#   source scripts/kernel-lab/env.sh

export LAB_ROOT="${LAB_ROOT:-/home/congqiang/work/repo/tools/kernel-lab}"
export KERNEL_SRC="${KERNEL_SRC:-/home/congqiang/work/repo/plutosdr-fw/linux}"
export KERNEL_BUILD="${KERNEL_BUILD:-$LAB_ROOT/build/linux-x86_64}"

# User-space tools extracted from Ubuntu packages (no sudo needed).
export PATH="$LAB_ROOT/root/usr/bin:$PATH"
export LD_LIBRARY_PATH="$LAB_ROOT/root/usr/lib/x86_64-linux-gnu:$LAB_ROOT/root/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CPATH="$LAB_ROOT/root/usr/include:$LAB_ROOT/root/usr/include/x86_64-linux-gnu${CPATH:+:$CPATH}"
export LIBRARY_PATH="$LAB_ROOT/root/usr/lib/x86_64-linux-gnu:$LAB_ROOT/root/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
export BISON_PKGDATADIR="$LAB_ROOT/root/usr/share/bison"
export QEMU_MODULE_DIR="$LAB_ROOT/root/usr/lib/x86_64-linux-gnu/qemu"

echo "LAB_ROOT=$LAB_ROOT"
echo "KERNEL_SRC=$KERNEL_SRC"
echo "KERNEL_BUILD=$KERNEL_BUILD"
