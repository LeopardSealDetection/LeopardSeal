## Hardware Requirements ##
#### Audio Loopback Board ####
[PJRC Teensy 4.1 Development Board](https://www.adafruit.com/product/4622)\
[Adafruit FONA 3G Cellular Breakout - American version](https://www.adafruit.com/product/2687)\
[High Quality Audio Loopback Plug](https://www.passmark.com/products/audio_loopback/index.php)\
Valid SIM Card\
Soldering iron, breadboard/perfboard, wires\
#### Audio Measurement Board #####
[Arduino Uno]()\
[3G/GPRS/GSM Shield for Arduino with GPS - American version SIM5320A](https://www.tinyosshop.com/3g-gprs-gsm-shield-for-arduino-sim5320a?filter_name=3G&filter_description=true&filter_sub_category=true)\
Valid SIM Card\
Soldering iron, wires

## Software Requirements ##
[Arduino IDE](https://www.arduino.cc/en/software) \
[Adafruit FONA Library](https://learn.adafruit.com/adafruit-fona-mini-gsm-gprs-cellular-phone-module/arduino-test)\
[Python3](https://www.python.org/downloads/)\
[SimpleAudio Library for Python](https://simpleaudio.readthedocs.io/en/latest/installation.html)

## Audio Devices Code ##
This directory contains the Arduino Uno and [Teensy 4.1](https://www.adafruit.com/product/4622) code used in the measurement and loopback devices, respectively. You can use the [Arduino IDE](https://www.arduino.cc/en/software) to load these .ino files into those boards. This will require that you load the [Adafruit FONA Library](https://learn.adafruit.com/adafruit-fona-mini-gsm-gprs-cellular-phone-module/arduino-test) into the IDE.
Once code is loaded onto both boards, you can connect the audio measurement board to your computer via USB and connect an aux cord from your computer's audio output port to the mic input of the cellular Arduino shield.

## SIM5320 Loopback Audio Settings via AT Commands ##
This is a reference for the settings that must be made to the SIM5320 board contained within the audio boards for the loopback and measurement devices. Our scripts should take care of these settings.\
[SIM5320 AT Command Set](https://cdn-shop.adafruit.com/datasheets/SIMCOM_SIM5320_ATC_EN_V2.02.pdf)

~~~
+CSDVC: 1 (1,3,4) // Audio Device
+CLVL: 2 (0 to 8) // Audio Level
+CMICAMP1: 1 (0,1) // Microphone Amplifier
+CNSM: 1 (0,1) // Noise suppression
+CEXTERNTONE: 0 (0,1) // Disable MIC
+CECM: 0 (0 to 7) // Enable/Disable Echo Canceller
+CTXGAIN: 10000 (0 to 65535)
+CRXGAIN: 3000 (0 to 65535)
+CTXVOL: 10000 (0 to 65535)
+CRXVOL: 0 (-100 to 100)
+CVLVL: -200,1000,3000,5000,3000,4000,5000,5000
~~~
