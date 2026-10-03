#!/usr/bin/env python3
"""
Patch за kernel съвместимост: inactive_list_is_low() е декларирана с 4
параметра (lruvec, file, sc, actual) - потвърдено от диагностика - но
на едно място се вика с 5 аргумента (излишен 'memcg', вмъкнат по грешка,
вероятно недовършен backport). Маха излишния аргумент от call site-а.

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

    # Диагностика: покажи всички прости (без nested parens) съвпадения -
    # полезно за преглед, но не е базата за самия patch.
    call_pattern = re.compile(r"inactive_list_is_low\s*\(([^)]*)\)")
    calls = call_pattern.findall(text)
    print(f"Намерени {len(calls)} прости съвпадения на "
          f"'inactive_list_is_low(...)' (декларация + извиквания; "
          f"извиквания с nested скоби може да не се хванат чисто тук):")
    for i, c in enumerate(calls):
        arg_count = len([a for a in c.split(",") if a.strip()])
        preview = " ".join(c.split())[:70]
        print(f"  [{i}] {arg_count} аргумента: {preview}")

    # Точният бъгав call site: излишен 'memcg' аргумент между 'file' и
    # 'sc'. Потвърдено чрез диагностика - декларацията е (lruvec, file,
    # sc, actual), БЕЗ memcg параметър, затова целим самото извикване.
    bad_call_pattern = re.compile(
        r"inactive_list_is_low\s*\(\s*lruvec\s*,\s*true\s*,\s*memcg\s*,\s*sc\s*,\s*false\s*\)"
    )

    if "inactive_list_is_low(lruvec, true, sc, false)" in text:
        print("Call site-ът вече изглежда пачнат - нищо не правя.")
        sys.exit(0)

    matches = list(bad_call_pattern.finditer(text))
    if len(matches) != 1:
        print(f"ГРЕШКА: очаквах точно 1 съвпадение на бъгавия call site, "
              f"намерих {len(matches)}. Спирам без промяна - нужна е "
              f"ръчна проверка на файла.")
        sys.exit(1)

    text = text[:matches[0].start()] + "inactive_list_is_low(lruvec, true, sc, false)" + text[matches[0].end():]
    p.write_text(text, encoding="utf-8")
    print("OK: излишният 'memcg' аргумент е премахнат от call site-а.")


if __name__ == "__main__":
    main()
