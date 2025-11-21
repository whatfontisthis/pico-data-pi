from machine import Pin
import time

led = Pin("LED", Pin.OUT)

while True:
    led.toggle()
    time.sleep(1)
    
    #다음 코드도 동일한 동작을 합니다.
    #led.on()
    #time.sleep(1)
    #led.off()
    #time.sleep(1)
    