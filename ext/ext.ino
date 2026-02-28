/*
 * Braille 8 points → Relais / Diodes (WPM436)
 *
 * CÂBLAGE : Arduino  →  Module relais
 *   Pin 2  →  IN1   (jaune)
 *   Pin 3  →  IN2   (orange)
 *   Pin 4  →  IN3   (rouge)
 *   Pin 5  →  IN4   (marron)
 *   Pin 6  →  IN5   (blanc)
 *   Pin 7  →  IN6   (violet)
 *   Pin 8  →  IN7   (vert)
 *   Pin 9  →  IN8   (bleu)
 * Si tes fils sont sur d'autres broches Arduino, modifie PIN_BRAILLE[] ci-dessous.
 */

// Broches Arduino connectées à IN1..IN8. NE PAS utiliser 0 et 1 (RX/TX = Série) !
const int PIN_BRAILLE[] = { 2, 3, 4, 5, 6, 7, 8, 9 };
const int N_PINS = 8;

// true = relais ON avec LOW (actif bas) | false = relais ON avec HIGH
const bool RELAY_ACTIF_LOW = false;

// Table Braille : a-z (indice 0..25), même convention que francais_vers_braille.py
// Chaque octet : bit0=pin0, bit1=pin1, ... bit7=pin7
const uint8_t BRAILLE_LETTRES[] PROGMEM = {
  1,  3, 17, 25,  9, 19, 27, 11, 18, 26,   // a-j
  5,  7, 21, 29, 13, 31, 23, 14, 30, 37,   // k-t
 39, 58, 45, 61, 53                        // u-z
};

#define LED_BUILTIN 13  // LED L sur la carte Arduino

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  for (int i = 0; i < N_PINS; i++) {
    pinMode(PIN_BRAILLE[i], OUTPUT);
    digitalWrite(PIN_BRAILLE[i], RELAY_ACTIF_LOW ? HIGH : LOW);
  }
  // Test : LED L (pin 13) clignote en meme temps que chaque relais
  Serial.println("Test: LED L sur Arduino clignote 8 fois (1 fois par relais)");
  Serial.println("Si la LED L clignote mais pas les LED du module -> verifie les broches 2 a 9");
  for (int i = 0; i < N_PINS; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    for (int j = 0; j < N_PINS; j++)
      digitalWrite(PIN_BRAILLE[j], (j == i) ? (RELAY_ACTIF_LOW ? LOW : HIGH) : (RELAY_ACTIF_LOW ? HIGH : LOW));
    Serial.print("  Relay ");
    Serial.print(i + 1);
    Serial.print(" (broche ");
    Serial.print(PIN_BRAILLE[i]);
    Serial.println(")");
    delay(600);
    digitalWrite(LED_BUILTIN, LOW);
    for (int j = 0; j < N_PINS; j++)
      digitalWrite(PIN_BRAILLE[j], RELAY_ACTIF_LOW ? HIGH : LOW);
    delay(200);
  }
  Serial.println("Braille 8 pins - Envoyez une lettre (a-z, espace, ou ponctuation)");
}

// Applique le motif Braille sur les 8 sorties
void setBraille(uint8_t pattern) {
  for (int i = 0; i < N_PINS; i++) {
    bool pointLeve = (pattern & (1 << i)) != 0;
    int niveau = RELAY_ACTIF_LOW ? (pointLeve ? LOW : HIGH) : (pointLeve ? HIGH : LOW);
    digitalWrite(PIN_BRAILLE[i], niveau);
  }
}

// Retourne le motif Braille (8 bits) pour un caractère, ou 0 si inconnu
uint8_t charVersBraille(char c) {
  if (c == ' ') return 0;
  if (c >= 'a' && c <= 'z') return pgm_read_byte(&BRAILLE_LETTRES[c - 'a']);
  if (c >= 'A' && c <= 'Z') return pgm_read_byte(&BRAILLE_LETTRES[c - 'A']);

  // Ponctuation (bits: pin0..pin7 = bit0..bit7, comme francais_vers_braille.py)
  switch (c) {
    case '.': return 50;   // point (2,5,6)
    case ',': return 34;   // virgule (2,6)
    case '?': return 38;   // ?
    case '!': return 14;   // !
    case '\'': return 4;   // apostrophe (3)
    case ':': return 10;   // deux-points (2,5)
    case ';': return 14;   // point-virgule (2,3,5)
    case '-': return 36;   // tiret (3,6)
    case '(': return 55;   // (
    case ')': return 62;   // )
    case '"': return 38;   // guillemet
    case '/': return 76;   // slash
    default:  return 0;
  }
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    // Ne pas appliquer le retour à la ligne / entrée : sinon on éteint tout juste après la lettre
    if (c == '\n' || c == '\r') return;
    uint8_t pattern = charVersBraille(c);
    setBraille(pattern);
    Serial.print("Caractere: ");
    if (c == ' ') Serial.print("[espace]");
    else Serial.print(c);
    Serial.print(" -> motif ");
    Serial.println(pattern, BIN);
    delay(1000);  // 1 seconde entre chaque caractère
  }
}
