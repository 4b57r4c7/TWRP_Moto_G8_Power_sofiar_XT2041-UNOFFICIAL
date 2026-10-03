#!/system/bin/sh
# sofiar TWRP - пуска се от TWRP при всеки boot.
#
# Тъч: драйверът (focaltech_0flash_mmi / nova_0flash_mmi) е vendor модул,
# а "0flash" контролерът иска фърмуер от /vendor/firmware при всяко пускане.
# Монтираме vendor САМО ЗА ЧЕТЕНЕ във временна папка, копираме тъч фърмуера
# в RAM (ramdisk /vendor/firmware и /lib/firmware), зареждаме модулите
# (първо зависимостите им от modules.dep) и демонтираме vendor.
# Нищо не се записва по дяловете на телефона. Лог: dmesg | grep TWDBG

LOG() { echo "<6>TWDBG: $*" > /dev/kmsg; }

SLOT=$(getprop ro.boot.slot_suffix)
VDEV=/dev/block/mapper/vendor$SLOT
VND=/tmp/vendor_ro
mkdir -p $VND /vendor/firmware /lib/firmware

if mount -t ext4 -o ro $VDEV $VND; then
  for f in $(ls $VND/firmware | grep -iE 'focal|fts|ft[0-9]|nvt|nova'); do
    cp -r $VND/firmware/$f /vendor/firmware/
    cp -r $VND/firmware/$f /lib/firmware/
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
fi

exit 0
