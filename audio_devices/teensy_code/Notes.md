# Leopard Seal Notes

## Overview:
So the way this works is that, like with the manual experiments, the computer plays the audio into the fona. However, we now use the Teensy doing analog reads to look for when the audio is played and when a response is received. The Teensy does not have differential analog reads, but from my experiments I don't think we'll need that for what we need to do. The following are the main things you'll need to do to test the system. 


### Hardware Code measurement_auto_external_v0.2.ino
This is the code to upload to the teensy hardware. It should reflect exactly what was in the google sheet in regards to what messaging and what it does. It also has an extra command it can take for reading raw analog data for testing, which can be used as follows:
- Command: header+"rawsampleread;0" - This will start the raw analog read and will print it to the serial monitor without the communication header so it shouldn't mess up the python code
	- Response: header+"rawstat;1"
- Command: Header+"stopraw;0" - This will stop the raw analog sensor read mode.
	- Response: header+"rawstat;0";

- Note: If a command is sent other than [Header+"stopraw;0"] while in raw analog read mode, it will respond with [header+"rawstaterror;1"]


### Additional Hardware Connections
To set this up you need to make two hardware connections to the Teensy so it can read the analog data:

A9 -> The Tip/Ring1 line of the audio jack in the bread board I gave you that is connected to the computer.
A2 -> The Tip/Ring1 line of the other audio jack in the bread board I gave you that is connected to nothing. 


### Python Code

The python code is relatively simple. It just plays the .wav files using a cross platform library. You will need to pip install 'simpleaudio'. You'll need to incorporate this into your python code to play after starting the sample taking process on the Teensy via the serial command. The Teensy waits for 8 seconds after the process has started to see the audio from the computer. If it doesn't it'll time out. 

- Note: There are 6 different audio files in the same folder as the python code. You need to put those in the same folder as where your code is. They are tones of 3 different frequencies, for both 1 and 3 seconds in length. Use whatever one you like in the code that seems to work the best. 

- Note: Currently you need to make sure your volume on your machine is all the way up when you play the audio, however, I am looking into a way to handle that via code.
