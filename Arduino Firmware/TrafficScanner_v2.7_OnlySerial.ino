#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "SPI.h"

int scanTime = 4; //In seconds
unsigned long curTime;
boolean alternator = false;
BLEScan* pBLEScan;

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      ;
    }
};

void setup() {
  Serial.begin(115200);

  pinMode(4, OUTPUT);
  pinMode(2, OUTPUT);
  pinMode(32, OUTPUT);

  digitalWrite(4, LOW);
  digitalWrite(2, LOW);
  digitalWrite(32, LOW);

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true); //active scan uses more power, but get results faster
  pBLEScan->setInterval(10);
  pBLEScan->setWindow(1000);
}

void loop() {
  Serial.println("1");
  curTime = millis();
  Serial.println(curTime);

  BLEScanResults foundDevices = pBLEScan->start(scanTime);
  Serial.println("2");

  digitalWrite(32, LOW);
  
  for (int i = 0; i < foundDevices.getCount(); i++) {
    Serial.println("2.1");
    Serial.print(curTime);
    Serial.print(", ");
    Serial.println(foundDevices.getDevice(i).getAddress().toString().c_str());

    digitalWrite(32, HIGH);
  }
  Serial.println("3");

  delay(500);
  
  if (alternator) {
    Serial.println("3.1");
    digitalWrite(4, HIGH);
    alternator = false;
  } else {
    Serial.println("3.2");
    digitalWrite(4, LOW);
    alternator = true;
  }
  Serial.println("4");

  pBLEScan->clearResults();   // delete results fromBLEScan buffer to release memory
  Serial.println("5");
  delay(500);
}
