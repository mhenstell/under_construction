#include <EEPROM.h>
#include <FreqCount.h>
#include "Arduhdlc.h"

// Pins
#define BULB 20

// Default settings
#define MAX_HDLC_FRAME_LENGTH 32
#define PROX_PERIOD 200
#define HEARTBEAT_PERIOD 1000

// Config defines
#define MAGIC_NUMBER 0xBEEF
#define ID_ADDRESS 0
#define CONFIG_ADDRESS 4
#define LATEST_VERSION 0

#define TOUCH_THRESHOLD 0x11
#define RECAL_THRESHOLD 0x12

// HDLC defines
#define BROADCAST 0xFF
#define PROX_DATA 0x01
#define LIGHT_LEVEL 0x02
#define ALL_LEVEL 0x03
#define HEARTBEAT 0x99
#define STARTUP 0xA1
#define CONFIG_ACK 0x20
#define SET_CONFIG 0x10
#define TOUCH_TRIG 0x30
#define TOUCH_UNTRIG 0x31


uint8_t RADIO_ID;

struct __attribute__((__packed__)) UCConfig_s
{
  uint16_t MagicNumber;
  uint8_t VersionNumber;
  uint16_t RecalThreshold;
  uint16_t TouchThreshold;
  uint8_t RecalCycles;
  uint16_t SendProx;
} UCConfig_default = {MAGIC_NUMBER, LATEST_VERSION, 5, 250, 20, 255};

typedef struct UCConfig_s UCConfig;

// Frequency variables
int32_t freq_in = 0;
int32_t freq_zero = 0;
uint32_t freq_cal = 0;
uint32_t freq_out = 0;
uint16_t cal_max = 0;
uint16_t cal = 0;
uint16_t count = 0;

// Other variables
bool touchEventActive = false;
uint8_t outputData = 0;
UCConfig thisConfig;
uint32_t lastProx = 0;

uint8_t in_pkt[100];
uint8_t ip_len = 0;
bool processIncoming = false;

UCConfig initConfig()
{
  UCConfig readConfig = UCConfig_default;
  EEPROM.get(CONFIG_ADDRESS, readConfig);

  if (readConfig.MagicNumber != MAGIC_NUMBER) {
    Serial.println("No config found in EEPROM, using default values");
    return readConfig;
  }

  Serial.println("Found config in EEPROM:");
  printConfig(&readConfig);
  return readConfig;
}

void saveConfig(UCConfig *config)
{
  EEPROM.put(CONFIG_ADDRESS, *config);
}

void printConfig(UCConfig *config)
{
  Serial.print("MagicNumber: ");
  Serial.println(config->MagicNumber, HEX);
  Serial.print("VersionNumber: ");
  Serial.println(config->VersionNumber, HEX);
  Serial.print("RecalThreshold: ");
  Serial.println(config->RecalThreshold, HEX);
  Serial.print("TouchThreshold: ");
  Serial.println(config->TouchThreshold, HEX);
  Serial.print("RecalCycles: ");
  Serial.println(config->RecalCycles, HEX);
  Serial.print("SendProx: ");
  Serial.println(config->SendProx, HEX);
  Serial.println();
}

// HDLC Stuff
void send_character(uint8_t data);
void hdlc_frame_handler(const uint8_t *data, uint16_t len);
Arduhdlc hdlc(&send_character, &hdlc_frame_handler, MAX_HDLC_FRAME_LENGTH);
void send_character(uint8_t data) {}

void hdlc_frame_handler(const uint8_t *data, uint16_t len) {


  if (data[0] != 0xFF && data[0] != RADIO_ID) return;

  switch (data[1]) {
    case ALL_LEVEL:
      analogWrite(BULB, data[2 + RADIO_ID]);
      break;
    case SET_CONFIG:
      setConfig(data);
      break;
  }

  //    Serial.print("Receive HDLC frame len ");
  //    Serial.print(len);
  //    Serial.print(" : ");
  //    for (int x = 0; x < len; x++) {
  //      if (data[x] < 0x10) Serial.print("0");
  //      Serial.print(data[x], HEX);
  //      Serial.print(" ");
  //    }
  //    Serial.println();


}

void setConfig(const uint8_t *data)
{
  UCConfig newConfig;
  Serial.print("Copy config size ");
  Serial.println(sizeof(UCConfig));
  memcpy(&newConfig, data + 2, sizeof(UCConfig));

  if (newConfig.MagicNumber != MAGIC_NUMBER) {
    Serial.println("Received invalid config");
    return;
  }

  Serial.println("Saving new config");
  printConfig(&newConfig);

  thisConfig = newConfig;
  saveConfig(&thisConfig);
  ackConfig(&thisConfig);
}

void ackConfig(UCConfig *config)
{
  uint8_t buf[20];
  uint8_t packet[20] = {RADIO_ID, CONFIG_ACK};
  memcpy(packet + 2, config, sizeof(UCConfig));
  uint8_t len = hdlc.makeBuffer(packet, buf, sizeof(UCConfig) + 2);

  Serial.print("Acking config: ");
  for (int x = 0; x < len; x++) {
    if (buf[x] < 0x10) Serial.print("0");
    Serial.print(buf[x], HEX);
    Serial.print(" ");
  }
  Serial.println();

  for (int i = 0; i < len; i++) {
    Serial1.print((char)buf[i]);
  }

}

uint8_t getRadioID()
{
  char id[4];
  for (int i = ID_ADDRESS + 0; i < 4; i++)
  {
    id[i] = EEPROM.read(i);
  }

  for (int i = 0; i < 4; i++) {
    Serial.print(id[i]);
  }

  if (String(id).substring(0, 2) == "UC") {
    return String(id).substring(2).toInt();
  } else {
    Serial.println("Invalid Radio ID in EEPROM");
  }
  return 0;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial1.begin(115200);

  pinMode(BULB, OUTPUT);

  // UCConfig test = UCConfig_default;
  // saveConfig(&test);

  // Get Radio ID from EEPROM
  RADIO_ID = getRadioID();

  thisConfig = initConfig();
  printConfig(&thisConfig);

  FreqCount.begin(25);

  uint8_t i = 10;
  while (i) {
    if (FreqCount.available()) {
      i--;
    }
  }
  uint32_t count = FreqCount.read();
  freq_zero = count;
  freq_cal = count;
  cal_max = 0;

  thisConfig.TouchThreshold = 250;

  Serial.println("Ready");
}

void recalibrate(uint32_t in)
{
  //  Serial.println("-- RECAL");
  if (cal_max <= thisConfig.RecalThreshold) {
    freq_zero = in;
  }
  freq_cal = freq_in;
  cal_max = 0;
}

void loop() {
  if (FreqCount.available()) {
    freq_in = FreqCount.read();

    if (count % thisConfig.RecalCycles == 0) {
      recalibrate(freq_in);
    }

    cal = abs(freq_in - freq_cal);
    cal_max = max(cal_max, cal);
    freq_out = abs(freq_in - freq_zero);

    if ((freq_out > thisConfig.TouchThreshold) && !touchEventActive) {
      touchEvent(true);
    }

    if (touchEventActive && (freq_out < thisConfig.TouchThreshold)) {
      touchEvent(false);
    }

    if (count % 10 == 0) {
      Serial.print("freq_in: ");
      Serial.print(freq_in);
      Serial.print(" freq_zero: ");
      Serial.print(freq_zero);
      Serial.print(" freq_out: ");
      Serial.print(freq_out);
      Serial.print(" TT: ");
      Serial.print(thisConfig.TouchThreshold);
      Serial.print(" RT: ");
      Serial.print(thisConfig.RecalThreshold);
      Serial.print(" SP: ");
      Serial.println(thisConfig.SendProx);
    }

    count++;
  }

  if (millis() - lastProx > thisConfig.SendProx)
  {
    uint8_t buf[10];
    uint8_t packet[4] = {RADIO_ID, PROX_DATA, (freq_out >> 8) & 0xFF, freq_out & 0xFF};
    uint8_t len = hdlc.makeBuffer(packet, buf, sizeof(packet) / sizeof(packet[0]));

    for (int i = 0; i < len; i++) {
      Serial1.print((char)buf[i]);
    }
    lastProx = millis();
  }

}
//
void serialEvent1() {
  while (Serial1.available()) {
    hdlc.receive(Serial1.read());
  }
}


void touchEvent(bool state)
{
  touchEventActive = state;
  //  outputData = (state == true) ? 0xFF : 0x00;

  Serial.print("Touch: ");
  Serial.println(outputData);

  uint8_t output = (state == true) ? TOUCH_TRIG : TOUCH_UNTRIG;

  uint8_t buf[10];
  uint8_t packet[2] = {RADIO_ID, output};
  uint8_t len = hdlc.makeBuffer(packet, buf, sizeof(packet) / sizeof(packet[0]));

  for (int i = 0; i < len; i++) {
    Serial1.print((char)buf[i]);
  }
  delay(1);
  for (int i = 0; i < len; i++) {
    Serial1.print((char)buf[i]);
  }

}
