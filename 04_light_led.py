from machine import Pin, I2C
from bh1750 import BH1750
import time

light = BH1750(0x23, I2C(0, sda=Pin(4), scl=Pin(5)))
led = Pin('LED', Pin.OUT)

while True:
  print(light.measurement)      # 현재 조도센서 밝기(lx) 출력
  if light.measurement >= 500:  # 밝기 값이 500 이상이면
    led.off()                   # LED 끄기
  else:                         # 아니라면
    led.on()                    # LED LED 켜기
  time.sleep(1)

    