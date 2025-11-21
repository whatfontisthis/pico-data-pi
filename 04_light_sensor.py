from machine import Pin, I2C
import time
from bh1750 import BH1750   # /lib 폴더에 bh1750.py

# ---- I2C 설정 (SDA=GP4, SCL=GP5) ----
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# ---- BH1750 객체 생성 (주소 0x23 기본) ----
sensor = BH1750(0x23, i2c)

# ---- 반복 측정 ----
while True:
    lux = sensor.measurement
    print("조도:", f'{lux:>8.2f}', "lux")
    time.sleep(1)
