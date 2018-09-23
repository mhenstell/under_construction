/*
 * EEPROM Write
 *
 * Stores values read from analog input 0 into the EEPROM.
 * These values will stay in the EEPROM when the board is
 * turned off and may be retrieved later by another sketch.
 */

#include <EEPROM.h>

char id[5] = "UC02";

void setup() {

  Serial.begin(115200);
  while (!Serial) {
    delay(1);
  }
  
  for (int i = 0; i < 4; i++) {
    EEPROM.write(i, id[i]);
  }
  Serial.println("Wrote ID");
}

void loop() {
  
}
