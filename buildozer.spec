[app]
title = Supremacy
package.name = supremacy
package.domain = org.supremacy

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 0.1

# Убрали комментарии из списка зависимостей
#requirements = python3==3.9.16, kivy==2.2.1, sqlite3, cython
requirements = python3==3.9.16, kivy==2.3.0, sqlite3, cython==0.29.36, openssl, certifi

# Убедитесь, что файлы icon.png и presplash.png существуют в папке assets
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png
presplash_color = #1C1C1C

orientation = portrait

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE

# УБРАЛИ КОММЕНТАРИЙ ИЗ СТРОКИ С android.archs
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True
android.accept_sdk_license = True

# Исправлен путь к БД (если она в папке assets)
source.include_patterns = 
    assets/*
    assets/game_data.db

[buildozer]
log_level = 2
warn_on_root = 1

android.ndk_version = 25.1.8937393

