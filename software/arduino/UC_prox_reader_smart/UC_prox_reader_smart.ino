#include <EEPROM.h>
#include <FreqCount.h>

#define IRQ 2
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
  pinMode(MISO, OUTPUT);

  pinMode(IRQ, OUTPUT);
  digitalWrite(IRQ, HIGH);

//  restoreConfig();

  // turn on SPI in slave mode
  SPCR |= bit(SPE);

  // turn on interrupts
  SPCR |= bit(SPIE);

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
}

// SPI interrupt routine
ISR (SPI_STC_vect)
{
  byte c = SPDR;

//  if (incomingData)
//  {
//    threshold = c * 4;
//    incomingData = false;
//    saveConfig();
//  } else {

    if (c == 1) {
      SPDR = outputData;
      return;
    } 
//    else if (c == 2) {
//      incomingData = true;
//      SPDR = 0;
//      return;
//    }
//  }
  SPDR = 0;
  digitalWrite(IRQ, HIGH);
}

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
  digitalWrite(IRQ, LOW);
}

