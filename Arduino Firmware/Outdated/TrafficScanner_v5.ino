#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "WiFi.h"
#include "ESPAsyncWebServer.h"

String fileName = "/scan.txt"; //follow {format}
unsigned long curTime;
File dataFile;
char c;
int lastLog = 0;

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

void setup() {
  Serial.begin(115200);
  Serial1.begin(115200, SERIAL_8N1, 16, 17);

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
    Serial.println("initialization failed.");
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

  Serial1.println("AT+DISI?");
  Serial.println(">>AT+DISI?");
}

void loop() {
  curTime = millis();
  dataFile = SD.open(fileName, FILE_APPEND);
  
  if (Serial1.available()) {
    c = Serial1.read();
    delay(10);
    Serial.write(c);
    dataFile.write(c);
    if (c == '+') {
      Serial.println();
      dataFile.println();
    }
  }

  if (curTime >= lastLog + 9000) {
    delay(1000);
    Serial1.println("AT+DISI?");
    Serial.println(">>AT+DISI?");
    lastLog = curTime;
  }
}
