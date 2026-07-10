# Google Colab APK Build Script
# এই ফাইলের কোডগুলো Colab নোটবুকের সেলে কপি-পেস্ট করে রান করুন।
# বিস্তারিত বাংলা নির্দেশনা: docs/APK_নির্মাণ_গাইড.txt

COLAB_CELL_1_INSTALL = r'''
# সেল ১ — প্রয়োজনীয় টুল ইনস্টল
!apt-get update -qq
!apt-get install -y -qq python3-pip build-essential git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev > /dev/null
!pip install -q buildozer cython==0.29.36
import os
print("ইনস্টল সম্পন্ন")
'''

COLAB_CELL_2_UPLOAD = r'''
# সেল ২ — গেম ফোল্ডার আপলোড (ZIP)
from google.colab import files
import zipfile, os, shutil

print("আপনার গেমের ZIP ফাইল সিলেক্ট করুন (ShepusSnake_Android.zip)")
uploaded = files.upload()

for name in uploaded:
    if name.endswith('.zip'):
        if os.path.exists('ShepusSnake'):
            shutil.rmtree('ShepusSnake')
        with zipfile.ZipFile(name, 'r') as z:
            z.extractall('.')
        print('আনজিপ সম্পন্ন:', name)

# প্রজেক্ট ফোল্ডারে যান
if os.path.exists('ShepusSnake'):
    os.chdir('ShepusSnake')
elif os.path.exists('New folder'):
    os.chdir('New folder')
else:
    print('সতর্কতা: গেম ফোল্ডার খুঁজে পাওয়া যায়নি — ম্যানুয়ালি cd করুন')

!ls -la
'''

COLAB_CELL_3_BUILD = r'''
# সেল ৩ — APK বিল্ড (৩০–৬০ মিনিট লাগতে পারে)
import os
os.environ['USE_SDK_WRAPPER'] = '1'
os.environ['BUILDOZER_WARN_ON_ROOT'] = '0'

!buildozer -v android debug
print('বিল্ড শেষ')
!ls -lh bin/
'''

COLAB_CELL_4_DOWNLOAD = r'''
# সেল ৪ — APK ডাউনলোড
from google.colab import files
import glob

apks = glob.glob('bin/*.apk')
if apks:
    print('APK পাওয়া গেছে:', apks[0])
    files.download(apks[0])
else:
    print('APK খুঁজে পাওয়া যায়নি — বিল্ড লগ চেক করুন')
'''

if __name__ == '__main__':
    print("এটি সরাসরি রান করার স্ক্রিপ্ট নয়।")
    print("Colab-এ docs/APK_নির্মাণ_গাইড.txt অনুসরণ করুন।")
