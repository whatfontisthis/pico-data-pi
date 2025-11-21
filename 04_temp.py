from machine import Pin, I2C
import time
from ahtx0 import AHT20   # /lib/ahtx0.py 사용

# ---- I2C 설정 (GP4=SDA, GP5=SCL) ----
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# ---- 센서 객체 만들기 ----
try:
    sensor = AHT20(i2c)        # 주소 0x38 기본
except Exception as e:
    print("AHT20 초기화 실패. 배선/전원 확인:", e)
    raise SystemExit

# ---- 반복 읽기 ----
while True:
    t = sensor.temperature          # 섭씨 온도
    h = sensor.relative_humidity    # 상대습도 %
    print("온도: {:.2f} °C  습도: {:.2f} %".format(t, h))
    time.sleep(0.5)