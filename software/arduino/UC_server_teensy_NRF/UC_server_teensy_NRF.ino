#include <SPI.h>
#include <NRFLite.h>
#include "Arduhdlc.h"

#define PROX_DATA 0x01
#define LIGHT_LEVEL 0x02
#define RING_BUFFER_DEPTH 20
#define BROADCAST 0xFF
#define MAX_HDLC_FRAME_LENGTH 32
#define HEARTBEAT_PERIOD 1000
#define HEARTBEAT 0x99
#define BASESTATION 0xAF

//const static uint8_t RADIO_ID = 255;
//const static uint8_t PIN_RADIO_CE = 10;
//const static uint8_t PIN_RADIO_CSN = 0;
//const static uint8_t PIN_RADIO_IRQ = 1;

#define PIN_RADIO_IRQ 3
#define PIN_RADIO_CSN 10
#define PIN_RADIO_CE 9


//volatile bool readyToSend = false;
uint8_t incomingByte = 0;
uint8_t incomingPacketArray[4] = {0};
uint8_t incomingPacketIndex = 0;

long lastHeartbeat = 0;

NRFLite _radio;

void send_character(uint8_t data);
void hdlc_frame_handler(const uint8_t *data, uint16_t len);
Arduhdlc hdlc(&send_character, &hdlc_frame_handler, MAX_HDLC_FRAME_LENGTH);

void send_character(uint8_t data) {
  Serial.print((char)data);
}

void hdlc_frame_handler(const uint8_t *data, uint16_t len) {
  _radio.send(BROADCAST, &data, len);
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(1);
  }
  Serial.println("Starting server...");

  pinMode(PIN_RADIO_IRQ, INPUT_PULLUP);

  if (!_radio.init(BROADCAST, PIN_RADIO_CE, PIN_RADIO_CSN))
  {
    Serial.println("Cannot communicate with radio");
    while (1); // Wait here forever.
  }

  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_IRQ), radioInterrupt, FALLING);

  Serial.println("Ready...");
}

void loop()
{

  if (millis() - lastHeartbeat > HEARTBEAT_PERIOD)
  {
    char buf[] = {BROADCAST, HEARTBEAT, BASESTATION};
    hdlc.send(buf, 3);
    lastHeartbeat = millis();
  }

}

void serialEvent() {
  uint8_t buf[MAX_HDLC_FRAME_LENGTH];
  uint8_t idx = 0;
  while (Serial.available()) {
    buf[idx++] = Serial.read();
  }

  _radio.startSend(BROADCAST, buf, idx, NRFLite::NO_ACK);
}

void radioInterrupt() {
  // Required to call whatHappened for some reason
  // or you won't get anything in hasDataISR
  uint8_t txOk, txFail, rxReady;
  _radio.whatHappened(txOk, txFail, rxReady);


  uint8_t len = _radio.hasDataISR();
  if (len > 0) {
    uint8_t buf[MAX_HDLC_FRAME_LENGTH];
    _radio.readData(&buf);

    for (int x = 0; x < len; x++) {
      Serial.print(char(buf[x]));
    }

    //      if (buf[x] < 0x10) Serial.print("0");
    //      Serial.print(buf[x], HEX);
    //      Serial.print(" ");
    //
    //    }
    //    Serial.println();
  }





  //  if (txOk)
  //  {
  //    Serial.println("TX ok");
  //  }
  //
  //  if (txFail)
  //  {
  //    Serial.println("...Failed");
  //  }
}

