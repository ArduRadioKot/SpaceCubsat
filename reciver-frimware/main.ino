/*
 * CubeSat Telemetry Receiver
 * This Arduino code simulates receiving telemetry data from CubeSats
 * and sends it to the Flask server via Serial/UART
 * 
 * Expected output format: ID:1,T:25.5,B:3.7,S:-45,A:520,V:7.6,STATUS:Active
 * Where:
 * ID = Satellite ID (1-6)
 * T = Temperature in Celsius
 * B = Battery voltage
 * S = Signal strength in dBm
 * A = Altitude in km
 * V = Orbital velocity in km/s
 * STATUS = Satellite status
 */

#include <SoftwareSerial.h>

struct SatelliteData {
  int id;
  float temperature;
  float battery;
  int signalStrength;
  float altitude;
  float velocity;
  String status;
};

SatelliteData satellites[6];
unsigned long previousMillis = 0;
const long interval = 2000;
int currentSatellite = 0;

void setup() {
  Serial.begin(9600);
  
  initializeSatellites();
  
  Serial.println("CubeSat Telemetry Receiver Initialized");
  Serial.println("Starting telemetry transmission...");
  delay(1000);
}

void loop() {
  unsigned long currentMillis = millis();
  
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    updateSatelliteData(currentSatellite);
    sendTelemetry(currentSatellite);
    currentSatellite = (currentSatellite + 1) % 6;
  }
  delay(100);
}

void initializeSatellites() {
  satellites[0] = {1, 25.5, 3.7, -45, 500, 7.6, "Active"};
  satellites[1] = {2, -10.2, 4.1, -52, 600, 7.7, "Active"};
  satellites[2] = {3, 35.8, 3.3, -38, 550, 7.5, "Maintenance"};
  satellites[3] = {4, 15.3, 3.9, -48, 520, 7.6, "Active"};
  satellites[4] = {5, -5.7, 2.8, -65, 480, 7.4, "Inactive"};
  satellites[5] = {6, 28.9, 4.0, -42, 510, 7.6, "Active"};
}

void updateSatelliteData(int satelliteIndex) {
  
  float tempChange = random(-50, 51) / 100.0; 
  satellites[satelliteIndex].temperature += tempChange;
  
  if (satellites[satelliteIndex].temperature > 50) {
    satellites[satelliteIndex].temperature = 50;
  } else if (satellites[satelliteIndex].temperature < -30) {
    satellites[satelliteIndex].temperature = -30;
  }
  satellites[satelliteIndex].battery -= random(1, 6) / 1000.0; 
  
  if (satellites[satelliteIndex].battery > 4.2) {
    satellites[satelliteIndex].battery = 4.2;
  } else if (satellites[satelliteIndex].battery < 2.5) {
    satellites[satelliteIndex].battery = 2.5;
  }
  int signalChange = random(-10, 11);
  satellites[satelliteIndex].signalStrength += signalChange;
  
  if (satellites[satelliteIndex].signalStrength > -20) {
    satellites[satelliteIndex].signalStrength = -20;
  } else if (satellites[satelliteIndex].signalStrength < -80) {
    satellites[satelliteIndex].signalStrength = -80;
  }
  
  float altChange = random(-20, 21) / 10.0; 
  satellites[satelliteIndex].altitude += altChange;
  
  if (satellites[satelliteIndex].altitude > 650) {
    satellites[satelliteIndex].altitude = 650;
  } else if (satellites[satelliteIndex].altitude < 450) {
    satellites[satelliteIndex].altitude = 450;
  }
  
  float velChange = random(-5, 6) / 100.0; 
  satellites[satelliteIndex].velocity += velChange;
  
  if (satellites[satelliteIndex].velocity > 8.0) {
    satellites[satelliteIndex].velocity = 8.0;
  } else if (satellites[satelliteIndex].velocity < 7.0) {
    satellites[satelliteIndex].velocity = 7.0;
  }
  
  if (random(1, 101) <= 5) { 
    String statuses[] = {"Active", "Inactive", "Maintenance"};
    satellites[satelliteIndex].status = statuses[random(0, 3)];
  }
}

void sendTelemetry(int satelliteIndex) {
  SatelliteData sat = satellites[satelliteIndex];
  String telemetry = "ID:" + String(sat.id) + 
                     ",T:" + String(sat.temperature, 1) + 
                     ",B:" + String(sat.battery, 2) + 
                     ",S:" + String(sat.signalStrength) + 
                     ",A:" + String(sat.altitude, 1) + 
                     ",V:" + String(sat.velocity, 2) + 
                     ",STATUS:" + sat.status;
  
  Serial.println(telemetry);

  Serial.print("Satellite ");
  Serial.print(sat.id);
  Serial.print(" - Temp: ");
  Serial.print(sat.temperature);
  Serial.print("°C, Battery: ");
  Serial.print(sat.battery);
  Serial.print("V, Signal: ");
  Serial.print(sat.signalStrength);
  Serial.print("dBm, Alt: ");
  Serial.print(sat.altitude);
  Serial.print("km, Vel: ");
  Serial.print(sat.velocity);
  Serial.print("km/s, Status: ");
  Serial.println(sat.status);
}

void checkForCommands() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "RESET") {
      initializeSatellites();
      Serial.println("Satellite data reset");
    } else if (command.startsWith("SET_STATUS:")) {
      int colonIndex = command.indexOf(':');
      if (colonIndex > 0) {
        int satId = command.substring(colonIndex + 1, command.indexOf(':', colonIndex + 1)).toInt();
        String newStatus = command.substring(command.indexOf(':', colonIndex + 1) + 1);
        
        if (satId >= 1 && satId <= 6) {
          satellites[satId - 1].status = newStatus;
          Serial.print("Satellite ");
          Serial.print(satId);
          Serial.print(" status set to: ");
          Serial.println(newStatus);
        }
      }
    }
  }
}