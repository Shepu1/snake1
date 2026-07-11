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
# NOTE: kivy remove kora hoyeche - eta apnar game e use e hoy na (pure pygame game)
# pygame = SDL2 bootstrap diye direct build hoy, onek fast ar stable
# pyjnius + android = Android-specific screen size / storage path er jonno lage (utils.py te use hoy)
requirements = python3,pygame,pyjnius==1.6.1,android

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

#
# Android specific
#

# (int) Target Android API (Play Store er niyom onujayi 34 nirapod)
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 21

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enable AndroidX support.
android.enable_androidx = True

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK

# SDK license auto accept
android.accept_sdk_license = True

# (str) Bootstrap to use for android
# sdl2 bootstrap pygame ar kivy dutar jonno e kaj kore - eta thik ache
bootstrap = sdl2

# (str) Presplash of the application (loading screen)
presplash.filename = %(source.dir)s/snake.png

# (str) Icon of the application (home screen icon)
icon.filename = %(source.dir)s/snake.png

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
