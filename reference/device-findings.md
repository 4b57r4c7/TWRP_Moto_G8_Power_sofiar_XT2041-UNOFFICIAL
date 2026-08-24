# Device findings - Motorola Moto G8 Power (sofiar) XT2041-3

Всички данни тук са извлечени директно от реалния stock firmware на
устройството (build **RETEU 11 RPES31.Q4U-47-35-12**), не са копирани
от други devices/forks. Инструментите, използвани за извличането, са
в `tools/`.

## Partition table (от gpt.bin, извлечен от stock firmware zip)

- GPT-то е обвито в проприетарен Motorola "SIN" wrapper (~13.5KB
  header преди истинската `EFI PART` сигнатура) - `tools/parse_gpt.py`
  го намира автоматично чрез сканиране на целия файл.
- A/B slot схема потвърдена: `boot_a/b`, `recovery_a/b`, `dtbo_a/b`,
  `vbmeta_a/b` - всички съществуват като отделни двойки дялове.
- `super` дял (8288 MB) - dynamic partitions (system/vendor/product
  вероятно логически вътре в super, не отделни физически дялове).
- `recovery_a`/`recovery_b` = 64MB всеки.
- `boot_a`/`boot_b` = 64MB всеки.
- Няма `cache` дял, няма `vendor_boot` (non-GKI устройство).
- Пълен изход: виж по-долу в тази бележка или пусни `tools/parse_gpt.py`
  наново върху `gpt.bin` от firmware zip-а.

## Boot image header (от recovery.img, чрез tools/unpack_bootimg.py)

```
header_version : 2
page_size      : 4096
kernel_size    : 14641057   kernel_addr : 0x8000
ramdisk_size   : 11909546   ramdisk_addr: 0x1000000
second_size    : 0          second_addr : 0x0
tags_addr      : 0x100
recovery_dtbo_size: 1559604
dtb_size       : 326894
```

Извод: base=0x0, kernel_offset=0x8000, ramdisk_offset=0x1000000,
tags_offset=0x100 - това са СТАНДАРТНИТЕ AOSP default стойности,
никакви екзотични отклонения за `BoardConfig.mk`.

cmdline включва `androidboot.hab.product=sofiar` - потвърждава, че
файлът реално е за това устройство (не грешен модел/архив).

## Stock recovery.fstab (реалният, от вътре в recovery ramdisk-а)

Извлечен чрез `tools/unpack_bootimg.py` + `tools/extract_ramdisk.py`
от `system/etc/recovery.fstab` вътре в стоковия recovery ramdisk.
Пренесен/адаптиран в TWRP формат в `device_motorola_sofiar/recovery.fstab`.

Ключови точки:
- `/data` използва `fileencryption=ice:aes-256-cts` - хардуерно FBE
  криптиране през Qualcomm Inline Crypto Engine. **Известен риск** -
  TWRP декриптиране за тази ICE конфигурация не е гарантирано да
  проработи от пръв опит (виж 2020-годишния XDA WIP thread за sofiar,
  който имаше точно този проблем).
- `/system` се mount-ва през обикновен `by-name` path БЕЗ изричен
  `logical` flag в stock fstab-а, въпреки че `super` дял съществува.
  За TWRP версията добавихме `logical`-съвместим подход в
  `device_motorola_sofiar/recovery.fstab`, но **трябва да се
  потвърди при реален boot тест** дали е нужен изричен `logical` flag.
- `/boot`, `/recovery`, `/misc` са тип `emmc` (raw/flashable, не
  filesystem mount) - очаквано за тези служебни дялове.

## Firmware source

- Build: `XT2041-3_SOFIAR_RETEU_11_RPES31.Q4U-47-35-12_subsidy-DEFAULT_regulatory-DEFAULT_CFC.xml.zip`
- Mirror: lolinet (`mirrors.lolinet.com/firmware/lenomola/2020/sofiar/official/RETEU/`)
- Точно съвпада с Android версията, реално инсталирана на устройството.

## Известни рискове за следващите стъпки

1. ICE/FBE декриптиране на `/data` - вероятно ще изисква допълнителни
   TWRP crypto патчове, ако не работи "из кутията".
2. `logical` flag за system/vendor/product в TWRP fstab-а - трябва
   тест, не е потвърдено от stock данните директно.
3. Kernel source (`codyf86/android_kernel_motorola_trinket`) е
   community-derived, не официален от Motorola - възможни леки
   разлики от точната конфигурация на този build.
