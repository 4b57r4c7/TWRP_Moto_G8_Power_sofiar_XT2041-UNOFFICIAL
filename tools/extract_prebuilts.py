#!/usr/bin/env python3
"""
Извлича kernel + dtb + recovery_dtbo от STOCK recovery.img (header v2)
директно в device tree-то като prebuilt файлове за TWRP build-а.

Употреба (от root-а на repo-то):
  python tools\\extract_prebuilts.py <път\\до\\stock\\recovery.img> device_motorola_sofiar

Създава:
  <device>/prebuilt/kernel
  <device>/prebuilt/dtb/sofiar.dtb
  <device>/prebuilt/recovery_dtbo
"""
import hashlib
import os
import struct
import sys

FDT_MAGIC = b"\xd0\x0d\xfe\xed"
DTBO_MAGIC = b"\xd7\xb7\xab\x1e"


def pages(size, page):
    return (size + page - 1) // page * page


def die(msg):
    print("!! " + msg)
    sys.exit(1)


def main(img_path, dev_dir):
    data = open(img_path, "rb").read()
    base = data.find(b"ANDROID!")
    if base < 0:
        die("Няма 'ANDROID!' сигнатура - това не е boot/recovery image.")

    h = data[base:base + 1660]
    kernel_size, _, ramdisk_size, _, second_size = struct.unpack_from("<5I", h, 8)
    page = struct.unpack_from("<I", h, 36)[0]
    hv = struct.unpack_from("<I", h, 40)[0]
    cmdline = h[64:576].split(b"\0")[0].decode(errors="ignore")
    dtbo_size, dtbo_off_hdr = struct.unpack_from("<IQ", h, 1632)
    dtb_size = struct.unpack_from("<I", h, 1648)[0]

    # Проверки - спираме при каквото и да е несъответствие
    if hv != 2:
        die(f"header_version е {hv}, очаквах 2.")
    if page != 4096:
        die(f"page_size е {page}, очаквах 4096.")
    if "androidboot.hab.product=sofiar" not in cmdline:
        die("cmdline не съдържа 'androidboot.hab.product=sofiar' - грешен файл?")

    off = page
    k_off = off;  off += pages(kernel_size, page)
    off += pages(ramdisk_size, page)
    off += pages(second_size, page)
    o_off = off;  off += pages(dtbo_size, page)
    d_off = off

    if dtbo_off_hdr and dtbo_off_hdr != o_off:
        die(f"recovery_dtbo offset не съвпада (header {dtbo_off_hdr}, изчислен {o_off}).")

    kernel = data[base + k_off: base + k_off + kernel_size]
    dtbo = data[base + o_off: base + o_off + dtbo_size]
    dtb = data[base + d_off: base + d_off + dtb_size]

    if len(kernel) != kernel_size or len(dtbo) != dtbo_size or len(dtb) != dtb_size:
        die("Файлът е по-къс от очакваното (отрязан?).")
    if not dtb.startswith(FDT_MAGIC):
        die("dtb не започва с FDT magic (d00dfeed).")
    if not dtbo.startswith(DTBO_MAGIC):
        die("recovery_dtbo не започва с DT table magic (d7b7ab1e).")

    pre = os.path.join(dev_dir, "prebuilt")
    os.makedirs(os.path.join(pre, "dtb"), exist_ok=True)
    out = {
        os.path.join(pre, "kernel"): kernel,
        os.path.join(pre, "dtb", "sofiar.dtb"): dtb,
        os.path.join(pre, "recovery_dtbo"): dtbo,
    }
    for path, blob in out.items():
        with open(path, "wb") as f:
            f.write(blob)
        print(f"OK  {path}  {len(blob)} B  sha256={hashlib.sha256(blob).hexdigest()[:16]}")
    print("\nГотово.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
