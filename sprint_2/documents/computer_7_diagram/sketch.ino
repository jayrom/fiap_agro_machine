#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Definições de pinos e limiares (inalteradas ou ajustadas)
const int computerId = 7;

// --- NOVOS PINOS PARA POTENCIÔMETROS ---
const int potFosforoPin = 34; // Conectado ao potenciômetro de Fósforo
const int potPotassioPin = 35; // Conectado ao potenciômetro de Potássio

const int doPin = 13;
const int aoPin = 36; // Pino para o sensor LDR (que estamos usando para simular pH)
const int dhtPin = 18; // Pino do sensor DHT
const int relayPin = 17;

const int humThreshold = 50;
const float PH_LOW_THRESHOLD = 6.0;
const float PH_HIGH_THRESHOLD = 7.5;

// Valores MIN e MAX do LDR para o mapeamento
const int LDR_MIN_VAL = 8;
const int LDR_MAX_VAL = 1016;

// Limites do pH real que queremos simular (multiplicados por 10 para usar map())
const int PH_SIM_MIN_INT = 40; // 4.0 * 10
const int PH_SIM_MAX_INT = 90; // 9.0 * 10

// Limiares para Fósforo e Potássio (valores de 0 a 4095 do analogRead)
// Se a leitura do potenciômetro for ABAIXO deste valor, será considerado "Baixo".
// Se for IGUAL ou ACIMA, será considerado "OK".
const int FOSFORO_THRESHOLD = 2000; // Exemplo: Abaixo de 2000 é "Baixo"
const int POTASSIO_THRESHOLD = 1800; // Exemplo: Abaixo de 1800 é "Baixo"


// O displayInterval não é mais necessário para alternar telas
const unsigned long displayInterval = 5000; // Mantido, mas não usado para alternância

// --- INICIALIZAÇÃO DO LCD 20x4 ---
LiquidCrystal_I2C lcd(0x27, 20, 4); // AGORA É 20 COLUNAS, 4 LINHAS
DHT dht22(dhtPin, DHT22);

// --- DEFINIÇÃO DOS CARACTERES PERSONALIZADOS (inalteradas) ---
byte grau[8] = {
  0b00000,
  0b00110,
  0b01001,
  0b01001,
  0b00110,
  0b00000,
  0b00000,
  0b00000
};

byte setaCima[8] = {
  0b00000,
  0b00100,
  0b01110,
  0b10101,
  0b00100,
  0b00100,
  0b00000,
  0b00000
};

byte setaBaixo[8] = {
  0b00000,
  0b00100,
  0b00100,
  0b10101,
  0b01110,
  0b00100,
  0b00000,
  0b00000
};

void setup() {
  Serial.begin(115200);
  Serial.println("TiãoTech - Log de sensores");
  Serial.print("Computador: ");
  Serial.println(computerId);

  // Não precisamos mais de pinMode para os pinos dos potenciômetros como INPUT
  // pois analogRead já os configura implicitamente para a leitura analógica.
  pinMode(doPin, INPUT);
  pinMode(aoPin, INPUT);
  pinMode(relayPin, OUTPUT);

  dht22.begin();

  lcd.init();
  lcd.backlight();
  lcd.print("Iniciando...");

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
  // Leitura dos potenciômetros (analógica)
  int fosforoRawValue = analogRead(potFosforoPin);
  int potassioRawValue = analogRead(potPotassioPin);

  int ldrRawValue = analogRead(aoPin);
  float humi = dht22.readHumidity();
  float temp = dht22.readTemperature();

  long mappedPH_int = map(ldrRawValue, LDR_MIN_VAL, LDR_MAX_VAL, PH_SIM_MIN_INT, PH_SIM_MAX_INT);
  float simulatedPH = (float)mappedPH_int / 10.0;
  
  if (simulatedPH < (float)PH_SIM_MIN_INT / 10.0) simulatedPH = (float)PH_SIM_MIN_INT / 10.0;
  if (simulatedPH > (float)PH_SIM_MAX_INT / 10.0) simulatedPH = (float)PH_SIM_MAX_INT / 10.0;

  Serial.print(millis()); Serial.print(",");
  Serial.print(temp); Serial.print(",");
  Serial.print(humi); Serial.print(",");

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
  Serial.print(humiStatus); Serial.print(",");
  Serial.print(pumpStatus); Serial.print(",");

  // --- Lógica para Fósforo e Potássio com Potenciômetros ---
  String fosforoStatus = (fosforoRawValue >= FOSFORO_THRESHOLD) ? "OK" : "Baixo";
  String potassioStatus = (potassioRawValue >= POTASSIO_THRESHOLD) ? "OK" : "Baixo";
  
  String phLevelStatus;
  byte phIcon = 0;
  if (simulatedPH < PH_LOW_THRESHOLD) {
    phLevelStatus = "acido";
    phIcon = 2; // Seta para baixo
  } else if (simulatedPH > PH_HIGH_THRESHOLD) {
    phLevelStatus = "alca";
    phIcon = 1; // Seta para cima
  } else {
    phLevelStatus = "norm";
    // phIcon = 0; // Se não quiser ícone para normal, mantenha 0.
  }
  Serial.print(fosforoStatus); Serial.print(",");
  Serial.print(potassioStatus); Serial.print(",");
  Serial.print(simulatedPH, 1); Serial.print(",");
  Serial.println(phLevelStatus);

  // --- Exibição no LCD 20x4 (layout fixo) ---
  lcd.clear(); // Limpa o display para reescrever com os valores atualizados

  // Linha 0: Umidade e Bomba
  lcd.setCursor(0, 0);
  lcd.print("Um: ");
  lcd.print(humi, 1); // Uma casa decimal
  lcd.print("% |Pmp: "); // Usando o pipe literal
  lcd.print(pumpStatus.substring(0,3)); // "lig" ou "des"

  // Linha 1: Fósforo e Potássio
  lcd.setCursor(0, 1);
  lcd.print("P: ");
  lcd.print(fosforoStatus); // "OK" ou "Baixo"
  lcd.print(" K: ");
  lcd.print(potassioStatus); // "OK" ou "Baixo"

  // Linha 2: pH
  lcd.setCursor(0, 2);
  lcd.print("pH: ");
  lcd.print(simulatedPH, 1); // pH com uma casa decimal
  lcd.print(" ");
  lcd.write(phIcon); // Ícone de seta (cima/baixo) ou grau se for "Normal"
  lcd.print(" (");
  lcd.print(phLevelStatus); // "acido", "alca" ou "norm"
  lcd.print(")");

  // Linha 3: Temperatura
  lcd.setCursor(0, 3);
  lcd.print("Temp: ");
  lcd.print(temp, 1); // Temperatura com uma casa decimal
  lcd.write(0); // Símbolo de grau
  lcd.print("C");

  delay(1000); // Aguarda 1 segundo antes da próxima atualização
}