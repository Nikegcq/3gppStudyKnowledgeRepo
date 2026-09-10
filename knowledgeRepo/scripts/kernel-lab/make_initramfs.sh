#!/bin/bash
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh" >/dev/null
LAB_ROOT="${LAB_ROOT:-/home/congqiang/work/repo/tools/kernel-lab}"
INITRAMFS="$LAB_ROOT/initramfs"
OUT="$LAB_ROOT/initramfs.cpio.gz"

rm -rf "$INITRAMFS"
mkdir -p "$INITRAMFS"/{bin,dev,proc,sys,tmp}

cp /usr/bin/busybox "$INITRAMFS/bin/busybox"
for applet in sh mount cat echo ls dmesg poweroff reboot sleep uname; do
	ln -sf busybox "$INITRAMFS/bin/$applet"
done

cp "$HERE/init" "$INITRAMFS/init"
chmod +x "$INITRAMFS/init"

(cd "$INITRAMFS" && find . | cpio -o -H newc | gzip -9 > "$OUT")
ls -lh "$OUT"
