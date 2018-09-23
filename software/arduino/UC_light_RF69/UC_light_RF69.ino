#include <RH_RF69.h>
#include <SPI.h>
#include <EEPROM.h>
#include "Arduhdlc.h"

#define BULB 6
#define PROX_INPUT 5

#define BROADCAST 0xFF
#define PROX_DATA 0x01
#define LIGHT_LEVEL 0x02
#define ALL_LEVEL 0x03

#define MAX_HDLC_FRAME_LENGTH 32

#define PROX_CS 4
#define PROX_IRQ 2

//struct UCConfig
//{
//  uint8_t TouchThreshold;
//};
//
//UCConfig thisConfig;

uint8_t RADIO_ID = 99;           // Our radio's id.
const static uint8_t RFM69_RST = 8;
const static uint8_t PIN_RADIO_CSN = 10;
const static uint8_t PIN_RADIO_IRQ = 3;

// Change to 434.0 or other frequency, must match RX's freq!
#define RF69_FREQ 915.0

// Singleton instance of the radio driver
RH_RF69 rf69(PIN_RADIO_CSN, PIN_RADIO_IRQ);

void send_character(uint8_t data);
void hdlc_frame_handler(const uint8_t *data, uint16_t len);
Arduhdlc hdlc(&send_character, &hdlc_frame_handler, MAX_HDLC_FRAME_LENGTH);

volatile uint16_t count = 0;
long lastSent = 0;


volatile uint8_t newTouchByte = 0;
volatile bool sendTouchByte = true;



void send_character(uint8_t data) {
  Serial.print((char)data);
}

void hdlc_frame_handler(const uint8_t *data, uint16_t len) {

  Serial.print("Receive HDLC frame len ");
  Serial.print(len);
  Serial.print(" : ");
  for (int x = 0; x < len; x++) {
    if (data[x] < 0x10) Serial.print("0");
    Serial.print(data[x], HEX);
    Serial.print(" ");
  }
  Serial.println();

  handlePacket(data);

}

void handlePacket(uint8_t *data)
{
  if (data[0] != RADIO_ID && data[0] != BROADCAST) return;

  if (data[1] == LIGHT_LEVEL) {
    //    Serial.print("Setting light level to ");
    //    Serial.println(data[3]);
    //    analogWrite(BULB, data[3]);
  } else if (data[1] == ALL_LEVEL)
  {
    Serial.print("[");
    Serial.print(RADIO_ID);
    Serial.print("] Setting light level to ");
    Serial.println(data[2 + RADIO_ID]);
    analogWrite(BULB, data[2 + RADIO_ID]);

  }
}

//void readConfiguration(UCConfig *conf)
//{
//  EEPROM.get(100, *conf);
//}
//
//void writeConfiguration(UCConfig *conf)
//{
//  EEPROM.put(100, *conf);
//}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(1);  // wait until serial console is open, remove if not tethered to computer
  }

  char id[4];
  for (int i = 0; i < 4; i++)
  {
    id[i] = EEPROM.read(i);
  }
  if (String(id).substring(0, 2) == "UC") {
    RADIO_ID = String(id).substring(2).toInt();
  } else {
    Serial.println("Invalid Radio ID in EEPROM");
  }

  Serial.print("Radio ID: ");
  Serial.println(RADIO_ID);
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);

  pinMode(PROX_CS, OUTPUT);
  digitalWrite(PROX_CS, HIGH);  // ensure SS stays high for now
  SPI.begin ();
  SPI.setClockDivider(SPI_CLOCK_DIV4);

  pinMode(PROX_IRQ, INPUT);

  pinMode(BULB, OUTPUT);
  digitalWrite(BULB, LOW);

  pinMode(PIN_RADIO_IRQ, INPUT);
  digitalWrite(PIN_RADIO_IRQ, HIGH);

  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);

  Serial.println("Feather Addressed RFM69 TX Test!");
  Serial.println();

  // manual reset
  digitalWrite(RFM69_RST, HIGH);
  delay(10);
  digitalWrite(RFM69_RST, LOW);
  delay(10);

  if (!rf69.init()) {
    Serial.println("RFM69 radio init failed");
    while (1);
  }
  Serial.println("RFM69 radio init OK!");
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM (for low power module)
  // No encryption
  if (!rf69.setFrequency(RF69_FREQ)) {
    Serial.println("setFrequency failed");
  }

  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(14, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW

  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
                  };
  rf69.setEncryptionKey(key);

  Serial.print("RFM69 radio @");  Serial.print((int)RF69_FREQ);  Serial.println(" MHz");

  //  thisConfig.TouchThreshold = 126;
  //  writeConfiguration(&thisConfig);
  //
  //  readConfiguration(&thisConfig);
  //  setThreshold(thisConfig.TouchThreshold);

  delay(1000);
  attachInterrupt(digitalPinToInterrupt(PROX_IRQ), getProxData, FALLING);
}

void getProxData()
{
  cli();
    Serial.print("Prox interrupt: ");

  // enable Slave Select
  digitalWrite(PROX_CS, LOW);
  SPI.transfer(1);   // initiate transmission
  delayMicroseconds(10);
  uint8_t input = SPI.transfer(0);
  digitalWrite(PROX_CS, HIGH);

    Serial.println(input);

  newTouchByte = input;
  sendTouchByte = true;
  
  sei();
}

//void setThreshold(uint8_t threshold)
//{
//  digitalWrite(PROX_CS, LOW);
//  SPI.transfer(2);
//  delayMicroseconds(10);
//  SPI.transfer(threshold);
//  digitalWrite(PROX_CS, HIGH);
//}

void loop()
{

  //  if (millis() - lastSent > 50) {
  //    lastSent = millis();
  //
  //    Serial.print("Sending ");
  //    Serial.println(count);
  //    uint8_t buf[10];
  //    uint8_t packet[] = {RADIO_ID, PROX_DATA, count >> 8, count & 0xFF};
  //    uint8_t len = hdlc.makeBuffer(packet, buf, 4);
  //    rf69.send(buf, 8);
  //    rf69.waitPacketSent();
  //  }

    if (rf69.available()) {
      uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];
      uint8_t len = sizeof(buf);
      if (rf69.recv(buf, &len)) {
        hdlc.receiveArray(buf, len);
      } else {
        Serial.println("Receive failed");
      }
    }

  if (sendTouchByte)
  {
    Serial.print("Touch byte: ");
    Serial.println(newTouchByte);

    uint8_t buf[10];
    uint8_t packet[] = {RADIO_ID, PROX_DATA, newTouchByte};
    uint8_t len = hdlc.makeBuffer(packet, buf, sizeof(packet) / sizeof(packet[0]));

    rf69.send(buf, len);
    rf69.waitPacketSent();

    Serial.println("Sent");


    sendTouchByte = false;
  }

}

//void serialEvent() {
//
//  //  Serial.println("Serial");
//  uint8_t buf[100];
//  uint8_t idx = 0;
//  while (Serial.available()) {
//    //    hdlc.receive((char)Serial.read());
//    buf[idx++] = Serial.read();
//  }
//
//  Serial.print("Received: ");
//
//  for (int x = 0; x < idx; x++) {
//    if (buf[x] < 0x10) Serial.print("0");
//    Serial.print(buf[x], HEX);
//  }
//  Serial.println();
//
//}

