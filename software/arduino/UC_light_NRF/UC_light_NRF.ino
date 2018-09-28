//#include <SPI.h>
#include "Arduhdlc.h"
#include <NRFLite.h>
#include <Wire.h>
#include <EEPROM.h>

#define BULB 6

#define BROADCAST 0xFF
#define PROX_DATA 0x01
#define LIGHT_LEVEL 0x02
#define ALL_LEVEL 0x03

#define MAX_HDLC_FRAME_LENGTH 32

uint8_t RADIO_ID = 99;
#define PIN_RADIO_CSN 10
#define PIN_RADIO_IRQ 3
#define PIN_RADIO_CE 8

// Singleton instance of the radio driver
NRFLite _radio;

void send_character(uint8_t data);
void hdlc_frame_handler(const uint8_t *data, uint16_t len);
Arduhdlc hdlc(&send_character, &hdlc_frame_handler, MAX_HDLC_FRAME_LENGTH);

volatile uint16_t proxData = 0;
volatile bool sendProxData = false;
uint32_t lastSent = 0;

void send_character(uint8_t data) {
  Serial.print((char)data);
}

void hdlc_frame_handler(const uint8_t *data, uint16_t len) {

  //  Serial.print("Receive HDLC frame len ");
  //  Serial.print(len);
  //  Serial.print(" : ");
  //  for (int x = 0; x < len; x++) {
  //    if (data[x] < 0x10) Serial.print("0");
  //    Serial.print(data[x], HEX);
  //    Serial.print(" ");
  //  }
  //  Serial.println();

  handlePacket(data);
}


void handlePacket(uint8_t *data)
{
  if (data[0] != RADIO_ID && data[0] != BROADCAST) return;

  if (data[1] == LIGHT_LEVEL) {
  } else if (data[1] == ALL_LEVEL)
  {
    //    Serial.print("Setting light level to ");
    //    Serial.println(data[2 + RADIO_ID]);
    analogWrite(BULB, data[2 + RADIO_ID]);
  }
}

uint8_t getRadioID()
{
  char id[4];
  for (int i = 0; i < 4; i++)
  {
    id[i] = EEPROM.read(i);
  }
  if (String(id).substring(0, 2) == "UC") {
    return String(id).substring(2).toInt();
  } else {
    Serial.println("Invalid Radio ID in EEPROM");
  }
  return 99;
}

void setup()
{
  Serial.begin(115200);

  pinMode(BULB, OUTPUT);
  digitalWrite(BULB, LOW);

  pinMode(PIN_RADIO_IRQ, INPUT);
  digitalWrite(PIN_RADIO_IRQ, HIGH);

  RADIO_ID = getRadioID();

  Serial.print("UC NRF Light Start - Radio #");
  Serial.println(RADIO_ID);
  Serial.println();

  if (!_radio.init(BROADCAST, PIN_RADIO_CE, PIN_RADIO_CSN))
  {
    Serial.println("Cannot communicate with radio");
    while (1); // Wait here forever.
  }

  Serial.println("Ready");

  flash(1);

  Wire.begin(1);
  Wire.onReceive(proxReceive);

  attachInterrupt(digitalPinToInterrupt(PIN_RADIO_IRQ), radioInterrupt, FALLING);

}

void proxReceive(int len)
{
  proxData = Wire.read();
  sendProxData = true;
}

void flash(int times)
{
  for (int i = 0; i < times; i++) {
    analogWrite(BULB, 255);
    delay(50);
    for (int x = 255; x >= 0; x--) {
      analogWrite(BULB, x);
      delay(1);
    }
    delay(100);
  }
}

void loop()
{
  //  if (millis() - lastSent > 50) {
  //    lastSent = millis();
  //
  //    uint8_t buf[10];
  //    uint8_t packet[] = {RADIO_ID, PROX_DATA, count};
  //    uint8_t len = hdlc.makeBuffer(packet, buf, 4);
  //
  //    _radio.send(BROADCAST, buf, len, NRFLite::NO_ACK);
  //  }

  if (sendProxData) {
    uint8_t buf[10];
    uint8_t packet[] = {RADIO_ID, PROX_DATA, proxData};
    uint8_t len = hdlc.makeBuffer(packet, buf, 3);
    _radio.startSend(BROADCAST, buf, len, NRFLite::NO_ACK);
    sendProxData = false;
  }

}


void radioInterrupt() {

  uint8_t txOk, txFail, rxReady;
  uint8_t data[20] = {0};

  _radio.whatHappened(txOk, txFail, rxReady);

  //  if (rxReady)
  //    {
  // Use 'hasDataISR' rather than 'hasData' when using interrupts.

  uint8_t len = _radio.hasDataISR();
  if (len > 0) {

    _radio.readData(&data);

    //    Serial.print("Received Data: ");
    //    for (int i = 0; i < 20; i++) {
    //      if (data[i] > 0x10) Serial.print("0");
    //      Serial.print(data[i]);
    //      Serial.print(" ");
    //    }
    //    Serial.println();
    hdlc.receiveArray(data, len);


  }
  //    }


  //  if (txOk)
  //  {
  //    Serial.println("TX ok");
  //  }

  if (txFail)
  {
    Serial.println("...Failed");
  }
}

