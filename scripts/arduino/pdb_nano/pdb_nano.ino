
//Preprocessor
#define pinSBC 9
#define pinMC 10
#define pinCheck A0
#define pinToggle 12
#define pinBuzzer 8
#define batt_zener 8.61 //zener voltage
#define R1 51.3 //Measurement of voltage divider in kOhm
#define R2 82.4 //Measurement of voltage divider in kOhm

//User Tunable Parameters
const float low_voltage_on_thresh = 9.18;
const float low_voltage_off_thresh = 9.16;
const int wait_time = 10000;
const unsigned long state_2_timeout = 10000;
const int nag_for_ack_time = 1000;

//overvoltage trips
const float danger_inp_voltage = 14.7;
const float max_inp_voltage = 15.0;

//Global Variables
int state = 0;
bool sd_ack = false;
int buzzer_state = 0;

//Variable for serial input
String compin;
String moving;
String ack;
String msg;
String command;
String serial_output;
String err;

//Pin States
int mc_relay_pin;
int sbc_relay_pin;
int buzz;

//Variables for Timer
unsigned long start_time; // the time the delay started
unsigned long end_time;
static unsigned long beep_start = 0;
static unsigned long beep_end;
int beep_counter = 0;
int elapsed;
unsigned long last_nag = 0;


//Beep patterns
//bp is beep pattern
//bs is beep state
int bp1[1] = {1000};
int bs1[1] = {HIGH};
int bp2[2] = {50, 1950};
int bs2[2] = {HIGH, LOW};
int bp3[4] = {30, 30, 30, 910};
int bs3[4] = {HIGH, LOW, HIGH, LOW};
int bp4[6] = {30, 30, 30, 30, 30, 850};
int bs4[6] = {HIGH, LOW, HIGH, LOW, HIGH, LOW};

//bool delayRunning = false; // true if still waiting for delay to finish

//Variable for Battery Voltage Check
double batt_volt;



//functions

void parse_command(String com){
  if(com.equals("ack")){
    sd_ack = true;
  }
  else if(com.equals("volts")){
    serial_output = String(batt_volt);
  }
  else if(com.equals("buzzer_state")){
    serial_output = String(buzzer_state);
  }
  else if(com.equals("state")){
    serial_output = String(state);
  }
  else if(com.equals("cancel")){
    state = 1;
  }
  else if(com.equals("ping")){
    digitalWrite(pinBuzzer, HIGH);
    delay(15);
    digitalWrite(pinBuzzer, LOW);
  }
  else{
    serial_output = "INVALID COMMAND";
  }
}

void get_serial_buffer() {
  while(Serial.available()){
    char c = Serial.read();
    if(c == '\n'){
//      Serial.println(command);
      parse_command(command);
      command = "";
    }
    else{
      command += c;
    }
  }
  if(serial_output.equals("") == false){
    Serial.println(serial_output);
    serial_output = "";
  }
}

double get_batt_volt() {
  return ((analogRead(A0))*5)*((R1 + R2)/(R2*1023)) + batt_zener;
}

bool low_batt() {
  return batt_volt < low_voltage_off_thresh;
}

int toggle_switch() {
  return digitalRead(pinToggle);
}

void change_sbc_relay(int sbc_relay_pin) {
  digitalWrite(pinSBC, sbc_relay_pin);
  digitalWrite(13, sbc_relay_pin);
}

void change_mc_relay(int mc_relay_pin) {
  digitalWrite(pinMC, mc_relay_pin);
}

void ring_buzzer(){
//  digitalWrite(pinBuzzer, buzz);
//  Serial.println(buzz_pattern);
  switch(buzzer_state){
    case 0:
      digitalWrite(pinBuzzer, LOW);
      beep_counter = 0;
      break;
      
    case 1:
      beep_counter = beep_counter % sizeof(bp2) == 0 ? 0 : beep_counter;
      beep_end = millis();
      digitalWrite(pinBuzzer,bs1[beep_counter]);
      elapsed = beep_end - beep_start;
      if(elapsed >= bp1[beep_counter]){
        beep_counter++;
        beep_counter = beep_counter % sizeof(bp1) == 0 ? 0 : beep_counter;
        digitalWrite(pinBuzzer,bs1[beep_counter]);
        beep_start = millis();
      }
      break;
      
    case 2:
      beep_counter = beep_counter % sizeof(bp2) == 0 ? 0 : beep_counter;
      beep_end = millis();
      digitalWrite(pinBuzzer,bs2[beep_counter]);
      elapsed = beep_end - beep_start;
      if(elapsed >= bp2[beep_counter]){
        beep_counter++;
        beep_counter = beep_counter % sizeof(bp2) == 0 ? 0 : beep_counter;
        digitalWrite(pinBuzzer,bs2[beep_counter]);
        beep_start = millis();
      }
      break;
      
    case 3:
      beep_counter = beep_counter % sizeof(bp2) == 0 ? 0 : beep_counter;
      beep_end = millis();
      digitalWrite(pinBuzzer,bs3[beep_counter]);
      elapsed = beep_end - beep_start;
      if(elapsed >= bp3[beep_counter]){
        beep_counter++;
        beep_counter = beep_counter % sizeof(bp3) == 0 ? 0 : beep_counter;
        digitalWrite(pinBuzzer,bs3[beep_counter]);
        beep_start = millis();
      }
      break;
      
    case 4:
      beep_end = millis();
      digitalWrite(pinBuzzer,bs4[beep_counter]);
      elapsed = beep_end - beep_start;
      if(elapsed >= bp4[beep_counter]){
        beep_counter++;
        beep_counter = beep_counter % sizeof(bp4) == 0 ? 0 : beep_counter;
        digitalWrite(pinBuzzer,bs4[beep_counter]);
        beep_start = millis();
      }
      break;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("DSO Counter-Terrorist Bot PDB v1.3a");
  pinMode(pinSBC, OUTPUT); 
  pinMode(pinMC, OUTPUT); 
  pinMode(pinCheck, INPUT); 
  pinMode(pinToggle, INPUT);
}

void loop(){
//  Check battery voltage
  batt_volt = get_batt_volt();
  get_serial_buffer();
  ring_buzzer(); //check the current state of the buzzer and ring accordingly
//  Serial.println(state);
  switch (state) {
  case 0:
    //OFF STATE

      sbc_relay_pin = LOW;
      change_sbc_relay(sbc_relay_pin);  //digitalWrite(pinSBC, LOW);

      mc_relay_pin = LOW;
      change_mc_relay(mc_relay_pin); //digitalWrite(pinMC, LOW);

      if (batt_volt <= low_voltage_on_thresh) {
        buzzer_state = 1;
        state = 0;
      }
      else if (batt_volt > low_voltage_on_thresh + 0.02){
        buzzer_state = 0;
        state = 0;
      }
      if (batt_volt >= low_voltage_on_thresh + 0.02 && batt_volt <= danger_inp_voltage && toggle_switch()==HIGH) {
        //to ON STATE
        buzzer_state = 0;
        state = 1;
      }
    break;
  
  
  case 1:
    //ON STATE
      if(batt_volt >= max_inp_voltage){
        digitalWrite(pinMC, LOW);
        serial_output += "BUS_OVERVOLTAGE_TRIP";
        err = "BUS_OVERVOLTAGE_TRIP";
        state = 2;
      }
      
      sd_ack = false;
      
      sbc_relay_pin = HIGH;
      change_sbc_relay(sbc_relay_pin); //digitalWrite(pinSBC, HIGH);

      mc_relay_pin = HIGH;
      change_mc_relay(mc_relay_pin); //digitalWrite(pinMC, HIGH);

      if (batt_volt < low_voltage_off_thresh) {
        buzzer_state = 1;
      }
      else if (batt_volt > low_voltage_off_thresh + 0.02){
        buzzer_state = 0;
      }

    //check for change in state
    
      if(low_batt()) {
        //to Shutting Down STATE
        state = 2;
        start_time = millis();
        serial_output += "BUS_LOW_VOLTAGE_TRIP";
        err = "BUS_LOW_VOLTAGE_TRIP";
      }
      else if(toggle_switch()==LOW) {
        //to Shutting Down STATE
        start_time = millis();
        state = 2;
      }
    break;

    
  case 2:
    //COMMUNICATE WITH SBC STATE
      sbc_relay_pin = HIGH;
      change_sbc_relay(sbc_relay_pin); //digitalWrite(pinSBC, HIGH);
  
      mc_relay_pin = LOW;
      change_mc_relay(mc_relay_pin); //digitalWrite(pinMC, LOW);

      if (low_batt()) {
        buzzer_state = 4;
      }
      else{
        buzzer_state = 3;
      }
      
      if(millis() - last_nag >= nag_for_ack_time){
        Serial.println(err);
        last_nag = millis();
      }

      end_time = millis();
      if(sd_ack == true) {
//        Serial.println("sd_ack = true");
//        to TIMEOUT STATE
        state = 3;
        start_time = millis();
        sd_ack = false;
      }
      else if(end_time - start_time >= state_2_timeout){
        state = 0;
        start_time = millis();
      }
      else{
        Serial.println("BATT VOLTS " + String(batt_volt));
      }
//      char acknowledge = Serial.read();
//      ack = ack + acknowledge;
      
//      if(ack == "K/n") {
//        //to TIMEOUT STATE
//        state = 3;
//      }   

    break;
  
  
  case 3:
    //TIMEOUT STATE
    if (low_batt()) {
      buzzer_state = 2;
    }
    else{
      buzzer_state = 0;
    }

    end_time = millis();
    if(end_time - start_time >= wait_time){
      state = 0;
    }
    
    break;
  }
}
