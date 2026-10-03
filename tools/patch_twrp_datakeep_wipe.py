#!/usr/bin/env python3
"""
sofiar: Format Data / Wipe Data да работят въпреки /datakeep.

/datakeep (datakeep.sh) държи userdata монтиран, за да не се губят FBE
ключовете при демонтиране на /data. Но mkfs (Format Data) отказва "busy",
докато дялът е монтиран някъде. Пачът освобождава /datakeep точно преди
wipe/format на /data (само тогава). Ключовете вече не са нужни, защото
данните така или иначе се изтриват.

Употреба: python3 patch_twrp_datakeep_wipe.py ~/twrp/bootable/recovery/partition.cpp
"""
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()

if "sofiar: released /datakeep" in src:
    print("Вече е пачнато")
    sys.exit(0)

RELEASE = (
    '\tif (Mount_Point == "/data" && umount2("/datakeep", MNT_DETACH) == 0)\n'
    '\t\tLOGINFO("sofiar: released /datakeep for wipe\\n");\n'
)

anchors = [
    ("bool TWPartition::Wipe(string New_File_System) {\n"
     "\tbool wiped = false, update_crypt = false, recreate_media = true;\n"
     "\tint check;\n", "Wipe(string)"),
    ("bool TWPartition::Wipe_Encryption() {\n"
     "\tbool Save_Data_Media = Has_Data_Media;\n"
     "\tbool ret = false;\n"
     "\tBasePartition* base_partition = make_partition();\n", "Wipe_Encryption()"),
]

for old, what in anchors:
    n = src.count(old)
    if n != 1:
        sys.exit(f"ГРЕШКА: '{what}' намерено {n} пъти (очаквано 1)")
    src = src.replace(old, old + RELEASE)

if "#include <sys/mount.h>" not in src:
    sys.exit("ГРЕШКА: липсва #include <sys/mount.h>")

open(path, "w", encoding="utf-8").write(src)
print("partition.cpp пачнат (/datakeep се освобождава преди wipe/format на /data)")
