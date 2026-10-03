#!/usr/bin/env python3
"""
Patch за kernel съвместимост: sde_connector.c използва 'dsi_display'
като локална променлива на ред ~2501, но никога не я декларира - редът
'dsi_display = (struct dsi_display *)(display);' пропуска типа
'struct dsi_display *' пред името на променливата (недовършен backport,
същия клас бъг като vmscan/cpufreq_stats по-рано).

Употреба: python3 patch_sde_connector.py <път до sde_connector.c>
"""
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Употреба: python3 patch_sde_connector.py <път до sde_connector.c>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"ГРЕШКА: файлът {p} не съществува!")
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    # Диагностика: покажи всички редове, съдържащи 'dsi_display = (struct'
    matches_preview = re.findall(r"^.*dsi_display\s*=\s*\(struct.*$", text, re.MULTILINE)
    print(f"Намерени {len(matches_preview)} реда с 'dsi_display = (struct...':")
    for i, m in enumerate(matches_preview):
        print(f"  [{i}] {m.strip()}")

    if re.search(r"struct\s+dsi_display\s*\*\s*dsi_display\s*=\s*\(struct\s+dsi_display\s*\*\)\s*\(display\)\s*;", text):
        print("Редът вече изглежда пачнат (типът вече присъства) - нищо не правя.")
        sys.exit(0)

    pattern = re.compile(
        r"(?<![\w*])dsi_display\s*=\s*\(struct\s+dsi_display\s*\*\)\s*\(display\)\s*;"
    )
    matches = list(pattern.finditer(text))
    if len(matches) == 0:
        print("ГРЕШКА: не намерих бъгавия ред никъде - спирам без промяна, "
              "нужна е ръчна проверка на файла.")
        sys.exit(1)

    print(f"Ще поправя {len(matches)} срещане(ия) на бъгавия ред "
          f"(всяко е в отделна функция, поправката е независима за всяко).")

    # Заменяме отзад напред, за да не се разместват индексите на
    # по-ранните съвпадения при всяка вложена замяна.
    for m in reversed(matches):
        old = m.group(0)
        new = "struct dsi_display *" + old
        text = text[:m.start()] + new + text[m.end():]
        print(f"  Позиция {m.start()}: '{old}' -> '{new}'")

    p.write_text(text, encoding="utf-8")
    print(f"OK: поправени {len(matches)} срещане(ия).")


if __name__ == "__main__":
    main()
