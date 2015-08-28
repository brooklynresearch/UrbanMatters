// include SPI, MP3 and SD libraries
#include <SPI.h>
#include <Adafruit_VS1053.h>
#include <SD.h>

#include <Adafruit_DotStar.h>

#define NUMPIXELS 60 // Number of LEDs in strip

// Here's how to control the LEDs from any two pins:
#define DATAPIN    6
#define CLOCKPIN   5
Adafruit_DotStar strip = Adafruit_DotStar(NUMPIXELS, DATAPIN, CLOCKPIN);

// define the pins used
//#define CLK 13       // SPI Clock, shared with SD card
//#define MISO 12      // Input data, from VS1053/SD card
//#define MOSI 11      // Output data, to VS1053/SD card
// Connect CLK, MISO and MOSI to hardware SPI pins.
// See http://arduino.cc/en/Reference/SPI "Connections"

// These can be any pins:
#define RESET 9      // VS1053 reset pin (output)
#define CS 10        // VS1053 chip select pin (output)
#define DCS 8        // VS1053 Data/command select pin (output)
#define CARDCS 4     // Card chip select pin
// DREQ should be an Int pin, see http://arduino.cc/en/Reference/attachInterrupt
#define DREQ 3       // VS1053 Data request, ideally an Interrupt pin

#define MAXVOLUME 10
#define MINVOLUME 40
#define MAXBRIGHT 254
#define MINBRIGHT 40

#define NUMPATTERNS 5

int volume = MINVOLUME;
float rate = 0.05;
float curve = 0.0;
int brightness = MINBRIGHT;
int colors[NUMPATTERNS] = {0, 0, 1, 0, 0};

long colorTimer = 0;
int threshold = 5000;

Adafruit_VS1053_FilePlayer musicPlayer = Adafruit_VS1053_FilePlayer(RESET, CS, DCS, DREQ, CARDCS);

void setup() {
  Serial.begin(9600);
  Serial.println("Adafruit VS1053 Simple Test");

  musicPlayer.begin(); // initialise the music player
  SD.begin(CARDCS);    // initialise the SD card

  // Set volume for left, right channels. lower numbers == louder volume!
  musicPlayer.setVolume(MINVOLUME, MINVOLUME);

  //musicPlayer.useInterrupt(VS1053_FILEPLAYER_TIMER0_INT); // timer int
  musicPlayer.useInterrupt(VS1053_FILEPLAYER_PIN_INT);  // DREQ int

  strip.begin(); // Initialize pins for output
  strip.show();  // Turn all LEDs off ASAP

  colorTimer = millis();
}

void loop() {
  // Loop Ocean Sounds
  if (! musicPlayer.playingMusic) {
    musicPlayer.startPlayingFile("track002.mp3");
  }
  
  int proximityReadings = analogRead(0);
  //Serial.print("Proximity: ");Serial.println(proximityReadings);
  volume = map(proximityReadings, 50, 500, MINVOLUME, MAXVOLUME);
  brightness = map(proximityReadings, 50, 500, MINBRIGHT, MAXBRIGHT);
  //Serial.print("Volume: ");Serial.println(volume);
  //Serial.print("Brightness: ");Serial.println(brightness);
  
  //Constrain Volume
  if (volume > MINVOLUME) {
    volume = MINVOLUME;
  } else if ( volume < MAXVOLUME) {
    volume = MAXVOLUME;
  }
  
  //Constrain Brightness
  if(brightness > MAXBRIGHT){
    brightness = MAXBRIGHT;
  } else if(brightness < MINBRIGHT){
    brightness = MINBRIGHT;
  }
  
  //Set Volume based on proximity distance
  musicPlayer.setVolume(volume, volume);

  //Determine which color pattern we are in
  pickAColorPattern();
  //Get the rgb values of that color pattern
  curve += rate;
  uint32_t color = getPatternColor(curve);
  
  //Serial.print("Color: ");Serial.println(color, HEX);
  
  //Set strip brightness based on proximity
  strip.setBrightness(brightness - 20);

  for (int pixel = 0; pixel < NUMPIXELS; pixel++) {
    strip.setPixelColor(pixel, color);
  }
  strip.show();
  delay(20);

}

uint32_t convertColor(int rCol, int gCol, int bCol){
  uint32_t currentColor = rCol;
  currentColor <<= 8;
  currentColor += bCol;
  currentColor <<= 8;
  currentColor += gCol;
  return currentColor;
}

void pickAColorPattern(){
  if (millis() - colorTimer > threshold) {
    int randomGrad = (int)random(5);
    Serial.print(randomGrad);
    for (int i = 0; i < 5; i++) {
      colors[i] = 0;
    }
    colors[randomGrad] = 1;
    colorTimer = millis();
  }
}

uint32_t getPatternColor(float gradCurve){
  int red, green, blue;
  if (colors[0]) {
    red = ((sin(gradCurve) * 128) + 127);
    green = 128;
    blue = 255;
  } else if (colors[1]) {
    green = ((sin(gradCurve) * 128) + 127);
    red = 255;
    blue = 255;
  } else if (colors[2]) {
    blue = ((sin(gradCurve) * 128) + 127);
    red = 255;
    green = 255;
  } else if (colors[3]) {
    red = ((sin(gradCurve) * 128) + 127);
    blue = ((sin(gradCurve) * 128) + 127);
    green = 255;
  } else if (colors[4]) {
    blue = ((sin(gradCurve) * 128) + 127);
    green = ((sin(gradCurve) * 128) + 127);
    red = 255;
  }
  return convertColor(red, green, blue);
}
