#include <DHT.h>                  // Lib. DHT22 - Sensor de umidade
#include <LiquidCrystal_I2C.h>    // Lib. display LCD
#include <WiFi.h>                 // Lib. Wi-Fi     
#include <PubSubClient.h>         // Lib. MQTT
#include <ArduinoJson.h>          // Lib. JSON

// Wi-Fi
const char* ssid = "Wokwi-GUEST"; // Nome da rede Wi-Fi no Wokwi
const char* password = "";        // Senha (não tem senha)

// MQTT
const char* mqtt_broker = "broker.hivemq.com";        // Broker MQTT
const int mqtt_port = 1883;                           // Porta padrão MQTT
const char* mqtt_client_id = "fe-00225-esp32-c-v4";   // ID cliente MQTT
const char* mqtt_topic_publish = "fe/field-3/plot-1/computer-7/data";

// Pinos e limiares
const int computerId = 7;         // ID do computador de borda
const int potPhosphorusPin = 34;  // Potenciômetro (P)
const int potPotassiumPin = 35;   // Potenciômetro (K)
const int doPin = 13;             // LDR (pH)
const int aoPin = 36;             // LDR (pH)
const int dhtPin = 18;            // DHT (umidade)
const int relayPin = 17;          // Comando da bomba

// Limiares
const int humThreshold = 50;          // Umidade
const float phLowThreshold = 6.0;     // pH mínimo
const float phHighThreshold = 7.5;    // pH máximo

// Valores para mapeamento de escalas de pH
const int ldrMinVal = 8;          // Valor mínimo de leitura no sensor
const int ldrMaxVal = 1016;       // Valor máximo de leitura no sensor
const int phSimMinInt = 40;       // Valor mínimo considerado -> 4.0 * 10 para manter precisão
const int phSimMaxInt = 90;       // Valor máximo considerado -> 9.0 * 10 para manter precisão

// Limiares de normalidade para fósforo e potássio
const int phosphorusThreshold = 2000;
const int potassiumThreshold = 1800;

// Objetos de rede
WiFiClient espClient;                 // Cliente Wi-Fi
PubSubClient mqttClient(espClient);   // Cliente MQTT

// Conexão
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando-se a ");
  Serial.println(ssid);
 
  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
 
  Serial.println("");
  Serial.println("WiFi conectado!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

// Conexão MQTT 
void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Tentando conexão MQTT...");
 
    // Tenta conectar
    if (mqttClient.connect(mqtt_client_id)) {
      Serial.println("conectado!");
    } else {
      Serial.print("falhou, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" tentando novamente em 5 segundos");
      delay(5000); // Espera 5s para tentar novamente
    }
  }
}
 
// Define LCD
LiquidCrystal_I2C lcd(0x27, 20, 4); // 20 colunas, 4 linhas

DHT dht22(dhtPin, DHT22);

// Caracteres personalizados
byte grau[8] = {
  0b00000, 0b00110, 0b01001, 0b01001, 0b00110, 0b00000, 0b00000, 0b00000
};

byte setaCima[8] = {
  0b00000, 0b00100, 0b01110, 0b10101, 0b00100, 0b00100, 0b00000, 0b00000
};

byte setaBaixo[8] = {
  0b00000, 0b00100, 0b00100, 0b10101, 0b01110, 0b00100, 0b00000, 0b00000
};

void setup() {

  // Log header
  Serial.begin(115200);
  Serial.println("TiãoTech - Log de sensores");
  Serial.print("Computador: ");
  Serial.println(computerId);

  // Pinagem componentes
  pinMode(doPin, INPUT);
  pinMode(aoPin, INPUT);
  pinMode(relayPin, OUTPUT);

  // Conectar Wi-Fi
  setup_wifi(); // chamando Wi-Fi Setup

  // Configurar cliente MQTT
  mqttClient.setServer(mqtt_broker, mqtt_port);

  // Inicializa DHT22
  dht22.begin();

  // Inicializa LCD
  lcd.init();
  lcd.backlight();
  lcd.print("Iniciando...");

  // Mapeia caracteres especiais
  lcd.createChar(0, grau);       // Índice 0 para o símbolo de grau
  lcd.createChar(1, setaCima);   // Índice 1 para a seta para cima
  lcd.createChar(2, setaBaixo);  // Índice 2 para a seta para baixo

  Serial.print("Limite de umidade: ");
  Serial.println(humThreshold);
  Serial.println("time,temperatura,valor_umidade,nivel_umidade,bomba,fosforo,potassio,valor_ph,nivel_ph");

  delay(2000);
  lcd.clear();
}

void loop() {

  // Garante que o cliente MQTT está conectado
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop(); // Mantém a conexão MQTT e processa mensagens

  // Leitura P e K
  int phosphorusRawValue = analogRead(potPhosphorusPin);
  int potassiumRawValue = analogRead(potPotassiumPin);

  //Leitura pH
  int ldrRawValue = analogRead(aoPin);
  float humi = dht22.readHumidity();
  float temp = dht22.readTemperature();

  //Mapeamento de escalas
  long mappedPH_int = map(ldrRawValue, ldrMinVal, ldrMaxVal, phSimMinInt, phSimMaxInt);
  float simulatedPH = (float)mappedPH_int / 10.0;
  
  if (simulatedPH < (float)phSimMinInt / 10.0) simulatedPH = (float)phSimMinInt / 10.0;
  if (simulatedPH > (float)phSimMaxInt / 10.0) simulatedPH = (float)phSimMaxInt / 10.0;


  String humiStatus;
  String pumpStatus;
  if (humi < humThreshold) {
    digitalWrite(relayPin, HIGH);
    humiStatus = "baixa";
    pumpStatus = "ligada";
  } else {
    digitalWrite(relayPin, LOW);
    humiStatus = "OK";
    pumpStatus = "desligada";
  }

  // Lógica para fósforo e potássio
  String phosphorusStatus = (phosphorusRawValue >= phosphorusThreshold) ? "OK" : "Baixo";
  String potassiumStatus = (potassiumRawValue >= potassiumThreshold) ? "OK" : "Baixo";
  
  // Lógica pH
  String phLevelStatus;
  byte phIcon = 0;
  if (simulatedPH < phLowThreshold) {
    phLevelStatus = "acid";
    phIcon = 2;                                 // Seta para baixo
  } else if (simulatedPH > phLowThreshold) {
    phLevelStatus = "alca";
    phIcon = 1;                                 // Seta para cima
  } else {
    phLevelStatus = "norm";
    phIcon = 0;                                 // Grau
  }

  // Saída para o serial monitor (mantida apenas para logs)
  Serial.print(millis()); Serial.print(",");
  Serial.print(temp); Serial.print(",");
  Serial.print(humi); Serial.print(",");
  Serial.print(humiStatus); Serial.print(",");
  Serial.print(pumpStatus); Serial.print(",");
  Serial.print(phosphorusStatus); Serial.print(",");
  Serial.print(potassiumStatus); Serial.print(",");
  Serial.print(simulatedPH, 1); Serial.print(",");
  Serial.println(phLevelStatus);

  // Formatação do payload JSON
  const int CAPACITY = JSON_OBJECT_SIZE(9) + 200; // 9 campos + espaço para strings (~ 200 bytes)
  StaticJsonDocument<CAPACITY> doc;

  doc["time"] = millis();
  doc["temperatura"] = temp;
  doc["valor_umidade"] = humi;
  doc["nivel_umidade"] = humiStatus;
  doc["bomba"] = pumpStatus;
  doc["fosforo"] = phosphorusStatus;
  doc["potassio"] = potassiumStatus;
  doc["valor_ph"] = simulatedPH;
  doc["nivel_ph"] = phLevelStatus;

  // Serializar JSON para string (char array)
  char jsonBuffer[256]; // Buffer para string JSON
  serializeJson(doc, jsonBuffer, sizeof(jsonBuffer));

  // Serial.print("Payload JSON: ");
  // Serial.println(jsonBuffer);

  // Enviar dados via MQTT
  if (mqttClient.publish(mqtt_topic_publish, jsonBuffer)) {
    Serial.println("Registro enviado com sucesso!");
  } else {
    Serial.println("Falha MQTT.");
  }

  // Exibição LCD
  lcd.clear(); // Limpa o display

  // Linha 0 - Umidade e bomba
  lcd.setCursor(0, 0);
  lcd.print("Um: ");
  lcd.print(humi, 1);
  lcd.print("%  Pmp: ");
  lcd.print(pumpStatus.substring(0,3));         // "lig" ou "des"

  // Linha 1 - Fósforo e potássio
  lcd.setCursor(0, 1);
  lcd.print("P: ");
  lcd.print(phosphorusStatus);                  // "OK" ou "Baixo"
  lcd.print(" K: ");
  lcd.print(potassiumStatus);                   // "OK" ou "Baixo"

  // Linha 2 - pH
  lcd.setCursor(0, 2);
  lcd.print("pH: ");
  lcd.print(simulatedPH, 1);
  lcd.print(" ");
  lcd.write(phIcon);
  lcd.print(" (");
  lcd.print(phLevelStatus);                     // "acid", "alca" ou "norm"
  lcd.print(")");

  // Linha 3 - Temperatura
  lcd.setCursor(0, 3);
  lcd.print("Temp: ");
  lcd.print(temp, 1);
  lcd.write(0);                                 // Símbolo de grau
  lcd.print("C");

  delay(1000);                                  // intervalo entre atualizações
}