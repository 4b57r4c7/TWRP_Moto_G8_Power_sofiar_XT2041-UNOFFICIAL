#!/usr/bin/env python3
"""
Декомпресира .gz ramdisk и разархивира cpio (newc формат) архива вътре.
Чист Python, без cpio.exe/7zip/други външни инструменти.

Употреба: python3 extract_ramdisk.py recovery-ramdisk.gz
Създава папка ramdisk_extracted/ с всички файлове, и директно принтира
съдържанието на всеки файл, съдържащ "fstab" в името.
"""
import gzip
import os
import sys


def parse_cpio_newc(data: bytes):
    """Парсва cpio (newc) изцяло в паметта - връща списък от (name, mode, content).
    Не пипа файловата система изобщо, за да избегне Windows-специфични проблеми
    (device nodes, symlink-ове, запазени имена като 'nul', case-insensitive колизии)."""
    pos = 0
    entries = []

    while pos < len(data):
        if data[pos:pos + 6] not in (b"070701", b"070702"):
            break

        header = data[pos:pos + 110]
        mode = int(header[14:22], 16)
        namesize = int(header[94:102], 16)
        filesize = int(header[54:62], 16)

        name_start = pos + 110
        name_end = name_start + namesize
        name = data[name_start:name_end - 1].decode(errors="replace")

        header_and_name_len = 110 + namesize
        pad = (4 - (header_and_name_len % 4)) % 4
        data_start = name_end + pad
        data_end = data_start + filesize

        if name == "TRAILER!!!":
            break

        content = data[data_start:data_end]
        pad2 = (4 - (filesize % 4)) % 4
        pos = data_end + pad2

        entries.append((name, mode, content))

    return entries


def main(path: str):
    print(f"Чета {path} ...")
    with open(path, "rb") as f:
        raw = f.read()

    if path.endswith(".gz") or raw[:2] == b"\x1f\x8b":
        print("Декомпресирам gzip ...")
        data = gzip.decompress(raw)
    else:
        data = raw

    entries = parse_cpio_newc(data)

    print(f"\nИзвлечени {len(entries)} записа (само в паметта, нищо не е писано на диска)\n")
    print("=== Пълен списък с файлове ===")
    for name, mode, content in entries:
        print(f"  {name}  ({len(content)} bytes, mode={oct(mode)})")

    print("\n=== Файлове с 'fstab' в името ===")
    found_any = False
    for name, mode, content in entries:
        if "fstab" in name.lower():
            found_any = True
            print(f"\n--- {name} ---")
            try:
                text = content.decode(errors="replace")
                print(text)
            except Exception as e:
                print(f"(не успях да декодирам като текст: {e})")
                continue
            # записваме само тези конкретни малки файлове на диска, safe имена
            safe_name = os.path.basename(name).replace(":", "_")
            with open(f"extracted_{safe_name}", "w", encoding="utf-8", errors="replace") as f:
                f.write(text)
            print(f"(записан локално като extracted_{safe_name})")

    if not found_any:
        print("Нищо не намерих с 'fstab' в името. Проверявам init.rc/init.recovery.*.rc "
              "файловете за 'mount'/'fstab' споменавания...\n")
        for name, mode, content in entries:
            base = os.path.basename(name).lower()
            if base.startswith("init") and base.endswith(".rc"):
                try:
                    text = content.decode(errors="replace")
                except Exception:
                    continue
                if "mount" in text.lower() or "fstab" in text.lower():
                    print(f"\n--- {name} (съдържа mount/fstab споменавания) ---")
                    print(text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Употреба: python3 extract_ramdisk.py recovery-ramdisk.gz")
        sys.exit(1)
    main(sys.argv[1])
