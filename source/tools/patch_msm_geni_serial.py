#!/usr/bin/env python3
"""
Patch за kernel съвместимост: wait_for_transfers_inflight() е обявена
като 'static int' и завършва с 'return 0;' на exit label-а, но има
ранен изход с гол 'return;' (без стойност) - несъответствие от
недовършен backport.

Употреба: python3 patch_msm_geni_serial.py <път до msm_geni_serial.c>
"""
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Употреба: python3 patch_msm_geni_serial.py <път до msm_geni_serial.c>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"ГРЕШКА: файлът {p} не съществува!")
        sys.exit(1)

    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")

    start_idx = None
    for i, line in enumerate(lines):
        if "wait_for_transfers_inflight" in line and re.match(r"^\s*static\s+int\s", line):
            start_idx = i
            break

    if start_idx is None:
        print("ГРЕШКА: не намерих дефиницията на wait_for_transfers_inflight "
              "(static int) - спирам без промяна.")
        sys.exit(1)

    end_idx = None
    for i in range(start_idx, len(lines)):
        if lines[i].strip() == "}" and not lines[i].startswith((" ", "\t")):
            end_idx = i
            break

    if end_idx is None:
        print("ГРЕШКА: не намерих края на функцията - спирам без промяна.")
        sys.exit(1)

    print(f"Функцията wait_for_transfers_inflight е между редове "
          f"{start_idx + 1} и {end_idx + 1}.")

    replaced = 0
    for i in range(start_idx, end_idx + 1):
        if re.match(r"^\s*return\s*;\s*$", lines[i]):
            indent = re.match(r"^(\s*)", lines[i]).group(1)
            print(f"  Ред {i + 1}: '{lines[i].strip()}' -> 'return 0;'")
            lines[i] = f"{indent}return 0;"
            replaced += 1

    if replaced == 0:
        print("ГРЕШКА: не намерих гол 'return;' в тялото на функцията - "
              "спирам без промяна, нужна е ръчна проверка.")
        sys.exit(1)

    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: заменени {replaced} гол(и) 'return;' с 'return 0;' в "
          f"wait_for_transfers_inflight.")


if __name__ == "__main__":
    main()
