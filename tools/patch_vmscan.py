#!/usr/bin/env python3
"""
Patch за kernel съвместимост: inactive_list_is_low() в mm/vmscan.c се
извиква с 5 аргумента на едно място, но е декларирана с 4 - несъответствие
от недовършен backport на upstream patch. Добавя липсващия 5-ти параметър
('bool reclaiming') към декларацията.

Употреба: python3 patch_vmscan.py <път до vmscan.c>
"""
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Употреба: python3 patch_vmscan.py <път до vmscan.c>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"ГРЕШКА: файлът {p} не съществува!")
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    # Гъвкав regex вместо точен текст match - устойчив на разлики в
    # whitespace/tabs между различни checkout-и на kernel source-а.
    decl_pattern = re.compile(
        r"static\s+bool\s+inactive_list_is_low\s*\(\s*"
        r"struct\s+lruvec\s*\*\s*lruvec\s*,\s*"
        r"bool\s+file\s*,\s*"
        r"struct\s+mem_cgroup\s*\*\s*memcg\s*,\s*"
        r"struct\s+scan_control\s*\*\s*sc\s*\)",
        re.MULTILINE,
    )

    # Диагностика: покажи ВСИЧКИ места, съвпадащи с извикване на
    # функцията (включително самата декларация), с брой аргументи
    # всяко - за да видим дали има друг call site с различен брой
    # аргументи, преди да пипнем сигнатурата (функцията е static,
    # значи всички извиквания са в този файл).
    call_pattern = re.compile(r"inactive_list_is_low\s*\(([^)]*)\)")
    calls = call_pattern.findall(text)
    print(f"Намерени {len(calls)} съвпадения на 'inactive_list_is_low(...)' "
          f"(декларация + извиквания):")
    for i, c in enumerate(calls):
        arg_count = len([a for a in c.split(",") if a.strip()])
        preview = " ".join(c.split())[:70]
        print(f"  [{i}] {arg_count} аргумента: {preview}")

    if "bool reclaiming" in text:
        print("Декларацията вече изглежда пачната ('bool reclaiming' "
              "присъства) - нищо не правя.")
        sys.exit(0)

    matches = list(decl_pattern.finditer(text))
    if len(matches) != 1:
        print(f"ГРЕШКА: очаквах точно 1 съвпадение на декларацията, "
              f"намерих {len(matches)}. Спирам без промяна - нужна е "
              f"ръчна проверка на файла.")
        sys.exit(1)

    old_decl = matches[0].group(0)
    new_decl = old_decl[:-1] + ",\n\t\t\t\t\tbool reclaiming)"
    text = text[: matches[0].start()] + new_decl + text[matches[0].end():]
    p.write_text(text, encoding="utf-8")
    print("OK: декларацията е обновена успешно с 5-ти параметър "
          "'bool reclaiming'.")


if __name__ == "__main__":
    main()
