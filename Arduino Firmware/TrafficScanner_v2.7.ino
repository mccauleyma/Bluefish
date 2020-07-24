#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"

int scanTime = 4; //In seconds + 1 second from delays
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
  Serial.begin(115200);
  SD.begin();

  pinMode(4, OUTPUT);
  pinMode(2, OUTPUT);
  pinMode(32, OUTPUT);

  digitalWrite(4, LOW);
  digitalWrite(2, LOW);
  digitalWrite(32, LOW);

  // testing if the card is working
  if (!SD.begin()) {
    digitalWrite(2, HIGH);
    digitalWrite(4, LOW);
    while (1);
  } else {
    Serial.println("SD Failed to initialize");
    digitalWrite(4, HIGH);
  }

  while (SD.exists("/" + fileName + " " + fileNum + ".csv")) {
    fileNum++;
  }
  fileName = "/" + fileName + " " + fileNum + ".csv";

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
  Serial.println("1");
  curTime = millis();
  Serial.println(curTime);

  BLEScanResults foundDevices = pBLEScan->start(scanTime);
  Serial.println("2");

  dataFile = SD.open(fileName, FILE_APPEND);

  digitalWrite(32, LOW);
  
  for (int i = 0; i < foundDevices.getCount(); i++) {
    Serial.println("2.1");
    dataFile.print(curTime);
    Serial.print(curTime);
    dataFile.print(", ");
    Serial.print(", ");
    dataFile.println(foundDevices.getDevice(i).getAddress().toString().c_str());
    Serial.println(foundDevices.getDevice(i).getAddress().toString().c_str());

    dataFile.flush();

    digitalWrite(32, HIGH);
  }
  Serial.println("3");

  delay(500);

  dataFile.close();

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
