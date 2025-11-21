import machine
import time
import sys
import select
from neopixel import NeoPixel
import ssd1306  # (추가) OLED 라이브러리

# --- 1. 학습된 핀 번호 설정 ---
NEOPIXEL_PIN = 21  # 네오픽셀 (GP21)
BUZZER_PIN = 22    # 부저 (GP22)
I2C_SDA_PIN = 4    # I2C SDA (GP4)
I2C_SCL_PIN = 5    # I2C SCL (GP5)
LOG_FILE = 'serial_log.txt'

# --- 2. (추가) OLED 설정 ---
OLED_WIDTH = 128
OLED_HEIGHT = 64
I2C_ADDR = 0x3C # OLED 주소

# --- 3. (추가) OLED에 표시할 텍스트 (128x64, 4줄 맞춤) ---
OLED_TEXTS = {
    # Class 0 또는 알 수 없음
    0: ["Status: IDLE",
        "",
        "Waiting for",
        "commands..."],
     # -------Class 1---------
    1: ["!!! EMERGENCY !!!",
        "Class 1",
        "left arm",
        "  Evacuate Now!"],
    # -------Class 2---------
    2: ["-- WARNING --",
        "Class 2",
        "right arm",
        "Be Cautious."],
    # -------Class 3---------
    3: ["Status: SAFE",
        "Class 3",
        "both arms down",
        "All Clear."],
    # -----------------------
    "boot": ["Booting...",
             "",
             "System Check...",
             ""],
    "error": ["SYSTEM ERROR",
              "",
              "Check log file",
              "for details."]
}

# --- 4. 하드웨어 초기화 ---
# 네오픽셀
np = NeoPixel(machine.Pin(NEOPIXEL_PIN), 1)

# 부저 (PWM)
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))
buzzer.freq(440)     # '라' 음 (440Hz)
buzzer.duty_u16(0)   # 볼륨 0으로 시작

# 시리얼 입력 감지기
poller = select.poll()
poller.register(sys.stdin, select.POLLIN)

# (추가) I2C 및 OLED 초기화
try:
    i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA_PIN), scl=machine.Pin(I2C_SCL_PIN), freq=400000)
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=I2C_ADDR)
    oled.fill(0)
    oled.show()
except Exception as e:
    print(f"OLED 초기화 실패: {e}. OLED 없이 계속합니다.")
    oled = None # OLED 없이도 프로그램이 동작하도록 None 처리

# --- 5. 색상 정의 ---
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_PURPLE = (255, 0, 255) # Class 2 (주의)
COLOR_OFF = (0, 0, 0)
COLOR_ERROR = (255, 100, 0)  # 오류시 주황색

# --- 6. 상태 변수 ---
current_state = 0
last_blink_time = 0
last_beep_time = 0
neopixel_on = False
buzzer_on = False

# --- 7. 헬퍼 함수 ---
def set_neopixel(color):
    """네오픽셀 색상을 즉시 적용"""
    np[0] = color
    np.write()

def log_message(msg):
    """파일에 로그를 기록합니다."""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{time.ticks_ms()}: {msg}\n")
    except Exception as e:
        print(f"Failed to write log: {e}")

def display_text(text_list):
    """OLED에 텍스트 목록을 출력합니다."""
    if oled is None: # OLED가 초기화되지 않았다면 함수 종료
        return
        
    oled.fill(0) # 화면 지우기
    for i, line_text in enumerate(text_list):
        # (수정) Y 좌표 계산: 인덱스(i) * 한 줄 높이(16)
        y_pos = i * 16
        
        if y_pos < OLED_HEIGHT:
            oled.text(line_text, 0, y_pos) # (텍스트, X좌표, Y좌표)
        else:
            break
    oled.show() # 화면 갱신

# --- 8. 부팅 및 시작 ---
log_message("---- SCRIPT STARTED ----")
display_text(OLED_TEXTS["boot"]) # (추가) OLED에 부팅 메시지
set_neopixel(COLOR_GREEN)
current_state = 3
time.sleep(1) # 부팅 메시지를 1초간 보여줌
display_text(OLED_TEXTS[current_state]) # (추가) OLED에 현재 상태(안전) 표시
print("Pico Ready. Waiting for Serial commands...")

# --- 9. 메인 루프 ---
while True:
    try:
        now = time.ticks_ms()

        # --- A. 시리얼 입력 처리 ---
        events = poller.poll(10)
        
        if events:
            line_data = sys.stdin.readline()
            if line_data:
                class_name = line_data.strip()
                log_message(f"Received: {class_name}")
                
                new_state = 0 # 기본값 (알수없는 명령)
                if class_name == "Class 1":
                    new_state = 1
                elif class_name == "Class 2":
                    new_state = 2
                elif class_name == "Class 3":
                    new_state = 3

                # 상태가 변경되었을 때만 실행
                if new_state != current_state:
                    current_state = new_state
                    
                    # (추가) OLED에 즉시 상태 텍스트 출력
                    display_text(OLED_TEXTS[current_state])
                    
                    # --- 장치 초기화 ---
                    buzzer.duty_u16(0)
                    buzzer_on = False
                    neopixel_on = False
                    
                    if current_state == 3:
                        set_neopixel(COLOR_GREEN)
                    elif current_state == 0:
                        set_neopixel(COLOR_OFF)
                    
                    last_blink_time = now
                    last_beep_time = now

        # --- B. 현재 상태에 따른 동작 처리 (비차단) ---

        # 1. 비상 (Class 1): 빨간색 깜빡임 + 2초 간격 비프음
        if current_state == 1:
            if time.ticks_diff(now, last_blink_time) > 500:
                neopixel_on = not neopixel_on
                set_neopixel(COLOR_RED if neopixel_on else COLOR_OFF)
                last_blink_time = now

            if not buzzer_on and time.ticks_diff(now, last_beep_time) > 2000:
                buzzer.duty_u16(30000)
                buzzer_on = True
                last_beep_time = now
            
            if buzzer_on and time.ticks_diff(now, last_beep_time) > 500:
                buzzer.duty_u16(0)
                buzzer_on = False

        # 2. 주의 (Class 2): 보라색 깜빡임
        elif current_state == 2:
            if time.ticks_diff(now, last_blink_time) > 500:
                neopixel_on = not neopixel_on
                set_neopixel(COLOR_PURPLE if neopixel_on else COLOR_OFF)
                last_blink_time = now
        
        # 3. 안전 (Class 3) 또는 0. IDLE (Class 0):
        #    (상태 변경 시 이미 네오픽셀/부저가 설정되었으므로
        #     루프에서 추가로 할 작업 없음)

    except Exception as e:
        log_message(f"ERROR: {str(e)}")
        display_text(OLED_TEXTS["error"]) # (추가) OLED에 오류 메시지
        for _ in range(5):
            set_neopixel(COLOR_ERROR); time.sleep_ms(50)
            set_neopixel(COLOR_OFF); time.sleep_ms(50)
