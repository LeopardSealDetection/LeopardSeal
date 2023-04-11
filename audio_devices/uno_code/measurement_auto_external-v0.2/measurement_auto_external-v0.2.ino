#include <Adafruit_FONA.h>
#include <SoftwareSerial.h>
#include <elapsedMillis.h>

// FONA pins
#define FONA_TX 2
#define FONA_RX 3
#define FONA_RST 9
//#define FONA_RI 3
#define FONA_POWER 8
#define FONA_POWER_ON_TIME  180  /* 180ms*/
#define FONA_POWER_OFF_TIME 1000 /* 1000ms*/

// FONA variables
Adafruit_FONA_3G fona = Adafruit_FONA_3G(FONA_RST);

// ADC pins
#define readPin A0
#define readPin2 A1

// ADC variables
#define ADC_max_value 1023
float THRESH_OUT = 0.1;
float THRESH_OUT_MIN = 0.01;
float THRESH_IN = 0.03;
float THRESH_IN_MIN = 0.01;

// Serial communication
SoftwareSerial fonaSS = SoftwareSerial(FONA_TX,FONA_RX);
SoftwareSerial *fonaSerial = &fonaSS;
char buffer[256];
String command_buffer[16];
String HEADDER = "#$ls;";

// Timing variables
elapsedMillis audio_time;

void setup() {

  // Set FONA pins
  pinMode(FONA_POWER, OUTPUT);
  digitalWrite(FONA_POWER, HIGH);
  delay(FONA_POWER_ON_TIME);
  digitalWrite(FONA_POWER, LOW);
  delay(3000);

  // Set ADC pins as inputs
  pinMode(readPin, INPUT);
  pinMode(readPin2, INPUT);

  // Begin serial communication
  while (!Serial);
  Serial.begin(115200);
  Serial.println(F("FONA basic test"));
  Serial.println(F("Initializing....(May take 3 seconds)"));

  fonaSerial->begin(4800);
  if (! fona.begin(*fonaSerial)) {
    Serial.println(F("Couldn't find FONA"));
    while (1);
  }

  // Set audio to external headset
  fona.setAudio(FONA_HEADSETAUDIO);
  
//  delay(500);
//  Serial.println(F("FONA basic test"));
//  fonaSerial->begin(4800);
//  fona.begin(*fonaSerial);

  // Begin communication with host
  lookForComms();
}

void lookForComms(){
	while(1){
		Serial.println(F("leopard_seal_init"));
		int i = serialCheck(buffer);

		if(i == 1){
			int j = initCmdParser(buffer);
			if(j == 1){
				break;
			}
		}
		delay(50);
	}
}


void loop(){
	int i = serialCheck(buffer);

	if(i == 1){
		int c = commandParser(buffer, command_buffer);
    handleCommands(command_buffer);
	}
	delay(50);
}

void handleCommands(String* s){
  String response;

  if(s[0].indexOf("calln") != -1){
    char numberbuffer[16];

    s[1].toCharArray(numberbuffer, s[1].length());
//    Serial.println(numberbuffer);
    uint8_t net_stat = fona.getNetworkStatus();

    if(net_stat == 0 || net_stat == 2 || net_stat == 3){
      response = HEADDER + "call_ack;-2";
    }else{
      if(placeCall(numberbuffer)){
        response = HEADDER + "call_ack;1";
      }else{
        response = HEADDER + "call_ack;-1";
      }
    }

  }else if(s[0].indexOf("records") != -1){
    if(fona.getCallStatus() != 4){
      response = HEADDER + "records;-2";
    }else{
      double samp = getSample();
      response = HEADDER + "records;"+String(samp,4);
    }
  }else if(s[0].indexOf("endc") != -1){
    if(endCall()){
      response = HEADDER + "end_ack;1";
    }else{
      response = HEADDER + "end_ack;0";
    }
  }else if(s[0].indexOf("nstat") != -1){
    uint8_t r = fona.getNetworkStatus();
  	response = HEADDER + "netstat;"+ String(r);
  }else if(s[0].indexOf("cstat") != -1){
    uint8_t r = fona.getCallStatus();
  	response = HEADDER + "callstat;"+ String(r);
  }else if(s[0].indexOf("rawsampleread") != -1){
    Serial.println(HEADDER+"rawstat;1");
    rawSampleRead();
    response = HEADDER+"rawstat;0";
  }else if(s[0].indexOf("reset") != -1){
    Serial.println(HEADDER+"rst_ack;1");
    delay(1000);
    lookForComms();
    response = "";
  }else{
    Serial.println("Error! Incorrect Command!");
  }

  Serial.println(response);
}


/*//////////////////////////////////////////////////////////
CALL TOOLS
*///////////////////////////////////////////////////////////
bool placeCall(char* number){
  //dial out and wait for response, if not on call return -1
  //Serial.println("Calling Loopback!");

  fona.callPhone(number);

  elapsedMillis ring_time = 0;

  while(ring_time < 8000){
    if(fona.getCallStatus() == 4){
      //Serial.println("Call in progress!");
      return true;
    }
  }
  fona.hangUp();
  //Serial.println("Call Not Completed!");
  return false;
}

bool endCall(){
  bool ret = true;

  fona.hangUp();

  if(fona.getCallStatus() != 0 || fona.getCallStatus() != 1){
    ret = false;
  }else{
    ret = true;
  }
  return ret;
}

void getSteadyState() {

  int value;
  int value2;
  int NUM_SAMPLES = 10;
  double total1 = 0;
  double total2 = 0;

  // Take average of 10 ADC readings for both channels
  for (int i = 0; i < NUM_SAMPLES; i++) {
    value = analogRead(readPin); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
    double t_val = value*3.3/ADC_max_value;
    total1 += t_val;
  
    value2 = analogRead(readPin2); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
    double t_val2 = value2*3.3/ADC_max_value;
    total2 += t_val2;
  }
  // Calculate thresholds based on steady state voltage readings
  if (total1 < 0.05) {
    THRESH_OUT = (0.05 / NUM_SAMPLES) * 4;
    THRESH_OUT_MIN = 0;
  }
  else {
    THRESH_OUT = (total1 / NUM_SAMPLES) * 4;
    THRESH_OUT_MIN = (total1 / NUM_SAMPLES) * 0.1;
    THRESH_OUT_MIN = 0;
  }
  if (total2 < 0.05) {
    THRESH_IN = (0.05 / NUM_SAMPLES) * 4 + 0.3;
    THRESH_IN_MIN = 0.3;
  }
  else {
    THRESH_IN = (total2 / NUM_SAMPLES) + 0.06;
    THRESH_IN_MIN = (total2 / NUM_SAMPLES) - 0.06;
//    THRESH_IN_MIN = 0.3;
  }
  
}

double getSample(){
  // Get average voltage values
  getSteadyState();
  Serial.println("Value 1: " + String(THRESH_OUT, 4) + ", Value 2: " + String(THRESH_IN, 4));
  double rtt_val = 0;
  int value;
  int value2;
  double t_val;
  double t_val2;
  elapsedMillis timeout=0;

  //look for audio on output line for specific amount of time 
  while(timeout< 10000){
    value = analogRead(readPin); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
    t_val = value*3.3/ADC_max_value;
    
    if(t_val >= THRESH_OUT || t_val < THRESH_OUT_MIN){
      Serial.println("Value 1: " + String(t_val, 4));
      timeout=0;
      //when detected, start timer
      audio_time=0;
      break;
    }
  }

  // Delay 300 ms to wait for audio recording to end
  delay(350);

  //look for audio on input line
  while(timeout < 3000){
    value2 = analogRead(readPin2); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
    t_val2 = value2*3.3/ADC_max_value;

    //if detected, Stop timer and output rtt
    if(t_val2 >= THRESH_IN || t_val2 < THRESH_IN_MIN){
      Serial.println("Value 2: " + String(t_val2, 4));
      rtt_val = audio_time;
      break;
    }
  }

  return rtt_val;
}

/*//////////////////////////////////////////////////////////
serial TOOLS
*///////////////////////////////////////////////////////////
int serialCheck(char* b){

	int r = 0;
  	if(Serial.available() > 0){
      Serial.println("Got command!");
    	Serial.readBytes(b, 256);
    	r = 1;
  	}
  	return r;
}

void printCharArray(char* b, int len){
  	Serial.print("Received Data: ");
  	
  	for(int i=0; i<len; i++){
    	Serial.print(b[i]);
  	}

  	Serial.print('\n');
}

void printStringArray(String* s, int len){

	Serial.print("Received Data: ");

	for(int i=0; i< len; i++){
		Serial.print(s[i]);
		Serial.print(':');
	}
	Serial.print('\n');

}

int initCmdParser(char* b){
	String message = String(b);
	int r = 0;

	if(message.indexOf("#$ls;ls_confirm_ready\n") != -1){
		r = 1;
	}
	return r;
}


int commandParser(char* b, String* param){
  	//example format
  	//headder;function_id;parameter1;
  	String input = String(b);
  	String sub_s;
  	int i = 0;
  	int c = 0;

  	int break_index = 0;

//    Serial.println("Input: " + input);

  	if(input.indexOf(HEADDER) != -1){
      break_index = input.indexOf(';',i);
      if(break_index == -1) {
        param[c] = input;
        return c;
      }
      i = break_index + 1;
      break_index = input.indexOf(';',i);
      if (break_index != -1) {
        param[c] = input.substring(0, break_index);
        c++;
      }
      i = break_index + 1;
      input = input.substring(i);
  		while(break_index != -1){
  			break_index = input.indexOf(';', i);
        i = break_index + 1;
  			if(break_index != -1){
          param[c] = input.substring(0,break_index);
          c++;
  				input = input.substring(i);
//          Serial.println("Substring: " + param[c]);
  			}
  		}
     param[c] = input;
  	}
  return c;
}


void rawSampleRead(){
  bool read_raw = true;

  while(read_raw){

    int value;
    int value2;

    value = analogRead(readPin); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
    double t_val = value*3.3/ADC_max_value;

    value2 = analogRead(readPin2); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
    double t_val2 = value2*3.3/ADC_max_value;

    if((t_val >= THRESH_OUT || t_val <= THRESH_OUT_MIN) || (t_val2 >= THRESH_IN || t_val2 <= THRESH_IN_MIN)){

      //t_val = t_val-t_val2;
      Serial.println("Value 1: " + String(t_val, 4) + ", Value 2: " + String(t_val2, 4));

    }

    int i = serialCheck(buffer);

    if(i == 1){
      int c = commandParser(buffer, command_buffer);
      if(command_buffer[0].indexOf("stopraw") != -1){
        read_raw = false;
      }else{
        Serial.println(HEADDER+"rawstaterror;1");
      }
    }

    delay(150);
  }
}
