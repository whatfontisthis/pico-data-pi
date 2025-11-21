from machine import Pin, PWM  # 버저를 제어하기 위한 라이브러리 가져오기
import notes  # 음표에 대한 주파수 값을 포함하는 모듈 가져오기
import time

# 22번 핀에 버저 초기화
buzzer = PWM(Pin(22))

# 멜로디(노래) 정의, "-"는 쉬는 부분을 의미
song = [
    "미5", "미5", "-", "미5", "-", "도5", "미5", "-", "솔5", "-", "-", "-", "솔4", "-", "-", "-",
    "도5", "-", "-", "솔4", "-", "-", "미4", "-", "-", "라4", "-", "시4", "-", "라#4", "라4",
    "솔4", "미5", "솔5", "라5", "파5", "솔5", "-", "미5", "도5", "레5", "시4", "-", "-",
    "도5", "-", "-", "솔4", "-", "-", "미4", "-", "-", "라4", "-", "시4", "-", "라#4", "라4",
    "솔4", "미5", "솔5", "라5", "파5", "솔5", "-", "미5", "도5", "레5", "시4", "-", "-"
]

# 음표를 재생하는 함수
def playtone(frequency):
    if frequency == 0:  # 주파수가 0일 때(쉼표)
        buzzer.duty_u16(0)
    else:
        buzzer.duty_u16(3000)  # 소리의 크기(볼륨) 설정
        buzzer.freq(frequency)  # 주파수 설정

# 소리를 끄는 함수
def bequiet():
    buzzer.duty_u16(0)

# 노래를 재생하는 함수
def playsong(mysong):
    for note in mysong:
        if note == "-":  # 쉼표일 때
            bequiet()
        else:
            playtone(notes.tones[note])  # 음표 재생 (한글 표기 사용)
        time.sleep(0.2)  # 노트 사이의 지연 (속도 설정 부분)
    bequiet()

# 메인 함수 실행
playsong(song)

