#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"

const int scanTime = 4; //In seconds
String fileName = "scan"; //follow {format}
unsigned long curTime;
File dataFile;
int fileNum = 1;
boolean alternator = false;
BLEScan* pBLEScan;

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      ;
    }
};

void setup() {
  SD.begin();

  pinMode(4, OUTPUT);
  pinMode(2, OUTPUT);
  pinMode(32, OUTPUT);
  pinMode(0, INPUT);

  digitalWrite(4, LOW);
  digitalWrite(2, LOW);
  digitalWrite(32, LOW);

  // testing if the card is working
  if (!SD.begin()) {
    digitalWrite(2, HIGH);
    digitalWrite(4, LOW);
    while (1);
  } else {
    digitalWrite(4, HIGH);
  }

  while (SD.exists("/" + fileName + " " + fileNum + ".txt")) {
    fileNum++;
  }
  fileName = "/" + fileName + " " + fileNum + ".txt";

  dataFile = SD.open(fileName, FILE_APPEND);
  dataFile.println("Timestamp, Address");
  dataFile.close();

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true); //active scan uses more power, but get results faster
  pBLEScan->setInterval(10);
  pBLEScan->setWindow(1000);
}

void loop() {
  while(digitalRead(0) == HIGH) {
    digitalWrite(4, HIGH);
  }
  digitalWrite(4, LOW);
  
  curTime = millis();

  BLEScanResults foundDevices = pBLEScan->start(scanTime);

  dataFile = SD.open(fileName, FILE_APPEND);

  for (int i = 0; i < foundDevices.getCount(); i++) {
    dataFile.print(curTime);
    dataFile.print(", ");
    dataFile.println(foundDevices.getDevice(i).getAddress().toString().c_str());

    dataFile.flush();

    digitalWrite(32, HIGH);
  }

  delay(500);
  dataFile.close();

  if (alternator) {
    digitalWrite(4, HIGH);
    alternator = false;
  } else {
    digitalWrite(4, LOW);
    alternator = true;
  }

  pBLEScan->clearResults();   // delete results fromBLEScan buffer to release memory
  delay(500);
}
