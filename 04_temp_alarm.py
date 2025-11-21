import time
from machine import Pin, I2C, PWM
import ahtx0

# 온습도 센서 설정 (I2C 0번, SCL=5, SDA=4)
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)
sensor = ahtx0.AHT20(i2c)

# 부저 설정 (PWM, 22번 핀)
buzzer = PWM(Pin(22))
buzzer.freq(500)   # 500Hz (소리 톤)
buzzer.duty_u16(0) # 👈 **중요: 처음엔 소리를 끈 상태로 시작**

# --- 2. 메인 루프 (무한 반복) ---
while True:
    # 1. 센서 값 읽기
    temperature_c = sensor.temperature
    humidity = sensor.relative_humidity

    # 터미널에 현재 상태 출력
    print(f"현재 상태: 온도 {temperature_c:.1f} °C / 습도 {humidity:.1f} %")

    # 4. 조건문: 온도가 28도를 초과했는지 확인
    if temperature_c > 28:
        # 28도 초과: 1초간 "삐!" 울림
        buzzer.duty_u16(1000) # 부저 켜기 (중간 세기)
        time.sleep(1.0)       # 1초 동안 울림
        buzzer.duty_u16(0)    # 부저 끄기
        time.sleep(1.0)       # 1초 동안 쉼 (총 2초 주기)
    
    else:
        # 28도 이하: 부저를 끄고 2초간 대기
        buzzer.duty_u16(0)    # 부저 끄기 (조용히)
        time.sleep(2.0)       # 2초 대기
    

