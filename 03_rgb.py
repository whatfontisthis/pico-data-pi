import machine
import neopixel

# 네오픽셀 설정
pin = machine.pin(21) #21번 핀
np = neopixel.NeoPixel(pin, 1) #네오픽셀 갯수 : 1개

# 네오픽셀 켜기
np[0] = (255, 0, 0)   # (빨강, 초록, 파랑)
np.write()            #적용