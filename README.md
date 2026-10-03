# TWRP for Moto G8 Power (sofiar) — UNOFFICIAL

**[English](#english) · [Български](#български)**

![TWRP](https://img.shields.io/badge/TWRP-3.7.1__12--0-blue)
![Device](https://img.shields.io/badge/device-sofiar%20XT2041--3-orange)
![Android](https://img.shields.io/badge/stock-Android%2011-green)
![Status](https://img.shields.io/badge/status-working-brightgreen)

---

## English

Unofficial TWRP recovery for the **Motorola Moto G8 Power** (`sofiar`, XT2041-3), built entirely in GitHub Actions — no local Linux machine required.

Its main feature is **working FBE decryption with PIN on stock Android 11**. Older unofficial TWRP builds for this device failed at this.

### Status

| Feature | Status |
|---|---|
| Boot (`fastboot boot` and installed in `recovery_a`) | ✅ |
| Display, brightness | ✅ |
| Touchscreen (FocalTech FT8756) | ✅ |
| ADB (root) | ✅ |
| MTP (internal storage + microSD) | ✅ |
| Battery level / charging indicator | ✅ |
| FBE decryption with PIN (stock Android 11) | ✅ |
| Format Data / Wipe Data | ⚠️ patched, not tested on a device yet |
| Vibration | ❌ not supported (no vibrator node exposed) |
| Decrypting custom ROM data (LineageOS etc.) | ❌ not supported |

### Tested on

| | |
|---|---|
| Model | XT2041-3, RETEU |
| Firmware | Android 11, `RPES31.Q4U-47-35-12` |
| Bootloader | `MBM-3.0-sofiar_reteu-0f8934adaf-220131` (unlocked) |
| Kernel used by TWRP | prebuilt, taken from the stock `boot_a` of this build |

Other firmware builds are **not tested**. See [Limitations](#limitations).

### ⚠️ Disclaimer

You use this at your own risk. Unlocking the bootloader and flashing custom recovery can void warranty and, if done wrong, brick the device. **Back up everything first** (see [Backups](#backups)). Never flash bootloader, modem or EFS partitions.

### Requirements

- Unlocked bootloader
- Stock Android 11, build `RPES31.Q4U-47-35-12`
- `adb` and `fastboot` (Android SDK Platform Tools)

### Usage

**1. Test without installing (recommended first).** This runs from RAM and writes nothing to the phone:

```bash
adb reboot bootloader
fastboot boot recovery.img
```

Check that touch works, then enter your PIN and verify that internal storage shows normal folder names (DCIM, Download, …).

**2. Back up the stock recovery** while TWRP is running:

```bash
adb pull /dev/block/bootdevice/by-name/recovery_a recovery_a_stock.img
adb pull /dev/block/bootdevice/by-name/recovery_b recovery_b_stock.img
```

**3. Install** (only to the active slot's recovery; `recovery_b` stays stock as a fallback):

```bash
adb reboot bootloader
fastboot getvar current-slot     # must say: a
fastboot flash recovery_a recovery.img
```

Then select **Recovery mode** in the bootloader menu with the volume keys.

**Restore stock recovery:**

```bash
fastboot flash recovery_a recovery_a_stock.img
```

### Backups

Before touching anything, back up at least:

- `recovery_a/b`, `boot_a`, `vbmeta_a/b`, `dtbo_a/b`
- **EFS / IMEI**: `modemst1`, `modemst2`, `fsg_a`, `fsg_b`, `fsc`, `persist`, plus the Moto partitions `prodpersist`, `utags`, `utagsBackup`, `hw`, `cid`, `sp`. These are **unique to your phone** and cannot be downloaded again.
- The full stock firmware zip for your build.

`tools/save_backups.ps1` (Windows) does all of this read-only from TWRP and verifies every image with SHA-256. Keep the EFS images private: they contain your IMEI.

### Building

Everything runs in GitHub Actions:

1. Fork this repository.
2. **Actions → Build TWRP - sofiar → Run workflow**.
3. Download `recovery.img` from the run's artifacts.

A full build takes about 2–3 hours, mostly `repo sync`. The workflow syncs the TWRP minimal manifest (`twrp-12.1`) plus the SM6125 common tree, copies in this device tree, applies a few workaround patches and runs `mka recoveryimage`.

### Technical notes

How the hard parts were solved, for anyone porting this to a similar device.

<details>
<summary><b>Prebuilt kernel from the device's own boot partition</b></summary>

The touchscreen driver is a vendor kernel module signed with a **per-build key** of the stock kernel. Kernels from the firmware's `recovery.img`, or from a different build, reject it with `Required key not available`. The fix is to use the kernel and dtb extracted from the phone's own `boot_a` (`tools/extract_prebuilts.py`). `recovery_dtbo` comes from the stock recovery.
</details>

<details>
<summary><b>Touchscreen</b></summary>

FocalTech FT8756 (`fts_ts`) on a Tianma panel, driven by `focaltech_0flash_mmi.ko`. The "0flash" controller needs its firmware (`focaltech-ft8756-0e-01-sofiar.bin`) on every power-up. `postrecoveryboot.sh` mounts the vendor partition **read-only**, copies the firmware to the ramdisk, loads the modules in `modules.dep` order and unmounts vendor.
</details>

<details>
<summary><b>FBE keys lost on /data unmount (<code>/datakeep</code>)</b></summary>

The kernel supports `FS_IOC_ADD_ENCRYPTION_KEY`, so FBE keys live in the **filesystem superblock**. TWRP unmounts and remounts `/data` during startup, which destroys the superblock and the keys with it. After that, the PIN screen sees only encrypted file names and cannot find `spblob`.

The fix: `datakeep.sh` (run synchronously by init in `on fs`) mounts userdata a second time at `/datakeep`. That keeps the superblock alive, so the keys survive TWRP's unmount/remount cycles. A small patch to `partition.cpp` releases `/datakeep` right before Format/Wipe Data so `mkfs` does not fail with "busy".
</details>

<details>
<summary><b>Android 11 legacy keystore → keystore2 (<code>key not found</code>)</b></summary>

TWRP 12.1 looks up the synthetic-password key only in **keystore2** (Android 12+). Android 11 keeps it as a legacy keystore blob (`/data/misc/keystore/user_0/1000_USRPKEY_synthetic_password_<handle>`), so decryption failed with `key not found`.

`tools/patch_vold_a11_keystore.py` patches `system/vold/Decrypt.cpp`. On `KEY_NOT_FOUND` it copies the legacy blob into TWRP's tmpfs keystore directory (uid 1000 → 0, because TWRP runs as root) and calls `IKeystoreMaintenance::migrateKeyNamespace`, the same migration Android 12 performs when upgrading from 11. Then it retries. Nothing on `/data` is modified. The patch also stops TWRP from overwriting keystore2's database with an empty file when `persistent.sqlite` does not exist (Android 11).
</details>

<details>
<summary><b>Other fixes</b></summary>

- **fstab split:** `twrp.fstab` (TWRP format) for TWRP, and `recovery.fstab` in AOSP `fs_mgr` format, because vold/fscrypt parse it.
- **TrustZone chain started early:** `crypto.ready=1` is set on `hwservicemanager.ready`, so qseecomd, keymaster and gatekeeper are up before TWRP tries the DE keys.
- **qseecomd library order:** `/system/lib64` is placed before `/vendor/lib` in `LD_LIBRARY_PATH`. Otherwise the 64-bit linker picks a 32-bit `libandroidicu.so`.
- **USB:** a single, device-specific `init.recovery.usb.rc` (configfs, `mtp.gs0` + `ffs.adb`) avoids a UDC rebind loop.
- **Battery:** the supply is `qcom_battery`, not `battery`. TWRP's `Android.mk` checks `TW_USE_LEGACY_BATTERY_SERVICES` *before* `TW_CUSTOM_BATTERY_PATH` sets it, so both must be set explicitly.
</details>

### Limitations

- **Tied to the stock kernel of one firmware build.** After an OTA update, re-extract the kernel from the new `boot` partition and rebuild, or touch will stop working. An OTA will also overwrite the recovery partition.
- Decryption works for **stock Android 11** only. Custom ROMs use different encryption and kernels: touch and decryption will most likely not work there, so use the recovery recommended by the ROM.
- No vibration.

### Repository layout

```
.github/workflows/build-twrp-sofiar.yml   CI build
local_manifest.xml                        SM6125 common tree
device_motorola_sofiar/
  BoardConfig.mk, device.mk, twrp_sofiar.mk, ...
  recovery.fstab                          AOSP fs_mgr format (for vold)
  prebuilt/                               kernel, dtb, recovery_dtbo
  recovery/root/
    init.recovery.usb.rc                  USB gadget, early crypto, /datakeep
    system/bin/postrecoveryboot.sh        touch firmware + modules
    system/bin/datakeep.sh                keeps FBE keys alive
    system/etc/twrp.fstab                 TWRP partition list
    vendor/lib64/                         decryption blobs
tools/                                    extraction, patch and backup scripts
```

### Credits

- [TeamWin](https://github.com/TeamWin) for TWRP
- [minimal-manifest-twrp](https://github.com/minimal-manifest-twrp)
- [trinket-common / teamwin_device_motorola_sm6125-common](https://github.com/trinket-common) for the SM6125 common tree
- Motorola for the stock firmware blobs

### License

TWRP is licensed under GPLv3. The scripts and configuration in this repository are provided as-is, without warranty.

---

## Български

Неофициален TWRP recovery за **Motorola Moto G8 Power** (`sofiar`, XT2041-3). Билдва се изцяло в GitHub Actions, без нужда от локален Linux.

Основната му функция е **работещо FBE декриптиране с ПИН на стоков Android 11**. Досегашните неофициални TWRP билдове за този телефон не се справяха с това.

### Статус

| Функция | Статус |
|---|---|
| Стартиране (`fastboot boot` и инсталиран в `recovery_a`) | ✅ |
| Дисплей, яркост | ✅ |
| Тъчскрийн (FocalTech FT8756) | ✅ |
| ADB (root) | ✅ |
| MTP (вътрешна памет + microSD) | ✅ |
| Батерия / индикатор за зареждане | ✅ |
| FBE декриптиране с ПИН (стоков Android 11) | ✅ |
| Format Data / Wipe Data | ⚠️ поправено, още не е тествано на телефон |
| Вибрация | ❌ не се поддържа |
| Декриптиране на custom ROM (LineageOS и др.) | ❌ не се поддържа |

### Тестван на

| | |
|---|---|
| Модел | XT2041-3, RETEU |
| Фърмуер | Android 11, `RPES31.Q4U-47-35-12` |
| Bootloader | `MBM-3.0-sofiar_reteu-0f8934adaf-220131` (отключен) |
| Ядро в TWRP | prebuilt, взето от стоковия `boot_a` на този билд |

Други версии на фърмуера **не са тествани**. Виж [Ограничения](#ограничения).

### ⚠️ Отказ от отговорност

Използваш на собствен риск. Отключването на bootloader-а и инсталирането на custom recovery може да анулира гаранцията и при грешка да брикне телефона. **Първо направи бекъп на всичко** (виж [Бекъпи](#бекъпи)). Никога не записвай bootloader, модем или EFS дялове.

### Изисквания

- Отключен bootloader
- Стоков Android 11, билд `RPES31.Q4U-47-35-12`
- `adb` и `fastboot` (Android SDK Platform Tools)

### Използване

**1. Тест без инсталиране (препоръчително първо).** TWRP се пуска от RAM и нищо не се записва на телефона:

```bash
adb reboot bootloader
fastboot boot recovery.img
```

Провери, че тъчът работи. После въведи ПИН-а и виж дали вътрешната памет показва нормални имена на папки (DCIM, Download, …).

**2. Бекъп на стоковото recovery**, докато TWRP е пуснат:

```bash
adb pull /dev/block/bootdevice/by-name/recovery_a recovery_a_stock.img
adb pull /dev/block/bootdevice/by-name/recovery_b recovery_b_stock.img
```

**3. Инсталиране.** Записва се само в recovery дяла на активния слот, а `recovery_b` остава стоков като резерва:

```bash
adb reboot bootloader
fastboot getvar current-slot     # трябва да е: a
fastboot flash recovery_a recovery.img
```

После избери **Recovery mode** в менюто на bootloader-а с бутоните за звук.

**Връщане на стоковото recovery:**

```bash
fastboot flash recovery_a recovery_a_stock.img
```

### Бекъпи

Преди да пипаш каквото и да е, запази поне:

- `recovery_a/b`, `boot_a`, `vbmeta_a/b`, `dtbo_a/b`
- **EFS / IMEI**: `modemst1`, `modemst2`, `fsg_a`, `fsg_b`, `fsc`, `persist`, както и дяловете на Motorola `prodpersist`, `utags`, `utagsBackup`, `hw`, `cid`, `sp`. Те са **уникални за твоя телефон** и не могат да се свалят отново от никъде.
- Пълния стоков фърмуер (zip) за твоя билд.

`tools/save_backups.ps1` (Windows) прави всичко това само с четене от TWRP и проверява всеки образ със SHA-256. Пази EFS образите лично: съдържат IMEI-то ти.

### Билдване

Всичко става в GitHub Actions:

1. Направи fork на репото.
2. **Actions → Build TWRP - sofiar → Run workflow**.
3. Изтегли `recovery.img` от артефактите на рън-а.

Пълен билд отнема около 2–3 часа, най-вече заради `repo sync`. Workflow-ът сваля TWRP minimal manifest (`twrp-12.1`) и общото SM6125 дърво, копира този device tree, прилага няколко поправки и пуска `mka recoveryimage`.

### Технически бележки

Как са решени трудните проблеми, за всеки, който пренася това на подобно устройство.

<details>
<summary><b>Prebuilt ядро от boot дяла на самия телефон</b></summary>

Драйверът на тъча е vendor модул на ядрото, подписан с **ключ, уникален за всеки билд** на стоковото ядро. Ядрата от `recovery.img` на фърмуера или от друг билд го отхвърлят с `Required key not available`. Решението е ядрото и dtb да се извадят от собствения `boot_a` на телефона (`tools/extract_prebuilts.py`). `recovery_dtbo` е от стоковото recovery.
</details>

<details>
<summary><b>Тъчскрийн</b></summary>

FocalTech FT8756 (`fts_ts`) на Tianma панел, с драйвер `focaltech_0flash_mmi.ko`. Контролерът „0flash“ иска фърмуера си (`focaltech-ft8756-0e-01-sofiar.bin`) при всяко пускане. `postrecoveryboot.sh` монтира vendor **само за четене**, копира фърмуера в ramdisk-а, зарежда модулите по реда в `modules.dep` и демонтира vendor.
</details>

<details>
<summary><b>Загуба на FBE ключовете при демонтиране на /data (<code>/datakeep</code>)</b></summary>

Ядрото поддържа `FS_IOC_ADD_ENCRYPTION_KEY`, затова FBE ключовете се пазят в **superblock-а на файловата система**. При стартиране TWRP демонтира и отново монтира `/data`. Това унищожава superblock-а, а заедно с него и ключовете. След това екранът за ПИН вижда само криптирани имена на файлове и не намира `spblob`.

Решението: `datakeep.sh` (init го пуска синхронно в `on fs`) монтира userdata втори път в `/datakeep`. Така superblock-ът остава жив и ключовете оцеляват, докато TWRP демонтира и монтира. Малък пач в `partition.cpp` освобождава `/datakeep` точно преди Format/Wipe Data, за да не дава `mkfs` грешка „busy“.
</details>

<details>
<summary><b>Стар keystore на Android 11 → keystore2 (<code>key not found</code>)</b></summary>

TWRP 12.1 търси ключа на synthetic password-а само в **keystore2** (Android 12+). Android 11 го пази като стар keystore файл (`/data/misc/keystore/user_0/1000_USRPKEY_synthetic_password_<handle>`), затова декриптирането спираше с `key not found`.

`tools/patch_vold_a11_keystore.py` пачва `system/vold/Decrypt.cpp`. При `KEY_NOT_FOUND` копира стария файл в keystore папката на TWRP в RAM (uid 1000 → 0, защото TWRP върви като root) и вика `IKeystoreMaintenance::migrateKeyNamespace`. Това е същата миграция, която прави Android 12 при ъпдейт от 11. После опитва отново. Нищо в `/data` не се променя. Пачът също така спира TWRP да презаписва базата на keystore2 с празен файл, когато `persistent.sqlite` липсва (Android 11).
</details>

<details>
<summary><b>Други поправки</b></summary>

- **Разделен fstab:** `twrp.fstab` (формат на TWRP) за TWRP и `recovery.fstab` в AOSP `fs_mgr` формат, защото vold/fscrypt го четат.
- **TrustZone веригата тръгва рано:** `crypto.ready=1` се задава при `hwservicemanager.ready`, за да са готови qseecomd, keymaster и gatekeeper, преди TWRP да пробва DE ключовете.
- **Ред на библиотеките за qseecomd:** `/system/lib64` е преди `/vendor/lib` в `LD_LIBRARY_PATH`. Иначе 64-битовият linker взима 32-битовия `libandroidicu.so`.
- **USB:** един собствен `init.recovery.usb.rc` (configfs, `mtp.gs0` + `ffs.adb`) избягва безкраен цикъл на UDC rebind.
- **Батерия:** захранването е `qcom_battery`, а не `battery`. `Android.mk` на TWRP проверява `TW_USE_LEGACY_BATTERY_SERVICES` *преди* `TW_CUSTOM_BATTERY_PATH` да го включи, затова двете трябва да се зададат изрично.
</details>

### Ограничения

- **Обвързан е със стоковото ядро на един билд на фърмуера.** След OTA ъпдейт трябва ядрото да се извади отново от новия `boot` и да се направи нов билд, иначе тъчът спира да работи. OTA ще презапише и recovery дяла.
- Декриптирането работи само за **стоков Android 11**. Custom ROM-овете ползват различно криптиране и ядро: там тъчът и декриптирането най-вероятно няма да работят, затова използвай recovery-то, което препоръчва ROM-ът.
- Няма вибрация.

### Структура на репото

```
.github/workflows/build-twrp-sofiar.yml   CI билд
local_manifest.xml                        общо SM6125 дърво
device_motorola_sofiar/
  BoardConfig.mk, device.mk, twrp_sofiar.mk, ...
  recovery.fstab                          AOSP fs_mgr формат (за vold)
  prebuilt/                               ядро, dtb, recovery_dtbo
  recovery/root/
    init.recovery.usb.rc                  USB, ранен старт на крипто, /datakeep
    system/bin/postrecoveryboot.sh        фърмуер и модули за тъча
    system/bin/datakeep.sh                пази FBE ключовете
    system/etc/twrp.fstab                 списък с дялове за TWRP
    vendor/lib64/                         библиотеки за декриптиране
tools/                                    скриптове за извличане, пачове и бекъп
```

### Благодарности

- [TeamWin](https://github.com/TeamWin) за TWRP
- [minimal-manifest-twrp](https://github.com/minimal-manifest-twrp)
- [trinket-common / teamwin_device_motorola_sm6125-common](https://github.com/trinket-common) за общото SM6125 дърво
- Motorola за стоковите библиотеки

### Лиценз

TWRP е под лиценз GPLv3. Скриптовете и конфигурацията в това репо се предоставят „както са“, без гаранции.
