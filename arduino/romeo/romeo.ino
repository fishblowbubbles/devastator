#define m1_dir_pin 4
#define m1_pwm_pin 5
#define m2_pwm_pin 6
#define m2_dir_pin 7

//TODO
/*
 * make ISR write directly to output registers
 * possibly make the sampling rate higher than 100Hz?
 * implement serial commands to tune params
 */

const float version_number = 1.2;

//motor parameters
const float motor_cut_in_1 = 0.105; // experimentally determined
const float motor_cut_in_2 = 0.105; // experimentally determined
float motor_gamma = 1.47; //tunes the linearity of the motor's speed vs voltage
float overshoot = 4.0; // tune the amount of overshoot/kick, useful to overcome stiction at low power setting
float overshoot_length = 0.068; // in seconds. tunes the time taken to reach 5% of steady state value
float supply_volt_compensation = 3.34; //compensation fudge factor for voltage loss
float supply_voltage = 12.6; // use "supply_voltage" serial command to change this over serial
float motor1_voltage = 5.8; // used to trim the motors
float motor2_voltage = 5.55; // used to trim the motors
float max_pwm_scale_1 = motor1_voltage/(supply_voltage-supply_volt_compensation);
float max_pwm_scale_2 = motor2_voltage/(supply_voltage-supply_volt_compensation);
int verbosity = 0;

// sampling timer params
// timer0 affects analogWrite on pins 5, 6 so we shouldnt use those
// timer1 affects analogWrite on pins 9, 10 which is unused so we can use that
// timer2 affects analogWrite on pins 3, 11
// prescaler = 256
const uint16_t sampling_freq = 200;
const uint16_t t1_load = 0;
const uint16_t t1_comp = uint16_t((16000000/(256*sampling_freq))-1);

// motor kick filter variables
const int filter_len = 2;
int filter_pos = 0; //to be incremented then modulo (filter_len)
float m1_v[filter_len] = {0.0, 0.0}; //type 2 filter circular delay line
float m2_v[filter_len] = {0.0, 0.0}; //type 2 filter circular delay line

//calculate motor kick filter coeffs
float filter_s = 1.0 - exp(-3/(overshoot_length*float(sampling_freq)));
float num[filter_len] = {1.0 + overshoot, -(1.0 + overshoot-filter_s)}; //numerator of filter
float den[filter_len] = {1.0, filter_s -1.0}; //denominator of filter

//watchdog timer to disable motors if commands not received
int no_command_timeout = 500; //milliseconds, set to zero for no watchdog timer
long last_command = 0;

// Globals
String command;
String output;
bool enable = false;
float motor1_speed = 0;
float motor2_speed = 0;

void set_motor(int motor, float m_speed){
  if(enable){
    m_speed = abs(m_speed) < 0.0008 ? 0 : m_speed;
    m_speed = m_speed > 1 ? 1 : m_speed;
    m_speed = m_speed < -1? -1 : m_speed;
//    int s;
    float s;
//    if(m_speed == 0){
//      s = 0;
//    }
//    else{
////      s = int(pow(abs(m_speed), motor_gamma)*(max_pwm_scale - motor_cut_in) + motor_cut_in) *255);
//      s = (pow(abs(m_speed), motor_gamma)*(max_pwm_scale - motor_cut_in) + motor_cut_in);
//    }
    if(motor == 1){
      s = m_speed == 0 ? 0 : (pow(abs(m_speed), motor_gamma)*(max_pwm_scale_1 - motor_cut_in_1) + motor_cut_in_1);
      motor1_speed = m_speed > 0 ? s : -s;
    }
    else if(motor == 2){
      s = m_speed == 0 ? 0 : (pow(abs(m_speed), motor_gamma)*(max_pwm_scale_2 - motor_cut_in_2) + motor_cut_in_2);
      motor2_speed = m_speed > 0 ? s : -s;
    }
  }
  else{
    output = "OUTPUT DISABLED!";
  }
}

void test(){
  for(float s = 0; s<1; s+=0.001){
    set_motor(1, s);
    set_motor(2, s);
    delay(10);
  }
  set_motor(1, 0);
  set_motor(2, 0);
}

void lol(){
  set_motor(1,1);
  set_motor(2,1);
  delay(50);
  set_motor(1,-1);
  set_motor(2,-0.5);
  delay(60);
  set_motor(1,0);
  set_motor(2,0);
  delay(100);
  set_motor(1,-1);
  set_motor(2,-1);
  delay(50);
  set_motor(1,1);
  set_motor(2,1);
  delay(60);
  set_motor(1,0);
  set_motor(2,0);
}

void parse_command(String com){
  float s;
  if(com.startsWith("1")){
    s = com.substring(com.indexOf(" ") + 1).toFloat();
    set_motor(1, s);
  }
  else if(com.startsWith("2")){
    s = com.substring(com.indexOf(" ") + 1).toFloat();
    set_motor(2, s);
  }
  else if(com.startsWith("supply_voltage")){
    float v = com.substring(com.indexOf(" ") + 1).toFloat();
    if(v == 0){
      output = String(supply_voltage);
    }
    else{
      supply_voltage = v;
      max_pwm_scale_1 = motor1_voltage/(supply_voltage-supply_volt_compensation);
      max_pwm_scale_1 = max_pwm_scale_1 > 1 ? 1 : max_pwm_scale_1;
      max_pwm_scale_2 = motor2_voltage/(supply_voltage-supply_volt_compensation);
      max_pwm_scale_2 = max_pwm_scale_2 > 1 ? 1 : max_pwm_scale_2;
    }
  }
  else if(com.startsWith("motor1_voltage")){
    float v = com.substring(com.indexOf(" ") + 1).toFloat();
    if(v == 0){
      output = String(motor1_voltage);
    }
    else{
      motor1_voltage = v;
      max_pwm_scale_1 = motor1_voltage/(supply_voltage-supply_volt_compensation);
      max_pwm_scale_1 = max_pwm_scale_1 > 1 ? 1 : max_pwm_scale_1;
    }
  }
  else if(com.startsWith("motor2_voltage")){
    float v = com.substring(com.indexOf(" ") + 1).toFloat();
    if(v == 0){
      output = String(motor2_voltage);
    }
    else{
      motor2_voltage = v;
      max_pwm_scale_2 = motor2_voltage/(supply_voltage-supply_volt_compensation);
      max_pwm_scale_2 = max_pwm_scale_2 > 1 ? 1 : max_pwm_scale_2;
    }
  }
  else if(com.startsWith("gamma")){
    float g = com.substring(com.indexOf(" ") + 1).toFloat();
    if(g == 0){
      motor_gamma = 1.2;
    }
    else{
      motor_gamma = g;
    }
  }
  else if(com.startsWith("overshoot")){
    overshoot = com.substring(com.indexOf(" ") + 1).toFloat();
    output = "overshoot = " + String(overshoot);
//    filter_s = 1.0 - exp(-3/(overshoot_length*float(sampling_freq)));
    num[0] = 1.0 + overshoot;
    num[1] = -(1.0 + overshoot-filter_s);//numerator of filter
    den[0] = 1.0;
    den[1] = filter_s -1.0; //denominator of filter
  }
  else if(com.startsWith("overshoot_length")){
    overshoot_length = com.substring(com.indexOf(" ") + 1).toFloat();
    output = "overshoot_length = " + String(overshoot_length);
    overshoot_length = overshoot_length == 0 ? 0.00001 : overshoot_length;
    filter_s = 1.0 - exp(-3/(overshoot_length*float(sampling_freq)));
    num[0] = 1.0 + overshoot;
    num[1] = -(1.0 + overshoot-filter_s);//numerator of filter
    den[0] = 1.0;
    den[1] = filter_s -1.0; //denominator of filter
  }
  else if(com.startsWith("timeout")){
    no_command_timeout = com.substring(com.indexOf(" ") + 1).toInt();
    output = "timeout = " + String(no_command_timeout);
  }
  else if(com.equals("test")){
    test();
  }
  else if(com.startsWith("test")){
    int asdf = com.substring(com.indexOf(" ") + 1).toInt();
    for(int i=0; i<asdf; i++){
      test();
    }
  }
  else if(com.equals("enable")){
    enable = true;
    output += "output enabled";
  }
  else if(com.equals("disable")){
    if(enable == true){
      set_motor(1, 0);
      set_motor(2, 0);
      output = "output disabled";
      enable = false;
    }
    output = "output disabled";
  }
  else if(com.startsWith("verb")){
    verbosity = com.substring(com.indexOf(" ") + 1).toInt();
    if(verbosity != 1){
      verbosity = 0;
    }
    output += "verbosity set to " + String(verbosity);
  }
  else if(com.equals("lol")){
    lol();
  }
  else if(com.startsWith("lol")){
    int asdf = com.substring(com.indexOf(" ") + 1).toInt();
    for(int i=0; i<asdf; i++){
      lol();
    }
  }
  else if(com.equals("info")){
    output = "DSO Counter-Terrorist Bot Motor Controller v" + String(version_number);
  }
  else{
    output = "INVALID COMMAND";
  }
}

void setup(){
  Serial.begin(115200);
  pinMode(m1_dir_pin, OUTPUT);
  pinMode(m1_pwm_pin, OUTPUT);
  pinMode(m2_dir_pin, OUTPUT);
  pinMode(m2_pwm_pin, OUTPUT);

  Serial.println("DSO Counter-Terrorist Bot Motor Controller v" + String(version_number));

  float s = 0;
  enable = true;
  lol();
  enable = false;

  // reset Timer1 Control Register A
  TCCR1A = 0;

  // set CTC mode i.e. reset timer1 to 0 when compare is true
  TCCR1B &= ~(1 << WGM13);
  TCCR1B |= (1 << WGM12);
  
  //set Timer1 to prescaler of 256
  TCCR1B |= (1 << CS12);
  TCCR1B &= ~(1 << CS11);
  TCCR1B &= ~(1 << CS10);

  //reset timer1 and set compare value
  TCNT1 = t1_load;
  OCR1A = t1_comp;

  //enable timer1 compare interrupt
  TIMSK1 = (1 << OCIE1A);

  //enable global interrupts
  sei();
}

void loop(){
  while(Serial.available()){
    char c = Serial.read();
    if(c == '\n'){
      Serial.println(command);
      parse_command(command);
      if(output.equals("") == false){Serial.println(output);}
      command = "";
      output = "";
      last_command = millis();
    }
    else{
      command += c;
    }
  }
  if(millis() - last_command >= no_command_timeout && no_command_timeout != 0){
    motor1_speed = 0.0;
    motor2_speed = 0.0;
  }
}


// callback function for the interrupt at sample freq to set the update the PWM on the motors
ISR(TIMER1_COMPA_vect){
  //calculate the filter
  int prev_idx = (filter_pos + 1) % filter_len;
  m1_v[filter_pos] = den[0]*motor1_speed - den[1]*m1_v[prev_idx];
  m2_v[filter_pos] = den[0]*motor2_speed - den[1]*m2_v[prev_idx];
  float m1_filtered = num[0]*m1_v[filter_pos] + num[1]*m1_v[prev_idx];
  float m2_filtered = num[0]*m2_v[filter_pos] + num[1]*m2_v[prev_idx];
  m1_filtered = m1_filtered < -1 ? -1 : m1_filtered;
  m1_filtered = m1_filtered > 1 ? 1 : m1_filtered;
  m2_filtered = m2_filtered < -1 ? -1 : m2_filtered;
  m2_filtered = m2_filtered > 1 ? 1 : m2_filtered;
  digitalWrite(m1_dir_pin, m1_filtered > 0 ? HIGH : LOW);
  analogWrite(m1_pwm_pin, int(abs(m1_filtered * 255)));
  digitalWrite(m2_dir_pin, m2_filtered > 0 ? HIGH : LOW);
  analogWrite(m2_pwm_pin, int(abs(m2_filtered * 255)));

  if(verbosity == 1){
    Serial.println(String(m1_filtered*100) + " " + String(m2_filtered*100));
  }

  filter_pos = prev_idx;
}
