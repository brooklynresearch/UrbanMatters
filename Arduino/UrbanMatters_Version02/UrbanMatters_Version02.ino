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

// color palette list
//uint32_t Sage = convertColor(222, 151, 61);
//uint32_t Sage = convertColor(103, 69, 32);
uint32_t Sage = convertColor(110, 66, 31);

//uint32_t Mica = convertColor(190,90,128);
//uint32_t Mica = convertColor(152, 57, 89);
uint32_t Mica = convertColor(152, 57, 57);
//uint32_t Mica = convertColor(102, 39, 60);

//uint32_t Buff = convertColor(191, 104, 50);
//uint32_t Buff = convertColor(98,60,39);
//uint32_t Buff = convertColor(255, 255, 255);
uint32_t Buff = convertColor(112, 68, 41);

uint32_t Elbo = convertColor(246,221,58);

//uint32_t Cozi = convertColor(211,222,102);
//uint32_t Cozi = convertColor(98, 134, 70);
uint32_t Cozi = convertColor(129, 160, 80);

uint32_t Palette[5] = {Sage, Mica, Buff, Elbo, Cozi};

// The following are used for converting 32bit colors to RGB values
// Use them only immediately after calling getRGB(uint32_t color)
uint8_t convertR = 0;
uint8_t convertG = 0;
uint8_t convertB = 0;


int volume = MINVOLUME;
float rate = 0.05;
float curve = 0.0;
int brightness = MINBRIGHT;
int colors[NUMPATTERNS] = {0, 0, 1, 0, 0};

long colorTimer = 0;
int threshold = 5000;

long currentMillis;

uint8_t currentColorIndex = 0;
uint32_t currentColor = Palette[0];
uint32_t displayColor = 0;

int transistionThreshold = 2000;


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

  
  //Serial.print("Color: ");Serial.println(color, HEX);
  
  //Set strip brightness based on proximity
  strip.setBrightness(brightness - 20);
  
  /*
  for (int pixel = 0; pixel < NUMPIXELS; pixel++) {
    strip.setPixelColor(pixel, color);
  }
  strip.show();
  delay(20);
  */
  int timer = millis() - currentMillis;

	if(timer < transistionThreshold){
		// get the current cycle color;
		displayColor = getCurrentColor(timer, currentColorIndex); 
	
	    	colorSegmentDefault(0, NUMPIXELS, displayColor);
  	} else {
  		// Serial.println("We've timed out");
                Serial.print("CurrentColor: ");Serial.println(Palette[currentColorIndex % 5]);
  		currentColorIndex++;
  		currentMillis = millis();
  	}
  strip.show();

}

uint32_t convertColor(int rCol, int gCol, int bCol){
  uint32_t currentColor = rCol;
  currentColor <<= 8;
  currentColor += bCol;
  currentColor <<= 8;
  currentColor += gCol;
  return currentColor;
}


void colorSegmentDefault(int startPix, int endPix, uint32_t segmentColor){
  for(int j = startPix; j < endPix; j++){
       strip.setPixelColor(j, segmentColor); 
  }
}


// converts 32bit colorspace back to r,g,b
void getRGB(uint32_t color){
  
  convertR = color >> 16;
  convertG = color >> 8;
  convertB = color;
}

uint32_t getCurrentColor(int timer, uint8_t colorIndex){

  uint32_t startColor = Palette[colorIndex % 5];
  uint32_t endColor = Palette[(colorIndex + 1) % 5];
  uint32_t newColor = 0;

  uint8_t Rstart,Gstart,Bstart;  
  uint8_t Rend,Gend,Bend;
  uint8_t Rnew,Gnew,Bnew;

  float colorPercentage = (float)timer / (float)transistionThreshold;

  // get RGB values of start color
  getRGB(startColor);
  Rstart = convertR;
  Gstart = convertG;
  Bstart = convertB;

  // get RGB values of end target color
  getRGB(endColor);
  Rend = convertR;
  Gend = convertG;
  Bend = convertB;
  


  Rnew = Rstart + (Rend - Rstart) * colorPercentage;
  Gnew = Gstart + (Gend - Gstart) * colorPercentage;
  Bnew = Bstart + (Bend - Bstart) * colorPercentage;

  return strip.Color(Rnew, Gnew, Bnew);

}
