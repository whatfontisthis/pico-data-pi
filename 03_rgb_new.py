import machine
import neopixel
import time

pin = machine.Pin(21)
np = neopixel.NeoPixel(pin, 1)

colors = [
    (255, 0, 0),   # 빨강
    (0, 255, 0),   # 초록
    (0, 0, 255)    # 파랑
]

while True:
    for color in colors:
        np[0] = color
        np.write()
        time.sleep(1)  # 1초 대기
