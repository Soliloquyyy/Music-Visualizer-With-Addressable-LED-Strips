
#include <FastLED.h>


#define LED_PIN 6
#define LED_COUNT 30

// Declare our NeoPixel strip object:
CRGB leds[LED_COUNT];



//global int array for incoming bytes
String rgbdata;
const int dHSL[] =  {224, 255, 50};
uint8_t hue = dHSL[0];
uint8_t brightness = 1;
unsigned int count = 0;
unsigned int secCount = 0;
void setup() {
  Serial.begin(9600);
  FastLED.addLeds<NEOPIXEL,LED_PIN>(leds,LED_COUNT);
  FastLED.showColor(CHSV(hue, dHSL[1], dHSL[2]));

}

void loop() {
  EVERY_N_SECONDS(1){
    hue++;
  }
  if(Serial.available()){
    rgbdata = Serial.readStringUntil('\n');
    static uint8_t light = brightness;
    EVERY_N_MILLISECONDS( 16 ) {
      light = constrain(rgbdata.toInt() + 80, 50, 255);  
    }
    if(light == brightness){  
      brightness = light;     
      FastLED.showColor(CHSV(hue, dHSL[1], brightness));
    }
    else if(light > brightness){
      while(light > brightness) {
        brightness += 5;
        FastLED.showColor(CHSV(hue, dHSL[1], brightness));
      }    
    }
    else {
      while(light < brightness) {
        brightness -=5;
        FastLED.showColor(CHSV(hue, dHSL[1], brightness));
      }    
    }
    brightness = light; 
  }
   else{
      EVERY_N_SECONDS(5){
        while(brightness > 50){
          FastLED.showColor(CHSV(hue, dHSL[1], brightness));
          --brightness;
        }
      }
   } 
}
