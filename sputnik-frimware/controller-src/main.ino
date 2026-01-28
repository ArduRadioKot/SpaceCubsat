#include <SoftwareSerial.h>
#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

RH_RF95 rf95(RFM95_CS, RFM95_INT);

const int SATELLITE_ID = 1;

struct TelemetryData {
  int satellite_id;
  float temperature;
  float voltage;
  float current;
  int signal_strength;
  unsigned long timestamp;
};

struct Command {
  int command_type;
  int value1;
  int value2;
  int value3;
};

#define IMAGE_BUFFER_SIZE 1024
byte imageBuffer[IMAGE_BUFFER_SIZE];
int imageIndex = 0;
bool receivingImage = false;

void setup() {
  Serial.begin(9600);
  
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);
  if (!rf95.init()) {
    Serial.println("Radio init failed");
    while (1);
  }
  
  if (!rf95.setFrequency(433.92)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  
  rf95.setTxPower(20, false);
  
  Serial.println("Radio initialized");
  Serial.println("SIT-Space Satellite Controller Ready");
}

void loop() {
  static unsigned long lastTelemetry = 0;
  if (millis() - lastTelemetry > 5000) {
    sendTelemetry();
    lastTelemetry = millis();
  }
  receiveCommands();
  receiveImageData();
  
  delay(100);
}

void sendTelemetry() {
  TelemetryData telemetry;
  
  telemetry.satellite_id = SATELLITE_ID;
  telemetry.temperature = 20.0 + (analogRead(A0) / 1024.0) * 10.0;
  telemetry.voltage = 3.3 + (analogRead(A1) / 1024.0) * 1.7;
  telemetry.current = (analogRead(A2) / 1024.0) * 500.0;
  telemetry.signal_strength = rf95.lastRssi();
  telemetry.timestamp = millis();
  
  rf95.send((uint8_t*)&telemetry, sizeof(telemetry));
  rf95.waitPacketSent();
  
  Serial.print("TELEMETRY:");
  Serial.print(telemetry.satellite_id);
  Serial.print(",");
  Serial.print(telemetry.temperature);
  Serial.print(",");
  Serial.print(telemetry.voltage);
  Serial.print(",");
  Serial.print(telemetry.current);
  Serial.print(",");
  Serial.print(telemetry.signal_strength);
  Serial.print(",");
  Serial.println(telemetry.timestamp);
}

void receiveCommands() {
  if (rf95.available()) {
    uint8_t buf[sizeof(Command)];
    uint8_t len = sizeof(buf);
    
    if (rf95.recv(buf, &len)) {
      Command* cmd = (Command*)buf;
      
      Serial.print("COMMAND:");
      Serial.print(cmd->command_type);
      Serial.print(",");
      Serial.print(cmd->value1);
      Serial.print(",");
      Serial.print(cmd->value2);
      Serial.print(",");
      Serial.println(cmd->value3);
      
      processCommand(cmd);
    }
  }
}

void processCommand(Command* cmd) {
  switch (cmd->command_type) {
    case 1: 
      Serial.print("ROTATE:");
      Serial.print(cmd->value1); // X axis
      Serial.print(",");
      Serial.print(cmd->value2); // Y axis
      Serial.print(",");
      Serial.println(cmd->value3); // Z axis
      break;
      
    case 2: 
      Serial.println("TAKE_PHOTO");
      break;
      
    case 3: 
      Serial.println("SYSTEM_RESET");
      break;
      
    default:
      Serial.println("UNKNOWN_COMMAND");
      break;
  }
}

void receiveImageData() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    
    if (data.startsWith("IMAGE_START:")) {
      receivingImage = true;
      imageIndex = 0;
      Serial.println("IMAGE_RECEIVE_START");
      
    } else if (data.startsWith("IMAGE_DATA:") && receivingImage) {
      String hexData = data.substring(11);
      
      for (int i = 0; i < hexData.length() && imageIndex < IMAGE_BUFFER_SIZE; i += 2) {
        String hexByte = hexData.substring(i, i + 2);
        imageBuffer[imageIndex++] = strtol(hexByte.c_str(), NULL, 16);
      }
      
      Serial.print("IMAGE_PROGRESS:");
      Serial.println(imageIndex);
      
    } else if (data.startsWith("IMAGE_END") && receivingImage) {
      receivingImage = false;
      Serial.print("IMAGE_RECEIVED:");
      Serial.println(imageIndex);
      
      transmitImage(imageBuffer, imageIndex);
      
    } else if (data.startsWith("ZONE_DETECTED:")) {
      Serial.println("ZONE_ALERT");

      String alert = "ZONE_ALERT:" + data.substring(14);
      rf95.send((uint8_t*)alert.c_str(), alert.length());
      rf95.waitPacketSent();
    }
  }
}

void transmitImage(byte* imageData, int imageSize) {
  Serial.println("TRANSMITTING_IMAGE");
  const int chunkSize = 64;
  int chunks = (imageSize + chunkSize - 1) / chunkSize;
  
  for (int i = 0; i < chunks; i++) {
    int offset = i * chunkSize;
    int size = min(chunkSize, imageSize - offset);
    
    rf95.send((uint8_t*)"IMG", 3);
    rf95.waitPacketSent();
    delay(10);

    rf95.send(&imageData[offset], size);
    rf95.waitPacketSent();
    
    Serial.print("CHUNK:");
    Serial.print(i + 1);
    Serial.print("/");
    Serial.println(chunks);
    
    delay(100); 
  }
  rf95.send((uint8_t*)"END", 3);
  rf95.waitPacketSent();
  
  Serial.println("IMAGE_TRANSMITTED");
}