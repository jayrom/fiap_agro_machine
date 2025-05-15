#include <DHT.h>

const int buttonPin1 = 5;
const int ledPin1 = 4;
int buttonState1 = 0;
const int buttonPin2 = 19;
const int ledPin2 = 23;
int buttonState2 = 0;
const int doPin = 13;
const int dhtPin = 21;
const int relayPin = 17;
const int humThreshold = 50;

DHT dht22(dhtPin, DHT22);

void setup() {
  
  Serial.begin(115200);
  Serial.println("TiãoTech - Log de sensores");

  pinMode(buttonPin1, INPUT);
  pinMode(ledPin1, OUTPUT);
  pinMode(buttonPin2, INPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(doPin, INPUT);
  pinMode(relayPin, OUTPUT);

  dht22.begin();

// Header

  Serial.println("time,temperatura,umidade,bomba,fósforo,potássio,pH");
}

void loop() {

  buttonState1 = digitalRead(buttonPin1);
  buttonState2 = digitalRead(buttonPin2);
  int lightState = digitalRead(doPin);
  float humi = dht22.readHumidity();
  float temp = dht22.readTemperature();

// Timestamp
  Serial.print(millis());
  Serial.print(",");

// Temperatura
  Serial.print(temp);
  Serial.print(",");

// Umidade

  if (humi < humThreshold) {

    digitalWrite(relayPin, HIGH);
    Serial.print("baixa");
    Serial.print(",");
    Serial.print("ligada");

  } else {

    digitalWrite(relayPin, LOW);    
    Serial.print("OK");
    Serial.print(",");
    Serial.print("desligada");
  }
  Serial.print(",");

// Fósforo

  if (buttonState1 == HIGH) {
    digitalWrite(ledPin1, HIGH);
    Serial.print("OK");
  } else {
    digitalWrite(ledPin1, LOW);
    Serial.print("baixo");
  }
  Serial.print(",");

  // Potássio

  if (buttonState2 == HIGH) {
    digitalWrite(ledPin2, HIGH);
    Serial.print("OK");
  } else {
    digitalWrite(ledPin2, LOW);
    Serial.print("baixo");
  }
  Serial.print(",");

  // pH

  if (lightState == HIGH) {
    Serial.println("baixo");
  } else {
    Serial.println("alto");
  }

  delay(1000); 
}

