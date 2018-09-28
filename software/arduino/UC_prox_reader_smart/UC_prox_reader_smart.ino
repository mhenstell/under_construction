#include <EEPROM.h>
#include <FreqCount.h>
#include <Wire.h>

//#define IRQ 2
//#define PROX_CS 3
#define RECAL_CYCLES 20
#define RECAL_THRESHOLD 2

volatile bool incomingData = false;
volatile uint16_t threshold = 500;

int32_t freq_in = 0;
int32_t freq_zero = 0;
uint32_t freq_cal = 0;
uint32_t freq_out = 0;
uint16_t cal_max = 0;
uint16_t cal = 0;
uint16_t count = 0;

bool touchEventActive = false;
uint8_t outputData = 0;


//#define PROX_MISO 9

//void saveConfig() {
//  EEPROM.put(0, threshold);
//}
//void restoreConfig() {
//  EEPROM.get(0, threshold);
//}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial) {
    delay(1);  // wait until serial console is open, remove if not tethered to computer
  }

  // have to send on master in, *slave out*

//  pinMode(IRQ, OUTPUT);
//  digitalWrite(IRQ, HIGH);

//  pinMode(PROX_CS, INPUT);
//  digitalWrite(PROX_CS, HIGH);

//  pinMode(PROX_MISO, OUTPUT);
//  digitalWrite(PROX_MISO, HIGH);


  //  restoreConfig();

//  // turn on SPI in slave mode
//  SPCR |= bit(SPE);
//
//  // turn on interrupts
//  SPCR |= bit(SPIE);

  Wire.begin();

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

  Serial.println("Ready");

//  delay(3000);
//    attachInterrupt(digitalPinToInterrupt(PROX_CS), proxInterrupt, FALLING);

}

//// SPI interrupt routine
//ISR (SPI_STC_vect)
//{
////  pinMode(MISO, OUTPUT);
//  byte c = SPDR;
//
//  if (c == 1) {
//    SPDR = outputData;
//    return;
//  }
//
//  SPDR = 0;
//  
//  digitalWrite(IRQ, HIGH);
////  pinMode(MISO, INPUT);
//}

//void proxInterrupt()
//{
//  Serial.println("Master is trying to read");
//
//  uint8_t idx = 0;
//  
//  while (idx < 8) {
//    while (digitalRead(SCK) == LOW) {}
//    digitalWrite(PROX_MISO, bitRead(outputData, idx++));
//  }
//
//
//  digitalWrite(IRQ, HIGH);
//}

void recalibrate(uint32_t in)
{
  //  Serial.println("-- RECAL");
  if (cal_max <= RECAL_THRESHOLD) {
    freq_zero = in;
  }
  freq_cal = freq_in;
  cal_max = 0;
}

void loop() {
  if (FreqCount.available()) {
    freq_in = FreqCount.read();

    if (count % RECAL_CYCLES == 0) {
      recalibrate(freq_in);
    }

    cal = abs(freq_in - freq_cal);
    cal_max = max(cal_max, cal);
    freq_out = abs(freq_in - freq_zero);


    if (count % 10 == 0) {
      Serial.print("freq_in: ");
      Serial.print(freq_in);
      Serial.print(" freq_zero: ");
      Serial.print(freq_zero);
      Serial.print(" freq_out: ");
      Serial.print(freq_out);
      Serial.print(" treshold: ");
      Serial.println(threshold);
    }

    if ((freq_out > threshold) && !touchEventActive) {
      touchEvent(true);
    }

    if (touchEventActive && (freq_out < threshold)) {
      touchEvent(false);
    }

    count++;
  }
}

void touchEvent(bool state)
{
  touchEventActive = state;
  outputData = (state == true) ? 0xFF : 0x00;
  Serial.print("Sending touch event: ");
  Serial.println(outputData);
//  digitalWrite(IRQ, LOW);

  Wire.beginTransmission(1);
  Wire.write(outputData);
  Wire.endTransmission();
}

