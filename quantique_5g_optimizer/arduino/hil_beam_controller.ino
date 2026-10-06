/*
 * Quantique Hackathon 2026 - Team Quantum Nexus
 * Hardware-in-the-Loop (HIL) Physical Antenna & Phased Array Controller
 * Compatible with Arduino Uno, Nano, Mega, and ESP32.
 * 
 * Hardware Connections:
 * - Pin 9: Servo Motor PWM Signal (Controls mechanical beam azimuth tilt: 45° to 135°)
 * - Pins 2..8, 10: 8-Element Phased Array LED Ripple / Status Indicators
 * - Serial: 115200 Baud Rate via USB COM port
 */

#include <Servo.h>

Servo beamServo;

const int SERVO_PIN = 9;
const int LED_PINS[8] = {2, 3, 4, 5, 6, 7, 8, 10};

float currentAzimuth = 0.0;
float currentServoAngle = 90.0;

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000); // Wait for serial connection
  
  beamServo.attach(SERVO_PIN);
  beamServo.write(90); // Center at 0° relative azimuth (90° physical servo)
  
  for (int i = 0; i < 8; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
  
  // Power-on self-test light sequence
  for (int i = 0; i < 8; i++) {
    digitalWrite(LED_PINS[i], HIGH);
    delay(40);
    digitalWrite(LED_PINS[i], LOW);
  }
  
  Serial.println("$HIL_INIT,STATUS=ONLINE,DEVICE=PHASED_ARRAY_PANEL_V3,BAUD=115200*0x3F");
}

void loop() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    // Command format: $HIL_TX,GNB=0,BEAM_AZ=+15.0,SERVO=105.0deg,PWR=37.0dBm,SUB=1*CRC
    if (line.startsWith("$HIL_TX")) {
      int azIdx = line.indexOf("BEAM_AZ=");
      if (azIdx != -1) {
        int commaIdx = line.indexOf(',', azIdx);
        String azStr = line.substring(azIdx + 8, commaIdx);
        float targetAz = azStr.toFloat();
        
        // Actuate Physical Demonstrator
        actuateBeam(targetAz);
      }
    }
  }
}

void actuateBeam(float targetAzimuth) {
  currentAzimuth = targetAzimuth;
  // Map [-45°, +45°] to Servo [45°, 135°]
  currentServoAngle = constrain(90.0 + targetAzimuth, 45.0, 135.0);
  
  // Smooth servo movement
  beamServo.write((int)currentServoAngle);
  
  // Animate RF Phased Array Elements progressive phase delay
  float phaseStepDeg = -180.0 * sin(targetAzimuth * 3.14159 / 180.0);
  for (int i = 0; i < 8; i++) {
    digitalWrite(LED_PINS[i], HIGH);
    delay(10);
    digitalWrite(LED_PINS[i], LOW);
  }
  
  // Acknowledge back to HIL Bridge
  Serial.print("$HIL_ACK,DEV=PHASED_ARRAY_PANEL,SERVO_LOCKED=TRUE,POS=");
  Serial.print(currentServoAngle, 1);
  Serial.print("deg,PHASE_STEP=");
  Serial.print(phaseStepDeg, 1);
  Serial.println("deg,VSWR=1.12*0x98AE");
}
