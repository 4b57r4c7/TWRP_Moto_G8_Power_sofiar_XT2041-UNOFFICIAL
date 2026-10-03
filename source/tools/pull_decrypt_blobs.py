#!/usr/bin/env python3
"""
Дърпа от ТЕЛЕФОНА vendor файловете, нужни за декриптиране на /data в TWRP:
qseecomd, keymaster 4.0 и gatekeeper 1.0 (+ техните .so зависимости, които
TWRP няма) и VINTF manifest-а. Така блобовете са точно от твоя vendor, а не
от чуждо устройство.

Изисква: TWRP пуснат с `fastboot boot` и `adb devices` да показва "recovery"
(там adb е root). Дяловете system/vendor се монтират САМО ЗА ЧЕТЕНЕ във /tmp
и после се демонтират - нищо на телефона не се променя.

Употреба (от root-а на repo-то):
  python tools\\pull_decrypt_blobs.py device_motorola_sofiar
"""
import os
import shutil
import struct
import subprocess
import sys

ADB = r"C:\Program Files\SDK-adb\adb.exe"
if not os.path.exists(ADB):
    ADB = shutil.which("adb") or "adb"

# vendor път -> папка в recovery/root (twrp-common иска услугите в system/bin)
ROOT_FILES = {
    "bin/qseecomd": "system/bin",
    "bin/hw/android.hardware.keymaster@4.0-service-qti": "system/bin",
    "bin/hw/android.hardware.gatekeeper@1.0-service-qti": "system/bin",
    "lib64/hw/android.hardware.gatekeeper@1.0-impl-qti.so": "vendor/lib64/hw",
}
# qseecomd зарежда "listener" библиотеките с dlopen (не са в NEEDED)
LISTENER_LIBS = [
    "libdrmfs.so", "libdrmtime.so", "librpmb.so", "libssd.so",
    "libGPreqcancel.so", "libGPreqcancel_svc.so", "libsecureui_svcsock.so",
    "libSecureUILib.so", "libStDrvInt.so", "libops.so", "libqisl.so",
    "libtime_genoff.so", "vendor.qti.hardware.tui_comm@1.0.so", "libqcbor.so",
    "libdiag.so", "libQSEEComAPI.so",
]

VB, SB = "/tmp/vb", "/tmp/sb"


def run(*args):
    return subprocess.run([ADB, *args], capture_output=True, text=True, errors="replace")


def sh(cmd):
    return run("shell", cmd).stdout


def needed(path):
    """DT_NEEDED записите от ELF64 файл (чист Python, без readelf)."""
    d = open(path, "rb").read()
    if d[:4] != b"\x7fELF" or d[4] != 2:
        return []

    def cstr(off):
        return d[off:d.index(b"\0", off)].decode(errors="replace")

    shoff = struct.unpack_from("<Q", d, 0x28)[0]
    shentsize, shnum = struct.unpack_from("<HH", d, 0x3A)
    if shoff and shnum:
        secs = [struct.unpack_from("<IIQQQQIIQQ", d, shoff + i * shentsize) for i in range(shnum)]
        for s in secs:
            if s[1] == 6:  # SHT_DYNAMIC
                stroff = secs[s[6]][4]
                out = []
                for j in range(0, s[5], 16):
                    tag, val = struct.unpack_from("<qQ", d, s[4] + j)
                    if tag == 0:
                        break
                    if tag == 1:
                        out.append(cstr(stroff + val))
                return out
    # без section headers - през program headers
    phoff = struct.unpack_from("<Q", d, 0x20)[0]
    phentsize, phnum = struct.unpack_from("<HH", d, 0x36)
    phs = [struct.unpack_from("<IIQQQQQQ", d, phoff + i * phentsize) for i in range(phnum)]

    def v2o(v):
        for p in phs:
            if p[0] == 1 and p[3] <= v < p[3] + p[5]:
                return v - p[3] + p[2]
        return None

    for p in phs:
        if p[0] == 2:  # PT_DYNAMIC
            vals, strtab = [], None
            for j in range(0, p[5], 16):
                tag, val = struct.unpack_from("<qQ", d, p[2] + j)
                if tag == 0:
                    break
                if tag == 1:
                    vals.append(val)
                elif tag == 5:
                    strtab = v2o(val)
            return [cstr(strtab + v) for v in vals] if strtab is not None else []
    return []


def main(dev_dir):
    state = run("get-state").stdout.strip()
    if state != "recovery":
        print(f"!! adb състояние е '{state or 'няма устройство'}', трябва 'recovery' (TWRP с fastboot boot).")
        sys.exit(1)

    root = os.path.join(dev_dir, "recovery", "root")
    slot = sh("getprop ro.boot.slot_suffix").strip()
    print(f"Slot: {slot}")
    sh(f"mkdir -p {VB} {SB}; "
       f"mountpoint -q {VB} || mount -t ext4 -o ro /dev/block/mapper/vendor{slot} {VB}; "
       f"mountpoint -q {SB} || mount -t ext4 -o ro /dev/block/mapper/system{slot} {SB}")
    try:
        ven_libs = set(sh(f"ls {VB}/lib64").split())
        if not ven_libs:
            print("!! vendor не се монтира (празен /tmp/vb/lib64). Спирам.")
            sys.exit(1)
        twrp_libs = set(sh("ls /system/lib64").split())
        sys_libs = set(sh(f"ls {SB}/system/lib64").split())

        queue = list(ROOT_FILES.items())
        queue += [(f"lib64/{n}", "vendor/lib64") for n in LISTENER_LIBS]
        done, pulled, from_system, missing, skipped = set(), [], [], set(), set()

        while queue:
            rel, dest_dir = queue.pop(0)
            if rel in done:
                continue
            done.add(rel)
            base = SB if rel.startswith("system/") else VB
            local = os.path.join(root, dest_dir, os.path.basename(rel))
            os.makedirs(os.path.dirname(local), exist_ok=True)
            r = run("pull", f"{base}/{rel}", local)
            if r.returncode != 0 or not os.path.exists(local):
                print(f"   (няма на телефона: /{'system' if base == SB else 'vendor'}/{rel})")
                continue
            pulled.append(f"{dest_dir}/{os.path.basename(rel)}")
            for lib in needed(local):
                if lib in twrp_libs:
                    skipped.add(lib)
                elif lib in ven_libs:
                    queue.append((f"lib64/{lib}", "vendor/lib64"))
                elif lib in sys_libs:
                    from_system.append(lib)
                    queue.append((f"system/lib64/{lib}", "system/lib64"))
                else:
                    missing.add(lib)

        man = os.path.join(root, "vendor", "etc", "vintf", "manifest.xml")
        os.makedirs(os.path.dirname(man), exist_ok=True)
        if run("pull", f"{VB}/etc/vintf/manifest.xml", man).returncode == 0:
            txt = open(man, encoding="utf-8", errors="replace").read()
            pulled.append("vendor/etc/vintf/manifest.xml")
            for hal in ("android.hardware.keymaster", "android.hardware.gatekeeper"):
                print(f"manifest съдържа {hal}: {'ДА' if hal in txt else 'НЕ'}")

        def prop(path, key):
            for line in sh(f"grep -m1 '^{key}=' {path}").splitlines():
                return line.split("=", 1)[1].strip()
            return "?"

        print("\n=== Версии (за BoardConfig) ===")
        print("ro.build.version.release        =", prop(f"{SB}/system/build.prop", "ro.build.version.release"))
        print("ro.build.version.security_patch =", prop(f"{SB}/system/build.prop", "ro.build.version.security_patch"))
        print("ro.vendor.build.security_patch  =", prop(f"{VB}/build.prop", "ro.vendor.build.security_patch"))

        print(f"\n=== Изтеглени ({len(pulled)}) ===")
        for p in sorted(pulled):
            print("  " + p)
        if from_system:
            print("\nВзети от /system на телефона (TWRP ги няма):", ", ".join(sorted(set(from_system))))
        if missing:
            print("\n!! НЕ са намерени никъде:", ", ".join(sorted(missing)))
        print(f"\n(TWRP вече има {len(skipped)} от нужните библиотеки - не са копирани)")
    finally:
        sh(f"umount {VB}; umount {SB}")
        print("\nvendor/system демонтирани. Готово.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
