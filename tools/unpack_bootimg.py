#!/usr/bin/env python3
"""
Извлича kernel + ramdisk от Android boot image (boot.img / recovery.img).
Работи чисто на Python, без нужда от abootimg/AIK/други външни инструменти.

Автоматично претърсва целия файл за 'ANDROID!' сигнатурата (не само offset 0),
за да поглъща какъвто и да е proprietary wrapper (напр. Motorola SIN формат)
преди реалния boot image header.

Употреба: python3 unpack_bootimg.py recovery.img
Създава: <name>-kernel, <name>-ramdisk.<gz|lz4|xz|cpio|bin>
"""
import struct
import sys
import os


def find_all(data: bytes, sig: bytes):
    offs = []
    i = 0
    while True:
        i = data.find(sig, i)
        if i == -1:
            break
        offs.append(i)
        i += 1
    return offs


def pages(size: int, page_size: int) -> int:
    if size == 0:
        return 0
    return ((size + page_size - 1) // page_size) * page_size


def detect_compression(blob: bytes) -> str:
    if blob[:2] == b"\x1f\x8b":
        return "gz"
    if blob[:4] in (b"\x02\x21\x4c\x18", b"\x04\x22\x4d\x18"):
        return "lz4"
    if blob[:6] == b"\xfd7zXZ\x00":
        return "xz"
    if blob[:4] == b"BZh\x39" or blob[:2] == b"BZ":
        return "bz2"
    if blob[:6] in (b"070701", b"070707"):
        return "cpio"
    return "bin"


def main(path: str):
    with open(path, "rb") as f:
        data = f.read()

    candidates = find_all(data, b"ANDROID!")
    if not candidates:
        print("!! Не намерих 'ANDROID!' сигнатура никъде във файла.")
        print("   Първите 32 байта (hex):", data[:32].hex())
        print("   Форматът вероятно е нещо различно от стандартен AOSP boot image.")
        return

    print(f"Намерих 'ANDROID!' сигнатура на позиции: {candidates}")
    base = candidates[0]
    if len(candidates) > 1:
        print("(Повече от едно място - използвам първото. Ако резултатът изглежда "
              "грешен, кажи ми - ще пробваме следващото.)")
    print(f"Използвам raw file offset {base} като начало на header-а.\n")

    h = data[base:base + 1660]  # достатъчно за header v0/v1/v2
    if len(h) < 1632:
        print("!! Файлът е твърде къс след намерения offset за пълен header.")
        return

    kernel_size    = struct.unpack_from("<I", h, 8)[0]
    kernel_addr    = struct.unpack_from("<I", h, 12)[0]
    ramdisk_size   = struct.unpack_from("<I", h, 16)[0]
    ramdisk_addr   = struct.unpack_from("<I", h, 20)[0]
    second_size    = struct.unpack_from("<I", h, 24)[0]
    second_addr    = struct.unpack_from("<I", h, 28)[0]
    tags_addr      = struct.unpack_from("<I", h, 32)[0]
    page_size      = struct.unpack_from("<I", h, 36)[0]
    header_version = struct.unpack_from("<I", h, 40)[0]
    os_version_raw = struct.unpack_from("<I", h, 44)[0]
    name           = h[48:64].split(b"\x00")[0].decode(errors="ignore")
    cmdline        = h[64:64 + 512].split(b"\x00")[0].decode(errors="ignore")
    extra_cmdline  = h[608:608 + 1024].split(b"\x00")[0].decode(errors="ignore")

    print("=== Boot image header ===")
    print(f"header_version : {header_version}")
    print(f"page_size      : {page_size}")
    print(f"kernel_size    : {kernel_size}   kernel_addr : {hex(kernel_addr)}")
    print(f"ramdisk_size   : {ramdisk_size}   ramdisk_addr: {hex(ramdisk_addr)}")
    print(f"second_size    : {second_size}   second_addr : {hex(second_addr)}")
    print(f"tags_addr      : {hex(tags_addr)}")
    print(f"name           : {name!r}")
    print(f"cmdline        : {cmdline!r}")
    if extra_cmdline:
        print(f"extra_cmdline  : {extra_cmdline!r}")

    if page_size == 0 or page_size > len(data):
        print("!! page_size изглежда невалиден - нещо не е наред с намерения offset.")
        return

    offset = base + page_size
    kernel_start = offset
    offset += pages(kernel_size, page_size)
    ramdisk_start = offset
    offset += pages(ramdisk_size, page_size)
    second_start = offset
    offset += pages(second_size, page_size)

    if header_version >= 1 and len(h) >= 1648:
        recovery_dtbo_size = struct.unpack_from("<I", h, 1632)[0]
        recovery_dtbo_offset = struct.unpack_from("<Q", h, 1636)[0]
        print(f"recovery_dtbo_size  : {recovery_dtbo_size}")
        print(f"recovery_dtbo_offset: {hex(recovery_dtbo_offset)}")
    if header_version >= 2 and len(h) >= 1660:
        dtb_size = struct.unpack_from("<I", h, 1648)[0]
        dtb_addr = struct.unpack_from("<Q", h, 1652)[0]
        print(f"dtb_size            : {dtb_size}")
        print(f"dtb_addr            : {hex(dtb_addr)}")

    out_prefix = os.path.splitext(os.path.basename(path))[0]

    kernel_blob = data[kernel_start:kernel_start + kernel_size]
    kernel_path = f"{out_prefix}-kernel"
    with open(kernel_path, "wb") as f:
        f.write(kernel_blob)
    print(f"\nЗаписах kernel  -> {kernel_path}  ({len(kernel_blob)} bytes)")

    ramdisk_blob = data[ramdisk_start:ramdisk_start + ramdisk_size]
    ext = detect_compression(ramdisk_blob)
    ramdisk_path = f"{out_prefix}-ramdisk.{ext}"
    with open(ramdisk_path, "wb") as f:
        f.write(ramdisk_blob)
    print(f"Записах ramdisk -> {ramdisk_path}  ({len(ramdisk_blob)} bytes, "
          f"детектирана компресия: {ext})")

    print("\nГотово. Прати ми целия този изход - следващата стъпка зависи от "
          "детектираната компресия на ramdisk-а.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Употреба: python3 unpack_bootimg.py <recovery.img или boot.img>")
        sys.exit(1)
    main(sys.argv[1])
