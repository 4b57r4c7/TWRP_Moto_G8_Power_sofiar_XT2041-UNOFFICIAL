#!/usr/bin/env python3
"""
Patch за kernel съвместимост: qpnp-smb5.c реферира
TYPE_C_DEBUG_ACCESS_SINK_REG и TYPEC_DEBUG_ACCESS_SINK_MASK, но тези
дефиниции липсват изцяло от smb5-reg.h (недовършен backport).

Стойности, изведени от:
- Числовата последователност на съседните TYPEC_BASE+offset регистри
  в тази конкретна smb5-reg.h (празнина точно на offset 0x4A между
  0x48 и 0x4C) -> REG = (TYPEC_BASE + 0x4A)
- Upstream Qualcomm patch discussion за същия driver, потвърждаващ
  MASK = GENMASK(4, 0) (битова ширина е хардуерна характеристика,
  не зависи от base offset-а)

Употреба: python3 patch_smb5_reg.py <път до smb5-reg.h>
"""
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Употреба: python3 patch_smb5_reg.py <път до smb5-reg.h>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"ГРЕШКА: файлът {p} не съществува!")
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    if "TYPE_C_DEBUG_ACCESS_SINK_REG" in text:
        print("Дефиницията вече изглежда добавена - нищо не правя.")
        sys.exit(0)

    anchor_pattern = re.compile(
        r"^#define\s+DEBUG_ACCESS_SRC_CFG_REG\s+\(TYPEC_BASE\s*\+\s*0x4C\)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    matches = list(anchor_pattern.finditer(text))
    if len(matches) != 1:
        print(f"ГРЕШКА: очаквах точно 1 съвпадение на anchor реда "
              f"(DEBUG_ACCESS_SRC_CFG_REG), намерих {len(matches)}. "
              f"Спирам без промяна.")
        sys.exit(1)

    anchor = matches[0].group(0)
    new_defines = (
        "#define TYPE_C_DEBUG_ACCESS_SINK_REG\t\t(TYPEC_BASE + 0x4A)\n"
        "#define TYPEC_DEBUG_ACCESS_SINK_MASK\t\tGENMASK(4, 0)\n\n"
        + anchor
    )
    text = text[:matches[0].start()] + new_defines + text[matches[0].end():]
    p.write_text(text, encoding="utf-8")
    print("OK: добавени TYPE_C_DEBUG_ACCESS_SINK_REG (TYPEC_BASE + 0x4A) "
          "и TYPEC_DEBUG_ACCESS_SINK_MASK (GENMASK(4, 0)).")


if __name__ == "__main__":
    main()
