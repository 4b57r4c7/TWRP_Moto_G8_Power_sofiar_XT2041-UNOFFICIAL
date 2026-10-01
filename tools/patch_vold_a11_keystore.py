#!/usr/bin/env python3
"""
sofiar: TWRP 12.1 + Android 11 данни.

TWRP 12.1 търси ключа на synthetic password-а в keystore2 (Android 12+),
а Android 11 го пази като стар (legacy) keystore файл:
  /data/misc/keystore/user_0/1000_USRSKEY_synthetic_password_<handle>
Резултат: "key not found" -> ПИН-ът "не е верен".

Пач на system/vold/Decrypt.cpp:
 1) copySqliteDb(): ако няма /data/misc/keystore/persistent.sqlite (Android 11),
    НЕ презаписва базата на keystore2 в /tmp с празен файл.
 2) При KEY_NOT_FOUND: копира legacy файловете на ключа в /tmp/misc/keystore/user_0
    (с uid 0 вместо 1000, защото TWRP върви като root), вика
    IKeystoreMaintenance::migrateKeyNamespace (същото, което прави Android 12 при
    ъпдейт от 11) и опитва пак. Всичко е в RAM (/tmp); /data само се чете.

Употреба: python3 patch_vold_a11_keystore.py ~/twrp/system/vold/Decrypt.cpp
"""
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()


def replace_once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit(f"ГРЕШКА: '{what}' намерено {n} пъти (очаквано 1)")
    return text.replace(old, new)


if "sofiarMigrateLegacySpKey" in src:
    print("Вече е пачнато")
    sys.exit(0)

# --- include ---
src = replace_once(
    src,
    "#include <aidl/android/system/keystore2/ResponseCode.h>\n",
    "#include <aidl/android/system/keystore2/ResponseCode.h>\n"
    "#include <aidl/android/security/maintenance/IKeystoreMaintenance.h>\n",
    "include ResponseCode.h",
)

# --- 1) copySqliteDb: без празен файл, когато няма източник ---
src = replace_once(
    src,
    '\t\tstd::string src = "/data/misc/keystore/persistent.sqlite";\n',
    '\t\tstd::string src = "/data/misc/keystore/persistent.sqlite";\n'
    "\t\tstruct stat sofiar_st;\n"
    "\t\tif (stat(src.c_str(), &sofiar_st) != 0) {\n"
    '\t\t\tprintf("sofiar: no %s (Android 11), keeping keystore2 db\\n", src.c_str());\n'
    "\t\t\treturn;\n"
    "\t\t}\n",
    "copySqliteDb src",
)

# --- 2a) помощна функция (в namespace keystore, преди unwrapSyntheticPasswordBlob) ---
helper = r'''
	// sofiar: Android 11 legacy keystore -> keystore2 (виж patch_vold_a11_keystore.py)
	bool sofiarMigrateLegacySpKey(const std::string& handle, const std::string& dest_alias) {
		const std::string src_dir = "/data/misc/keystore/user_0/";
		const std::string dst_dir = "/tmp/misc/keystore/user_0/";
		const std::string name = "synthetic_password_" + handle;
		mkdir("/tmp/misc/keystore", 0700);
		mkdir("/tmp/misc/keystore/user_0", 0700);
		bool copied = false;
		DIR* d = opendir(src_dir.c_str());
		if (!d) {
			printf("sofiar: cannot open %s\n", src_dir.c_str());
			return false;
		}
		struct dirent* de;
		while ((de = readdir(d)) != nullptr) {
			std::string f = de->d_name;
			if (f.find(name) == std::string::npos) continue;
			std::string out;
			if (f.rfind("1000_", 0) == 0) out = "0_" + f.substr(5);
			else if (f.rfind(".1000_chr_", 0) == 0) out = ".0_chr_" + f.substr(10);
			else continue;
			std::string data;
			if (!android::base::ReadFileToString(src_dir + f, &data)) {
				printf("sofiar: read failed %s\n", f.c_str());
				continue;
			}
			if (!android::base::WriteStringToFile(data, dst_dir + out)) {
				printf("sofiar: write failed %s\n", out.c_str());
				continue;
			}
			printf("sofiar: copied %s -> %s (%zu bytes)\n", f.c_str(), out.c_str(), data.size());
			copied = true;
		}
		closedir(d);
		if (!copied) {
			printf("sofiar: no legacy key files for %s\n", name.c_str());
			return false;
		}
		::ndk::SpAIBinder mb(AServiceManager_checkService("android.security.maintenance"));
		auto maint = ::aidl::android::security::maintenance::IKeystoreMaintenance::fromBinder(mb);
		if (!maint) {
			printf("sofiar: no android.security.maintenance service\n");
			return false;
		}
		ks2::KeyDescriptor legacy_key = {
			.domain = ks2::Domain::APP,
			.nspace = -1,
			.alias = name,
			.blob = {},
		};
		auto mrc = maint->migrateKeyNamespace(legacy_key, keyDescriptor(dest_alias));
		if (!mrc.isOk()) {
			printf("sofiar: migrateKeyNamespace failed: %s\n", mrc.getDescription().c_str());
			return false;
		}
		printf("sofiar: legacy key migrated to %s\n", dest_alias.c_str());
		return true;
	}

'''
anchor = "\t/* C++ replacement for function of the same name\n\t* https://android.googlesource.com/platform/frameworks/base/+/android-8.0.0_r23/services/core/java/com/android/server/locksettings/SyntheticPasswordManager.java#867"
src = replace_once(src, anchor, helper + anchor, "unwrapSyntheticPasswordBlob comment")

# --- 2b) при KEY_NOT_FOUND -> миграция и нов опит ---
src = replace_once(
    src,
    "\t\t\tauto rc = keystore->getKeyEntry(keyDescriptor(keystore_alias), &keyEntryResponse);\n"
    "\t\t\tif (!rc.isOk()) {\n",
    "\t\t\tauto rc = keystore->getKeyEntry(keyDescriptor(keystore_alias), &keyEntryResponse);\n"
    "\t\t\tif (!rc.isOk() && ks2::ResponseCode(unwrapError(rc)) == ks2::ResponseCode::KEY_NOT_FOUND\n"
    "\t\t\t\t\t&& sofiarMigrateLegacySpKey(handle, keystore_alias)) {\n"
    "\t\t\t\trc = keystore->getKeyEntry(keyDescriptor(keystore_alias), &keyEntryResponse);\n"
    "\t\t\t}\n"
    "\t\t\tif (!rc.isOk()) {\n",
    "getKeyEntry",
)

open(path, "w", encoding="utf-8").write(src)
print("Decrypt.cpp пачнат (Android 11 legacy keystore)")
