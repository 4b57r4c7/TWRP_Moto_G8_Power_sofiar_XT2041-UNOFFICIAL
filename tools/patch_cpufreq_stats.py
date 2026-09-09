#!/usr/bin/env python3
"""
Patch за kernel съвместимост: cpufreq_stats_update() е void функция,
но съдържа 'return 0;' вместо просто 'return;' (kernel backport бъг,
несъвместим с по-строгия clang -Wreturn-type като error).

Употреба: python3 patch_cpufreq_stats.py <път до cpufreq_stats.c>
"""
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Употреба: python3 patch_cpufreq_stats.py <път до cpufreq_stats.c>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"ГРЕШКА: файлът {p} не съществува!")
        sys.exit(1)

    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")

    start_idx = None
    for i, line in enumerate(lines):
        if "void" in line and re.search(r"\bcpufreq_stats_update\s*\(", line):
            start_idx = i
            break

    if start_idx is None:
        print("ГРЕШКА: не намерих дефиницията на cpufreq_stats_update - "
              "спирам без промяна.")
        sys.exit(1)

    end_idx = None
    for i in range(start_idx, len(lines)):
        if lines[i].strip() == "}" and not lines[i].startswith((" ", "\t")):
            end_idx = i
            break

    if end_idx is None:
        print("ГРЕШКА: не намерих края на функцията (затваряща скоба на "
              "ниво 0) - спирам без промяна.")
        sys.exit(1)

    print(f"Функцията cpufreq_stats_update е между редове "
          f"{start_idx + 1} и {end_idx + 1}.")

    replaced = 0
    for i in range(start_idx, end_idx + 1):
        if re.match(r"^\s*return\s+0\s*;\s*$", lines[i]):
            indent = re.match(r"^(\s*)", lines[i]).group(1)
            print(f"  Ред {i + 1}: '{lines[i].strip()}' -> 'return;'")
            lines[i] = f"{indent}return;"
            replaced += 1

    if replaced == 0:
        print("ГРЕШКА: не намерих 'return 0;' в тялото на функцията - "
              "спирам без промяна, нужна е ръчна проверка.")
        sys.exit(1)

    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: заменени {replaced} 'return 0;' с 'return;' в "
          f"cpufreq_stats_update.")


if __name__ == "__main__":
    main()
