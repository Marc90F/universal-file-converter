[app]

# (str) Title of your application
title = Universal File Converter

# (str) Package name
package.name = universalfileconverter

# (str) Package domain (needed for android/ios packaging)
package.domain = org.marc90f

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,xml,txt,md

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,core/*,engines/*,gui/*,mobile/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,pyc,pyo,zip

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv, .venv, .git, .github, colab, docs

# (list) List of exclusions using pattern matching
source.exclude_patterns = colab_app.py

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0,pillow,openpyxl,plyer,certifi

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen to not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE, INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) The Android architectures to build for (ARM 64-bit e 32-bit per tutti gli smartphone Android)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Allow backup of app data
android.allow_backup = True

# (bool) Automatically accept SDK license
android.accept_sdk_license = True

# (str) python-for-android branch or tag to use (Python 3.11 LTS compatibile con Kivy)
p4a.branch = v2024.01.21

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with compiler output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
