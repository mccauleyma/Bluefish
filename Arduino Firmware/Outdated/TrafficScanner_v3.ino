#include "SD.h"
#include "SPI.h"
#include <SoftwareSerial.h>

#define BUFFSIZE 512

int scanTime = 3; //In seconds
String fileName = "/scan.txt"; //follow {format}
unsigned long curTime;
File dataFile;
SoftwareSerial BTserial(8, 9); // RX | TX
int i = 0;
char buffer[BUFFSIZE];
char c;
int bufferidx;

void saveLine(String str) {
  dataFile = SD.open(fileName, FILE_WRITE);
  Serial.println(str);
  dataFile.println(str);
  dataFile.close();
}

void setup() {
  Serial.begin(9600);
  SD.begin(4);
  BTserial.begin(9600);

  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  Serial.print("\nInitializing SD card...");

  // testing if the card is working
  if (!SD.begin(4)) {
    Serial.println("initialization failed.");
    while (1);
  } else {
    Serial.println("Wiring is correct and a card is present.");
  }

  dataFile = SD.open(fileName, O_CREAT | O_WRITE | O_APPEND);
  dataFile.println("Timestamp, Address");
  dataFile.println("5, ");
  dataFile.flush();

  BTserial.write("AT+DISI?");
}

void loop() {
  curTime = millis();

  if (BTserial.available()) {
    c = BTserial.read();
    Serial.write(c);
    if (c == "OK+DISCE") {
      dataFile.println("");
      dataFile.print(curTime + ", ");
      BTserial.write("AT+DISI?");
    }
    dataFile.write(c);
    dataFile.flush();
  }
}
