#include "Parser.h"
#include <GyverBME280.h>
GyverBME280 bme;
#include <SPI.h>
#include <SD.h>
const byte chipSelect = 4;
bool sdCardCheck = 0;
bool flag = 0;
bool recording = 0;
bool startRecording = 0;
//=========================Setup==================
void setup() {
  Serial.begin(115200);
  pinMode(13, OUTPUT);
  if (!SD.begin(chipSelect)) {
    sdCardCheck = 1;
  }
  bme.begin();
}
//====================MainLoop=========================
void loop() {
  //=================ReadData======================
  if (Serial.available()) {
    char buf[50];
    int num = Serial.readBytesUntil(';', buf, 50);
    buf[num] = NULL;
    Parser data(buf, ',');
    int ints[10];
    data.parseInts(ints);
    switch (ints[0]) {
      case 0:
        digitalWrite(13, ints[1]);
        break;
      case 1:
        recording = ints[1];
        break;
    }
  }
  static uint32_t tmr = 0;
  if (millis() - tmr > 100) {
    tmr = millis();
    //==================SendData===========================
    if (sdCardCheck) {
      Serial.print(3);
      Serial.print(',');
      Serial.println(1);
    } else {
      Serial.print(1);
      Serial.print(',');
      Serial.print(bme.readTemperature());
      Serial.print(',');
      Serial.print(bme.readHumidity());
      Serial.print(',');
      Serial.println(pressureToMmHg(bme.readPressure()));
    }
    //===============SD====================
    if (!sdCardCheck && recording) {
      static uint32_t timeSD = 0;
      if (startRecording == 0) {
        timeSD = millis();
        startRecording = 1;
      }
      String dataString = "";
      dataString += String(millis() - timeSD);
      dataString += ",";
      dataString += String(bme.readTemperature());
      dataString += ",";
      dataString += String(pressureToMmHg(bme.readPressure()));
      dataString += ",";
      dataString += String(bme.readHumidity());
      File dataFile = SD.open("datalog.csv", FILE_WRITE);
      if (dataFile) {
        if (flag == 0) {
          dataFile.println("Time,Temperature,Pressure,Humidity");
          flag = 1;
        }
        dataFile.println(dataString);
        dataFile.close();
      } else {
        Serial.print(3);
        Serial.print(',');
        Serial.println(2);
      }
    } else {
      startRecording = 0;
    }
  }
}
