#include <RH_RF69.h>
#include <SPI.h>
#include <EEPROM.h>
#include "Arduhdlc.h"


#define BROADCAST 0xFF
#define PROX_DATA 0x01
#define LIGHT_LEVEL 0x02
#define STARTUP 0x03
#define HEARTBEAT 0x99

//#define RING_BUFFER_DEPTH 20
#define MAX_HDLC_FRAME_LENGTH 32

const static uint8_t RFM69_RST = 10;
const static uint8_t PIN_RADIO_CSN = 0;
const static uint8_t PIN_RADIO_IRQ = 3;

uint8_t RADIO_ID = 99;

//volatile bool readyToSend = false;
uint8_t incomingByte = 0;
uint8_t incomingPacketArray[4] = {0};
uint8_t incomingPacketIndex = 0;

// Change to 434.0 or other frequency, must match RX's freq!
#define RF69_FREQ 915.0

// Singleton instance of the radio driver
RH_RF69 rf69(PIN_RADIO_CSN, PIN_RADIO_IRQ);

//IntervalTimer myTimer;

long lastHeartbeat = 0;

void send_character(uint8_t data);
void hdlc_frame_handler(const uint8_t *data, uint16_t len);
Arduhdlc hdlc(&send_character, &hdlc_frame_handler, MAX_HDLC_FRAME_LENGTH);

void send_character(uint8_t data) {
  Serial.print((char)data);
}

void hdlc_frame_handler(const uint8_t *data, uint16_t len) {
  rf69.send(data, len);
}

//void sendSerialPacket(uint8_t cmd, uint16_t payload)
//{
//  char buf[] = {BROADCAST, STARTUP, 0x0000};
//  hdlc.send(buf, 4);
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
    Serial.println("UC");
  }

  
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);

  // manual reset
  digitalWrite(RFM69_RST, HIGH);
  delay(10);
  digitalWrite(RFM69_RST, LOW);
  delay(10);

  if (!rf69.init()) {
    while (true) {
      char msg[] = "RFM69 radio init failed";
      hdlc.send(msg, sizeof(msg) / sizeof(msg[0]));
      delay(1000);
    }
  }
      Serial.println("RFM69 radio init OK!");
  
  if (!rf69.setFrequency(RF69_FREQ)) {
    //      Serial.println("setFrequency failed");
    while (true) {
      char msg[] = "setFrequency failed";
      hdlc.send(msg, sizeof(msg) / sizeof(msg[0]));
      delay(1000);
    }
  }

  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(14, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW

  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
                  };
  rf69.setEncryptionKey(key);
//  sendSerialPacket(STARTUP, RADIO_ID);
  Serial.println("Ready");
}

//void sendPackets() {
//  if (txRingBufferIdx != txRingBufferLastSent) {
//    noInterrupts();
//    Serial.print("Sending ");
//    Serial.println(txRingBufferLastSent);
//    rf69.send(ringBuffer[txRingBufferLastSent++], sizeof(ringBuffer[0]));
//    txRingBufferLastSent %= RING_BUFFER_DEPTH;
//    interrupts();
//  }
//}

//void debugPrintPacket(UCSensorPacket packet)
//{
//  String msg = "Debug Packet: To: ";
//  msg += packet.FromRadioId;
//  msg += " CMD: ";
//  msg += packet.Command;
//  msg += " DATA: ";
//  msg += packet.Payload;
//  Serial.println(msg);
//}

void loop()
{
  if (rf69.available()) {

    // Should be a message for us now
    uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf69.recv(buf, &len)) {
      for (int x = 0; x < len; x++) {
        Serial.print(char(buf[x]));
      }
    } else {
      Serial.println("Receive failed");
    }
  }

  //    if (millis() - lastHeartbeat > 1000) {
  //      char buf[] = {BROADCAST, HEARTBEAT, 0, RADIO_ID};
  //      hdlc.send(buf, 4);
  //      lastHeartbeat = millis();
  //
  //    }

}

void serialEvent() {

  uint8_t buf[100];
  uint8_t idx = 0;
  while (Serial.available()) {
    //    hdlc.receive((char)Serial.read());
    buf[idx++] = Serial.read();
  }

  rf69.send(buf, idx);

  //  if (Serial.available() >= 4) {
  //    for (int b = 0; b < 4; b++) {
  //      ringBuffer[txRingBufferIdx][b] = Serial.read();
  //    }
  //    if (Serial.read() == '\n') {
  //      Serial.print("Received packet: ");
  //      for (int x = 0; x < 4; x++) {
  //        if (ringBuffer[txRingBufferIdx][x] < 0x10) Serial.print("0");
  //        Serial.print(ringBuffer[txRingBufferIdx][x], HEX);
  //      }
  //      Serial.println();
  //      txRingBufferIdx++;
  //    } else {
  //      Serial.println("Invalid packet");
  //    }
  //  }



  //  while (Serial.available()) {
  //    Serial.print("Available: ");
  //    Serial.println(Serial.available());
  //    incomingByte = Serial.read();
  //
  //    if (incomingByte == '\n') {
  //
  //      //      Serial.print("Received packet ");
  //      //      Serial.println(txRingBufferIdx);
  //
  ////      memcpy(&txRingBuffer[txRingBufferIdx++], incomingPacketArray, sizeof(txRingBuffer[txRingBufferIdx]));
  ////      memset(incomingPacketArray, 0, sizeof(incomingPacketArray));
  ////      incomingPacketIndex = 0;
  //      Serial.print("Received packet: ");
  //      for (int x=0; x < 4; x++) {
  //        if (ringBuffer[txRingBufferIdx][x] < 0x10) Serial.print("0");
  //        Serial.print(ringBuffer[txRingBufferIdx][x], HEX);
  //      }
  //      Serial.println();
  //      byteIndex = 0;
  //      txRingBufferIdx++;
  //
  //      txRingBufferIdx %= RING_BUFFER_DEPTH;
  //    } else {
  //
  ////      if (incomingPacketIndex >= sizeof(UCSensorPacket)) {
  ////        Serial.println("Invalid packet");
  ////        memset(incomingPacketArray, 0, sizeof(incomingPacketArray));
  ////        incomingPacketIndex = 0;
  ////      } else {
  ////        incomingPacketArray[incomingPacketIndex] = incomingByte;
  //        ringBuffer[txRingBufferIdx][byteIndex++] = incomingByte;
  ////        incomingPacketIndex++;
  ////      }
  //    }
  //  }
}

