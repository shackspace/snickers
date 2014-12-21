/*
  Example for receiving
  
  http://code.google.com/p/rc-switch/
  
  If you want to visualize a telegram copy the raw data and 
  paste it into http://test.sui.li/oszi/
*/

#include <RCSwitch.h>

#include <FastLED.h>
#define DATA_PIN 2
// RCSwitch pin is at 3
#define NUM_LEDS 4
CRGB leds[NUM_LEDS];

RCSwitch mySwitch = RCSwitch();

void turn_color(int r,int g,int b){
  for(int i = 0; i < NUM_LEDS; i++) {
    // Set the i'th led to red 
    leds[i].r = r;
    leds[i].g = g;
    leds[i].b = b;
    // Show the leds
    // now that we've shown the leds, reset the i'th led to black
    // Wait a little bit before we loop around and do it again
  }
  FastLED.show();

}

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, DATA_PIN, RGB>(leds, NUM_LEDS); 
  mySwitch.enableReceive(0);  // Receiver on inerrupt 0 => that is pin #3 for 
  turn_color(0,255,0);
  Serial.println("dickbutt");
}

void loop() {
  while (Serial.available() > 0) {
    int r = Serial.parseInt();
    int g = Serial.parseInt();
    int b = Serial.parseInt();
    if (Serial.read() == '\n') {
        /*Serial.print("(r,g,b) -> (");
        Serial.print(r);
        Serial.print(",");
        Serial.print(g);
        Serial.print(",");
       
        Serial.print(b);
        Serial.println(")"); */


      turn_color(r,g,b);
      }
  }

  if (mySwitch.available()) {
    output(mySwitch.getReceivedValue(), mySwitch.getReceivedBitlength(), mySwitch.getReceivedDelay(), mySwitch.getReceivedRawdata(),mySwitch.getReceivedProtocol());
    mySwitch.resetAvailable();    
  }
}
