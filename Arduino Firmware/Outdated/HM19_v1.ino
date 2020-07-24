#include <SoftwareSerial.h>

SoftwareSerial BTSerial(2, 3); //RX, TX
char c = ' ';
boolean NL = true;

void setup()
{
  Serial.begin(9600);
  Serial.print("Sketch:   ");   Serial.println(__FILE__);
  Serial.print("Uploaded: ");   Serial.println(__DATE__);
  Serial.println(" ");

  BTSerial.begin(9600);
}

void loop() {
  if (BTSerial.available()) {
    c = BTSerial.read();

    // Echo the user input to the main window. The ">" character indicates the user entered text.
    if (NL) {
      Serial.print(">");
      NL = false;
    }
    Serial.write(c);
    if (c == 10) {
      NL = true;
    }
  }

  if (Serial.available()) {
    c = Serial.read();
    BTSerial.write(c);
  }
}
