#!/system/bin/sh
# sofiar TWRP - държи userdata монтиран в /datakeep (виж init.recovery.usb.rc).
# Пуска се синхронно от init ("exec" в "on fs"), преди TWRP да стартира.
# Само монтира; нищо не се записва по дяла.

LOG() { echo "<3>TWDBG: datakeep: $*" > /dev/kmsg; }

DEV=""
i=0
while [ $i -lt 100 ]; do
  for d in /dev/block/bootdevice/by-name/userdata /dev/block/by-name/userdata \
           /dev/block/platform/soc/*/by-name/userdata /dev/block/platform/*/by-name/userdata; do
    if [ -e "$d" ]; then DEV=$d; break; fi
  done
  [ -n "$DEV" ] && break
  sleep 0.1
  i=$((i + 1))
done

if [ -z "$DEV" ]; then
  LOG "userdata not found after $i tries"
  ls /dev/block 2>&1 | while IFS= read -r l; do LOG "dev/block: $l"; done
  exit 0
fi

LOG "found $DEV after $i tries"
mkdir -p /datakeep
out=$(mount -t f2fs -o rw,noatime,nosuid,nodev,discard,nobarrier,inlinecrypt "$DEV" /datakeep 2>&1)
LOG "mount rc=$? ${out}"
grep datakeep /proc/mounts | while IFS= read -r l; do LOG "mounts: $l"; done
exit 0
