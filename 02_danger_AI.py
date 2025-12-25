import machine
import time
import sys
import select
from neopixel import NeoPixel
import ssd1306

# --- 1. Settings ---
NEOPIXEL_PIN = 21
BUZZER_PIN = 22
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
LOG_FILE = 'serial_log.txt'

OLED_WIDTH = 128
OLED_HEIGHT = 64
I2C_ADDR = 0x3C

# --- 2. Display Texts ---
OLED_TEXTS = {
    0: ["Status: IDLE", "", "Waiting for", "commands..."],
    1: ["!!! EMERGENCY !!!", "Class 1", "left arm", "Evacuate Now!"],
    2: ["-- WARNING --", "Class 2", "right arm", "Be Cautious."],
    3: ["Status: SAFE", "Class 3", "both arms down", "All Clear."],
    "boot": ["Booting...", "", "System Check...", ""],
    "error": ["SYSTEM ERROR", "", "Check log file", "for details."]
}

# --- 3. Hardware Init ---
np = NeoPixel(machine.Pin(NEOPIXEL_PIN), 1)
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))
buzzer.freq(440)
buzzer.duty_u16(0)

poller = select.poll()
poller.register(sys.stdin, select.POLLIN)

try:
    i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA_PIN), scl=machine.Pin(I2C_SCL_PIN), freq=400000)
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=I2C_ADDR)
except:
    oled = None

# --- 4. Helpers ---
def set_neopixel(color):
    np[0] = color
    np.write()

def display_text(text_list):
    if oled:
        oled.fill(0)
        for i, line in enumerate(text_list):
            oled.text(line, 0, i * 16)
        oled.show()

# --- 5. Main Loop Variables ---
current_state = 3
last_blink_time = 0
last_beep_time = 0
neopixel_on = False
buzzer_on = False
input_buffer = "" # To store incoming serial characters

display_text(OLED_TEXTS["boot"])
set_neopixel((0, 255, 0))
time.sleep(1)
display_text(OLED_TEXTS[3])

# --- 6. Execution Loop ---
while True:
    now = time.ticks_ms()

    # --- A. Robust Serial Handling ---
    # Check if there is data in the serial buffer
    if poller.poll(0): 
        char = sys.stdin.read(1) # Read one byte
        
        if char == '\n' or char == '\r': # Line completed
            command = input_buffer.strip()
            if command:
                log_message = f"Cmd: {command}"
                print(log_message) # Echo back for debugging
                
                # State Logic
                new_state = current_state
                if "Class 1" in command: new_state = 1
                elif "Class 2" in command: new_state = 2
                elif "Class 3" in command: new_state = 3
                
                if new_state != current_state:
                    current_state = new_state
                    display_text(OLED_TEXTS[current_state])
                    # Reset hardware for new state
                    buzzer.duty_u16(0)
                    if current_state == 3: set_neopixel((0, 255, 0))
                    elif current_state == 0: set_neopixel((0, 0, 0))
            
            input_buffer = "" # Clear buffer for next command
        else:
            input_buffer += char # Build the string

    # --- B. Non-Blocking Actions ---
    if current_state == 1: # Emergency (Red Blink + Beep)
        if time.ticks_diff(now, last_blink_time) > 300:
            neopixel_on = not neopixel_on
            set_neopixel((255, 0, 0) if neopixel_on else (0, 0, 0))
            last_blink_time = now
        
        if time.ticks_diff(now, last_beep_time) > 1000:
            buzzer.duty_u16(15000 if not buzzer_on else 0)
            buzzer_on = not buzzer_on
            last_beep_time = now

    elif current_state == 2: # Warning (Purple Blink)
        if time.ticks_diff(now, last_blink_time) > 600:
            neopixel_on = not neopixel_on
            set_neopixel((255, 0, 255) if neopixel_on else (0, 0, 0))
            last_blink_time = now
