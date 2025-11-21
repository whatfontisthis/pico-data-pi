from machine import Pin
import time
led = Pin('LED', Pin.OUT)

# GPIO 20번 핀에 연결된 버튼을 입력 모드로 설정합니다. 내부 풀업 저항을 활성화합니다.
button = Pin(20, Pin.IN, Pin.PULL_UP)

# 무한 루프를 통해 버튼의 상태를 지속적으로 확인하고 LED를 제어합니다.
while True:
    # button의 상태를 출력합니다. (눌렸을 때 1, 눌리지 않았을 때 0)
    if button.value() == 0:
        print("1")
        led.value(True)
    else:
        print("0")
        led.value(False)
        
    # 0.1초마다 반복합니다.
    time.sleep(0.1)




