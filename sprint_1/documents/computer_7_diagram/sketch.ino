#include <DHT.h>

const int computerId = 7;

const int buttonPin1 = 5;
const int ledPin1 = 4;
int buttonState1 = 0;
const int buttonPin2 = 19;
const int ledPin2 = 23;
int buttonState2 = 0;
const int doPin = 13;
const int aoPin = 36;
const int dhtPin = 21;
const int relayPin = 17;
const int humThreshold = 50;
const int pHThreshold = 1000;

DHT dht22(dhtPin, DHT22);

void setup() {
  
  Serial.begin(115200);
  Serial.println("TiãoTech - Log de sensores");

  Serial.print("Computador: ");
  Serial.println(computerId);

  pinMode(buttonPin1, INPUT);
  pinMode(ledPin1, OUTPUT);
  pinMode(buttonPin2, INPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(doPin, INPUT);
  pinMode(aoPin, INPUT);
  pinMode(relayPin, OUTPUT);

  dht22.begin();

// Header

  Serial.print("Limite de umidade: ");
  Serial.println(humThreshold);

  Serial.print("Limite de pH: ");
  Serial.println(pHThreshold);

  Serial.println("time,temperatura,valor_umidade,nivel_umidade,bomba,fosforo,potassio,valor_ph,nivel_ph");
}

void loop() {

  buttonState1 = digitalRead(buttonPin1);
  buttonState2 = digitalRead(buttonPin2);
  // int pHLevel = digitalRead(doPin);
  int pHValue = analogRead(aoPin);
  float humi = dht22.readHumidity();
  float temp = dht22.readTemperature();

// Timestamp
  Serial.print(millis());
  Serial.print(",");

// Temperatura
  Serial.print(temp);
  Serial.print(",");

// Umidade

  Serial.print(humi);
  Serial.print(",");

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

  Serial.print(pHValue);
  Serial.print(",");

  if (pHValue > pHThreshold) {
    Serial.println("baixo");
  } else if (pHValue < pHThreshold) {
    Serial.println("alto");
  } else {
    Serial.println("OK");
  }

  delay(1000); 
}

