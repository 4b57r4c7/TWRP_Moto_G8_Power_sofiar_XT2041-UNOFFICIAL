#!/usr/bin/env python3
"""
Парсва суров GPT partition table dump (напр. gpt.bin от Motorola firmware zip).
Извлича имена, начален/краен LBA и размер на всеки дял.

Употреба: python3 parse_gpt.py gpt.bin
"""
import struct
import sys

SECTOR_SIZE = 512


def find_all_gpt_headers(data: bytes):
    """Претърсва целия файл за 'EFI PART' сигнатурата - навсякъде, не само
    на очакваните offset-и. Motorola понякога слага проприетарен wrapper
    (SIN формат) с непредвидим размер преди реалната GPT."""
    offsets = []
    start = 0
    while True:
        idx = data.find(b"EFI PART", start)
        if idx == -1:
            break
        offsets.append(idx)
        start = idx + 1
    return offsets


def parse_gpt(path: str):
    with open(path, "rb") as f:
        data = f.read()

    candidates = find_all_gpt_headers(data)
    if not candidates:
        print("!! Не намерих 'EFI PART' signature никъде във файла.")
        print("   Първите 16 байта на файла (hex):", data[:16].hex())
        print("   Файлът вероятно е изцяло в проприетарен Motorola SIN формат,")
        print("   не просто с малък header отпред. Прати `file gpt.bin` и `xxd gpt.bin | head -c 200`.")
        return

    print(f"Намерих 'EFI PART' сигнатура на {len(candidates)} място(а) в суровия файл: {candidates}\n")

    # Взимаме първото срещане като primary GPT header
    header_raw_offset = candidates[0]
    header = data[header_raw_offset:header_raw_offset + 92]

    current_lba = struct.unpack("<Q", header[24:32])[0]
    entries_lba = struct.unpack("<Q", header[72:80])[0]
    num_entries = struct.unpack("<I", header[80:84])[0]
    entry_size = struct.unpack("<I", header[84:88])[0]

    # current_lba обикновено е 1 (header-ът стандартно седи на LBA1).
    # base_offset = къде във файла би бил LBA0, изчислено обратно от
    # реалната позиция на header-а. Това поглъща какъвто и да е wrapper
    # с произволен размер преди истинската GPT.
    base_offset = header_raw_offset - current_lba * SECTOR_SIZE

    print(f"GPT header намерен на raw file offset {header_raw_offset}")
    print(f"Header декларира current_lba={current_lba} -> изчислен base_offset (LBA0) = {base_offset}")
    if base_offset != 0:
        print(f"(Т.е. wrapper/header отпред на реалната GPT е с размер {base_offset} байта - това е нормално за Motorola SIN формат)\n")
    else:
        print()

    print(f"Partition entries: {num_entries}, entry size: {entry_size} bytes, "
          f"entries начинат от LBA {entries_lba}\n")

    entries_offset = base_offset + entries_lba * SECTOR_SIZE

    print(f"{'Name':<24}{'Start LBA':<14}{'End LBA':<14}{'Size (MB)':<12}")
    print("-" * 64)

    total_mb = 0.0
    for i in range(num_entries):
        off = entries_offset + i * entry_size
        if off + entry_size > len(data):
            break
        entry = data[off:off + entry_size]
        type_guid = entry[0:16]
        if type_guid == b"\x00" * 16:
            continue  # празен entry

        first_lba = struct.unpack("<Q", entry[32:40])[0]
        last_lba = struct.unpack("<Q", entry[40:48])[0]
        name_raw = entry[56:128]
        name = name_raw.decode("utf-16-le", errors="ignore").rstrip("\x00")
        size_mb = (last_lba - first_lba + 1) * SECTOR_SIZE / (1024 * 1024)
        total_mb += size_mb

        print(f"{name:<24}{first_lba:<14}{last_lba:<14}{size_mb:<12.2f}")

    print("-" * 64)
    print(f"Общо: {total_mb:.2f} MB покрити от именувани дялове в тази GPT")


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "gpt.bin"
    parse_gpt(p)
