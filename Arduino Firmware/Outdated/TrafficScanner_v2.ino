#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "WiFi.h"
#include "ESPAsyncWebServer.h"

int scanTime = 5; //In seconds
String fileName = "/scan.txt"; //follow {format}
unsigned long curTime;
File dataFile;
BLEScan* pBLEScan;

// Replace with your network credentials
const char* ssid = "BLUEFISH";
const char* password = "bluefish123";

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

String masterLog = "";

String masterLogFunc() {
  return masterLog;
}

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
  <style>
    html {
     font-family: Arial;
     display: inline-block;
     margin: 0px auto;
     text-align: center;
    }
    h2 { font-size: 3.0rem; }
    p { font-size: 1.0rem; }
    .labels{
      font-size: 1.5rem;
      vertical-align:middle;
      padding-bottom: 15px;
    }
  </style>
</head>
<body>
  <h2>Bluefish Server</h2>
  <p>
    <span class="labels">Log</span> 
    <span id="log" style="overflow:auto;">%LOG%</span>
  </p>
</body>
<script>
setInterval(function ( ) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById("log").innerHTML = this.responseText;
    }
  };
  xhttp.open("GET", "/log", true);
  xhttp.send();
}, 10000 ) ;
</script>
</html>)rawliteral";

// Replaces placeholder with values
String processor(const String& var){
  //Serial.println(var);
  if(var == "LOG"){
    return masterLog;
  }
  return String();
}

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      Serial.printf("Advertised Device: %s \n", advertisedDevice.toString().c_str());
    }
};

void setup() {
  Serial.begin(115200);
  SD.begin();

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);

  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // Route for root / web page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send_P(200, "text/html", index_html, processor);
  });
  server.on("/log", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send_P(200, "text/plain", masterLogFunc().c_str());
  });

  // Start server
  server.begin();

  Serial.print("\nInitializing SD card...");
  masterLog = masterLog + "Initializing SD Card...";

  // testing if the card is working
  if (!SD.begin()) {
    Serial.println("initialization failed. Things to check:");
    Serial.println("* is a card inserted?");
    masterLog = masterLog + "Initializing failed.";
    while (1);
  } else {
    Serial.println("Wiring is correct and a card is present.");
    masterLog = masterLog + "Wiring is correct and a card is present.............LOG BUFFER...........................................................................................................................................................................................................................................................";
  }

  uint64_t cardSize = SD.cardSize() / (1024 * 1024);
  Serial.printf("SD Card Size: %lluMB\n", cardSize);

  dataFile = SD.open(fileName, FILE_WRITE);
  dataFile.println("Timestamp, Address");
  dataFile.close();

  Serial.println("Scanning...");

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true); //active scan uses more power, but get results faster
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);  // less or equal setInterval value
}

void loop() {
  curTime = millis();
  BLEScanResults foundDevices = pBLEScan->start(scanTime, false);

  dataFile = SD.open(fileName, FILE_APPEND);
  for (int i = 0; i < foundDevices.getCount(); i++) {
    Serial.print(curTime);
    dataFile.print(curTime);
    Serial.print(", ");
    dataFile.print(", ");
    Serial.println(foundDevices.getDevice(i).getAddress().toString().c_str());
    dataFile.println(foundDevices.getDevice(i).getAddress().toString().c_str());
  }
  
  masterLog = masterLog + "Logged " + curTime + "ms. ";
  masterLog.remove(0, 11 + String(curTime).length());
  dataFile.close();

  pBLEScan->clearResults();   // delete results fromBLEScan buffer to release memory
}
