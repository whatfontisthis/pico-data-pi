from machine import Pin, PWM
import time
# GPIO 22번 핀에 부저를 PWM(Pulse Width Modulation) 모드로 설정합니다.
buzzer = PWM(Pin(22))
# 부저의 주파수를 500Hz로 설정합니다. 이것은 부저가 내는 소리의 톤을 결정합니다.
buzzer.freq(500)
# 부저의 듀티 사이클을 설정하여 소리를 활성화합니다. duty_u16 값은 0에서 65535 사이입니다.
buzzer.duty_u16(1000)
# 부저가 1초 동안 소리를 낸 후에 대기합니다.
time.sleep(1)
# 부저의 듀티 사이클을 0으로 설정하여 소리를 끕니다.
buzzer.duty_u16(0)

