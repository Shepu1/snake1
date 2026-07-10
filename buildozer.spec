[app]

# (str) Title of your application
title = Shepus Snake

# (str) Package name
package.name = shepussnake

# (str) Package domain (needed for android/ios packaging)
package.domain = com.shepu.snake

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,wav,mp3,ttf,ico,txt

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# pygame + Android: Python 3.10 পিন করতে হয় (3.11+ এ build fail হয়)
requirements = python3==3.10.12, hostpython3==3.10.12, kivy==2.3.0, pyjnius==1.5.0, pygame, android

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

#
# Android specific
#

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (list) Android application meta-data to set (key=value format)
# android.meta_data =

# (list) Android library project to add (will be added on build-time)
# android.library_repositories =

# (str) Android logcat filters to use
# android.logcat_filters = *:S python:D

# (bool) Android copy library instead of making a libpymodules.so
# android.copy_libs = 1

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package.
android.enable_androidx = True

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK

# SDK লাইসেন্স অটো একসেপ্ট
android.accept_sdk_license = True

# (str) Bootstrap to use for android
# pygame bootstrap launches main.py with SDL2
bootstrap = sdl2

# (str) Presplash of the application (লোডিং স্ক্রিন)
presplash.filename = %(source.dir)s/snake.png

# (str) Icon of the application (হোম স্ক্রিন আইকন)
icon.filename = %(source.dir)s/snake.png

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
