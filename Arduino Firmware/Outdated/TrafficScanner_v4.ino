#include "SPI.h"
#include <SoftwareSerial.h>
#include <Wire.h>

SoftwareSerial BTSerial(2, 3);
char c;
int lastLog = 0;

void setup() {
  Serial.begin(115200);
  BTSerial.begin(115200);
  Wire.begin();

  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  BTSerial.println("AT+DISI?");
  Serial.println(">>AT+DISI?");
  Wire.beginTransmission(8);
}

void loop() {
  if (BTSerial.available()) {
    c = BTSerial.read();
    Serial.write(c);
    Wire.write(c);
  }

  if (millis() >= lastLog + 9000) {
    Wire.endTransmission();
    delay(1000);
    BTSerial.println("AT+DISI?");
    Serial.println(">>AT+DISI?");
    lastLog = millis();
    Wire.beginTransmission(8);
  }
}
