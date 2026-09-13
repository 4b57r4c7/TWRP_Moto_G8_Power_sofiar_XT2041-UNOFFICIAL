#!/usr/bin/env python3
"""
Patch за kernel dts Makefile: целият файл е обвит в
ifeq($(CONFIG_MMI_DEVICE_DTBS),y) ... else ... endif - истинският
Motorola/sofiar клон никога не се ползва (базовият ни defconfig не
задава този flag), затова build-ът пада в "else" клона, съдържащ
МНОГО чужди reference board dtb-та, part от които crash-ват dtc
(Error 139/SIGSEGV).

Решение: заменяме ЦЯЛАТА ifeq/else/endif структура с твърдо закодирана
версия, съдържаща само sofiar overlay-ите - огледало на оригиналния
Motorola "if" клон, без Kconfig зависимост.

Употреба: python3 patch_dts_makefile.py <път до dts/qcom/Makefile>
"""
import re
import sys
from pathlib import Path

NEW_BLOCK = """# Only include Motorola DTBs (sofiar) - твърдо закодирано,
# заобикаляйки CONFIG_MMI_DEVICE_DTBS Kconfig gate-а (не се задава от
# базовия ни generic defconfig), за да избегнем множеството чужди/
# crash-ващи reference board dtb записи в оригиналния "else" клон.

dtb-y += trinket-sofiar-base.dtb

# Add 1k of padding to the DTBs to allow for environment variables
# to be runtime added by the bootloader (i.e. /chosen properties)
DTC_FLAGS += -p 1024

dtbo-y += \\
\ttrinket-sofiar-evb1-overlay.dtbo \\
\ttrinket-sofiar-evt1-overlay.dtbo \\
\ttrinket-sofiar-evt2-overlay.dtbo \\
\ttrinket-sofiar-dvt1a-overlay.dtbo \\
\ttrinket-sofiar-dvt1b-overlay.dtbo \\
\ttrinket-sofiar-dvt2-overlay.dtbo \\
\ttrinket-sofiar-pvt-overlay.dtbo

trinket-sofiar-evb1-overlay.dtbo-base :=  trinket-sofiar-base.dtb
trinket-sofiar-evt1-overlay.dtbo-base :=  trinket-sofiar-base.dtb
trinket-sofiar-evt2-overlay.dtbo-base :=  trinket-sofiar-base.dtb
trinket-sofiar-dvt1a-overlay.dtbo-base :=  trinket-sofiar-base.dtb
trinket-sofiar-dvt1b-overlay.dtbo-base :=  trinket-sofiar-base.dtb
trinket-sofiar-dvt2-overlay.dtbo-base :=  trinket-sofiar-base.dtb
trinket-sofiar-pvt-overlay.dtbo-base :=  trinket-sofiar-base.dtb
"""


def main():
    if len(sys.argv) < 2:
        print("Употреба: python3 patch_dts_makefile.py <път до dts/qcom/Makefile>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"ГРЕШКА: файлът {p} не съществува!")
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    if "твърдо закодирано" in text or "hardcoded, заобикаляйки" in text:
        print("Файлът вече изглежда пачнат - нищо не правя.")
        sys.exit(0)

    start_marker = "# Only include Motorola DTBs"
    end_marker = "endif # CONFIG_MMI_DEVICE_DTBS"

    start_idx = text.find(start_marker)
    end_marker_idx = text.find(end_marker)

    if start_idx == -1 or end_marker_idx == -1:
        print(f"ГРЕШКА: не намерих очакваните anchor-и "
              f"(start намерен: {start_idx != -1}, "
              f"end намерен: {end_marker_idx != -1}). Спирам без промяна.")
        sys.exit(1)

    end_idx = end_marker_idx + len(end_marker)

    print(f"Заменям блок от позиция {start_idx} до {end_idx} "
          f"({text.count(chr(10), 0, start_idx) + 1} до "
          f"{text.count(chr(10), 0, end_idx) + 1} ред).")

    text = text[:start_idx] + NEW_BLOCK + text[end_idx:]
    p.write_text(text, encoding="utf-8")
    print("OK: заменена цялата ifeq/else/endif структура с sofiar-само версия.")


if __name__ == "__main__":
    main()
