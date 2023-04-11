#include "Adafruit_FONA.h"
#include <SPI.h>
#include <elapsedMillis.h>
#include <Wire.h>

/*
Decription: This is a modified version of the code that does the loopback
and gets rid of the calling feature. It auto picks up and loops audio.
Screen is removed and replaced with LEDs for simplicity.
*/

const uint8_t FONA_RST = 9;
const uint8_t FONA_RI = 4;
const uint8_t FONA_KEY = 3;

//BOX 1
const uint8_t LED_1 = 5;
const uint8_t LED_2 = 6;
const uint8_t LED_3 = 9;

//Box 2
//const uint8_t LED_1 = 9; //blue = 9
//const uint8_t LED_2 = 6; //yellow = 6
//const uint8_t LED_3 = 5; //red = 5

//int SD_ERROR = 0;
volatile bool UPDATE_STATS = true;

//Raw Stat Info
int8_t STAT_RSSI = 0; //in dBm
uint8_t STAT_NETWORK = 0;
uint8_t STAT_GPS = 0;
uint8_t STAT_CALL = 0;

//Stat info in STR format
String STAT_RSSI_STR = "";
String STAT_NETWORK_STR = "";
String STAT_GPS_STR = "";
String STAT_CALL_STR = "";

//Lat, Lon, Speed_kph, heading, alt
float GPS_STAT_DATA[5];

HardwareSerial *fonaSerial = &Serial1;
Adafruit_FONA_3G fona = Adafruit_FONA_3G(FONA_RST);

// GUItool: begin automatically generated code
//AudioInputI2S            i2s1;           //xy=170,165
//AudioOutputI2S           i2s2;           //xy=385,164
//AudioConnection          patchCord1(i2s1, 0, i2s2, 0);
//AudioConnection          patchCord3(i2s1, 1, i2s2, 1);
//AudioControlSGTL5000     sgtl5000_1;     //xy=273,228
// GUItool: end automatically generated code

//const int myInput = AUDIO_INPUT_LINEIN;
//elapsedMillis fps;
elapsedMillis STAT_U;
uint8_t STAT_U_C = 0;
uint8_t cnt=0;

void setAudio(){

  // Disables automatic echo suppression which prevents loopback
  fona.disableEchoSuppression();

  // Set maximum audio out volume
  fona.setVolume(8);

}

void setup() {

  // Set baud rate
  Serial.begin(115200);

  // Set I/O pin types
  pinMode(FONA_RI, INPUT_PULLUP);
  pinMode(FONA_RST, OUTPUT);
  pinMode(FONA_KEY, OUTPUT);
  pinMode(LED_1, OUTPUT);
  pinMode(LED_2, OUTPUT);
  pinMode(LED_3, OUTPUT);

  // Initialize I/O pin values
  digitalWrite(FONA_KEY, LOW);
  digitalWrite(LED_1, LOW);
  digitalWrite(LED_2, LOW);
  digitalWrite(LED_3, LOW);

  // begin serial communication with FONA
  fonaSerial->begin(4800);
  fona.begin(*fonaSerial);

  // Audio settings
  setAudio();

  // Small delay before we enter loop
  delay(500);

}

void loop() {

	// Pick up an incoming call
  if(fona.getCallStatus() == FONA_CALL_RINGING){
		fona.pickUp();
		digitalWrite(LED_1, HIGH);
		Serial.println("Answered Call!");
		delay(100);
	}

  // Status Update
	if(STAT_U >= 500){
		STAT_U = 0;
		STAT_U_C++;
		uint8_t c_stat = fona.getCallStatus();

		if(STAT_U_C >= 10){ //Try Full Status Update
			if(c_stat != 4 || c_stat != 3){ //If we're not on a call, update status
				updateNetworkInfo();
				STAT_U_C = 0; // Reset Full Update Counter
			}
		}else{ //Just Call Status Update
			if(digitalRead(LED_1) == HIGH && c_stat != 4){ //If we're not on the call but the call light is on
				digitalWrite(LED_1, LOW);
			}
		}
	}

	delay(10);
}


void updateNetworkInfo(){
	//Check Network Connection Stat
	STAT_NETWORK = fona.getNetworkStatus();

	//Get Call Stat
	getCallStat();

	//Check RSSI
	getRSSI();

	//Check GPS Info
	if(fona.GPSstatus() == 2 || fona.GPSstatus() == 3){
		STAT_GPS = 1;
		fona.getGPS(&GPS_STAT_DATA[0],&GPS_STAT_DATA[1],&GPS_STAT_DATA[2],&GPS_STAT_DATA[3],&GPS_STAT_DATA[4]);
	}else{
		STAT_GPS = 0;
	}

	//Output results
	//outputStatsSerial();
	outputStatsDisplay();

}

void getRSSI(){
  uint8_t n = fona.getRSSI();
  int8_t r;

  if (n == 0) r = -115;
  if (n == 1) r = -111;
  if (n == 31) r = -52;
  if ((n >= 2) && (n <= 30)) {
    r = map(n, 2, 30, -110, -54);
  }
  STAT_RSSI = r;
  Serial.print(r);Serial.println(" dBm");
}

void getCallStat(){
	uint8_t stat = fona.getCallStatus();
	STAT_CALL = stat;
}

void outputStatsDisplay(){
	if(STAT_CALL == 0){
		STAT_CALL_STR = "Ready";
		digitalWrite(LED_2, LOW);
	}else if(STAT_CALL == 1){
		STAT_CALL_STR = "Failure";
		digitalWrite(LED_1, LOW);
	}else if(STAT_CALL == 2){
		STAT_CALL_STR = "Unknown";
		digitalWrite(LED_1, LOW);
	}else if(STAT_CALL == 3){
		STAT_CALL_STR = "Ringing";
		digitalWrite(LED_1, HIGH);
	}else if(STAT_CALL == 4){
		STAT_CALL_STR = "Call in Progress";
		digitalWrite(LED_1, HIGH);
	}else{
		STAT_CALL_STR = "Call Stat Error";
	}


	if(STAT_NETWORK == 0){
		STAT_NETWORK_STR = "Not registered, MT is not currently searching";
		digitalWrite(LED_2, LOW);
	}else if(STAT_NETWORK == 1){
		STAT_NETWORK_STR = "Registered, home network";
		digitalWrite(LED_2, HIGH);
	}else if(STAT_NETWORK == 2){
		STAT_NETWORK_STR = "Not registered, but MT is currently searching";
		digitalWrite(LED_2, LOW);
	}else if(STAT_NETWORK == 3){
		STAT_NETWORK_STR = "Registration denied";
		digitalWrite(LED_2, LOW);
	}else if(STAT_NETWORK == 4){
		STAT_NETWORK_STR = "Unknown";
	}else{
		STAT_NETWORK_STR = "Registered, roaming";
		digitalWrite(LED_2, HIGH);
	}


	//RSSI: -54 = Best, -115 = Worst
	if(STAT_RSSI >= -85){
		digitalWrite(LED_3, LOW);
	}else{
		digitalWrite(LED_3, HIGH);
	}
}
