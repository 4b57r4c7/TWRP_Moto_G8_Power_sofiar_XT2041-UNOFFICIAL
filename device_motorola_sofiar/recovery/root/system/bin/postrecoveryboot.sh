#!/system/bin/sh
# sofiar TWRP - пуска се от TWRP при всеки boot.
#
# 1) Тъч: драйверът (focaltech_0flash_mmi / nova_0flash_mmi) е vendor модул,
#    а "0flash" контролерът иска фърмуер от /vendor/firmware при всяко пускане.
#    Монтираме vendor САМО ЗА ЧЕТЕНЕ във временна папка, копираме тъч фърмуера
#    в RAM (ramdisk /vendor/firmware и /lib/firmware), зареждаме модулите
#    (първо зависимостите им от modules.dep) и демонтираме vendor.
# 2) Диагностика (временно): 30 сек. след старта записва USB/тъч състоянието в
#    kernel лога (/dev/kmsg). Оцелява при рестарт (pstore) и се чете от Android
#    с `adb bugreport` (секция LAST KMSG).
# Нищо не се записва по дяловете на телефона.

LOG() { echo "<3>TWDBG: $*" > /dev/kmsg; }

SLOT=$(getprop ro.boot.slot_suffix)
VDEV=/dev/block/mapper/vendor$SLOT
VND=/tmp/vendor_ro
mkdir -p $VND /vendor/firmware /lib/firmware

if mount -t ext4 -o ro $VDEV $VND; then
  LOG "vendor mounted ro from $VDEV"
  ls $VND/firmware | head -n 150 | while IFS= read -r l; do LOG "vendor fw: $l"; done
  for f in $(ls $VND/firmware | grep -iE 'focal|fts|ft[0-9]|nvt|nova'); do
    cp -r $VND/firmware/$f /vendor/firmware/
    cp -r $VND/firmware/$f /lib/firmware/
    LOG "fw copied: $f"
  done
  MD=$VND/lib/modules
  for m in focaltech_0flash_mmi nova_0flash_mmi; do
    deps=$(grep "/$m.ko:" $MD/modules.dep | cut -d: -f2)
    order=""
    for d in $deps; do order="$(basename $d) $order"; done
    for d in $order $m.ko; do
      out=$(insmod $MD/$d 2>&1)
      LOG "insmod $d: ${out:-ok}"
    done
  done
  umount $VND
else
  LOG "vendor mount FAILED: $VDEV"
  ls /dev/block/mapper 2>&1 | while IFS= read -r l; do LOG "mapper: $l"; done
fi

(
  sleep 30
  {
    echo "=== props"
    getprop | grep -E "usb|adb|debuggable|selinux|ro.hardware|twrp|slot_suffix"
    echo "=== udc: $(ls /sys/class/udc 2>&1) / UDC=$(cat /config/usb_gadget/g1/UDC 2>&1)"
    echo "=== ffs"
    ls -l /dev/usb-ffs/adb 2>&1
    echo "=== gadget b.1"
    ls -l /config/usb_gadget/g1/configs/b.1 2>&1
    echo "=== getenforce: $(getenforce 2>&1)"
    echo "=== cmdline"
    tr ' ' '\n' < /proc/cmdline | grep -E "selinux|buildvariant|usb"
    echo "=== input"
    grep -E "Name=" /proc/bus/input/devices
    echo "=== modules"
    cut -d' ' -f1 /proc/modules
    echo "=== dmesg"
    dmesg | grep -iE "fts|focal|nvt|nova|touch|firmware|dwc3|udc|gadget|ffs|avc:" | tail -n 80
    echo "=== recovery.log"
    grep -iE "error|fail|unable|firmware|usb" /tmp/recovery.log | tail -n 60
    echo "=== END"
  } 2>&1 | while IFS= read -r l; do echo "<3>TWDBG: $l" > /dev/kmsg; done
) </dev/null >/dev/null 2>&1 &

exit 0
