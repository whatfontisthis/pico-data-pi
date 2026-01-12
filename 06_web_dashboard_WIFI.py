import network
import socket
import json
import time
from machine import Pin, I2C, PWM, ADC
import neopixel
import ssd1306  # (추가) OLED
from ahtx0 import AHT20
from bh1750 import BH1750 # (추가) 조도

# ---- WiFi 설정 (수업 환경에 맞게 수정) ----
WIFI_SSID = "#############"  # 학교/교육장 WiFi 이름
WIFI_PASSWORD = "#############"  # WiFi 비밀번호

# --- 2. 학습된 핀 번호 설정 ---
I2C_SDA_PIN = 4     # I2C SDA (GP4)
I2C_SCL_PIN = 5     # I2C SCL (GP5)
BUZZER_PIN = 22     # 부저 (GP22)
NEOPIXEL_PIN = 21   # 네오픽셀 (GP21)
ADC_SENSOR_PIN = 28 # 마이크/수위 센서 (GP28)

# --- 3. (추가) OLED 설정 ---
OLED_WIDTH = 128
OLED_HEIGHT = 64
I2C_ADDR = 0x3C

# --- 4. (수정) 알람 임계값 (전역 변수) ---
# 기본값을 100만으로 설정하여 "비활성화" 상태로 시작
HIGH_THRESHOLD = 1000000.0
alarm_thresholds = {
    "temperature": HIGH_THRESHOLD,
    "humidity": HIGH_THRESHOLD,
    "light": HIGH_THRESHOLD,
    "mic": HIGH_THRESHOLD,
    "water": HIGH_THRESHOLD
}

# 센서 타입 선택 (기본값: "mic" - 마이크)
sensor_type = "mic"  # "mic" 또는 "water"

# 수위 센서 최대 거리 설정
# 40mm = 4cm 를 최대 거리로 사용
MAX_TANK_DISTANCE = 4.0  # 최대 거리 (cm, 40mm)

# --- 5. 하드웨어 초기화 ---
# I2C 버스 (온습도, 조도, OLED)
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400000)

# 부저
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.freq(440)
buzzer.duty_u16(0)

# 네오픽셀
np = neopixel.NeoPixel(Pin(NEOPIXEL_PIN), 1)

# ADC 센서 (마이크/수위) 초기화
adc_sensor = ADC(Pin(ADC_SENSOR_PIN))

# OLED 초기화
try:
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=I2C_ADDR)
    oled.fill(0)
    oled.text("OLED Init OK", 0, 0)
    oled.show()
    print("OLED 초기화 성공")
except Exception as e:
    print(f"OLED 초기화 실패: {e}")
    oled = None 

# --- 6. 센서 객체 생성 (2개 센서) ---
try:
    aht_sensor = AHT20(i2c)
    print("AHT20 (온습도) 초기화 성공")
    if oled: oled.text("AHT20 OK", 0, 16); oled.show()
    bh_sensor = BH1750(0x23, i2c)
    print("BH1750 (조도) 초기화 성공")
    if oled: oled.text("BH1750 OK", 0, 32); oled.show()
except Exception as e:
    print(f"I2C 센서 초기화 실패: {e}")
    if oled: oled.text("SENSOR FAIL", 0, 16); oled.show()
    np[0] = (255, 100, 0) 
    np.write()
    raise SystemExit

# --- 7. (추가) OLED 텍스트 출력 함수 ---
def display_text(lines):
    """OLED에 텍스트 목록(최대 4줄)을 출력합니다."""
    if oled is None: return
    oled.fill(0)
    y_pos = 0
    for i, line_text in enumerate(lines):
        if y_pos < OLED_HEIGHT:
            oled.text(line_text, 0, y_pos)
            y_pos += 16 
        else:
            break
    oled.show()

# --- (추가) 임계값 포맷팅 함수 ---
def format_threshold(value):
    """OLED에 표시할 임계값 텍스트를 포맷합니다."""
    if value >= HIGH_THRESHOLD:
        return "OFF"
    else:
        return str(value)

# --- 8. (수정) WiFi 연결 함수 (OLED 피드백 추가) ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    display_text(["WiFi Connecting...", f"{WIFI_SSID[:16]}", "Plz Wait..."])

    if not wlan.isconnected():
        print(f"WiFi 연결 중... ({WIFI_SSID})")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        timeout = 0
        while not wlan.isconnected() and timeout < 100: # 10초
            time.sleep(0.1)
            timeout += 1
            print(".", end="")
            if oled and timeout % 5 == 0:
                oled.text(".", (timeout % 16) * 8, 48) 
                oled.show()

        if wlan.isconnected():
            ip_address = wlan.ifconfig()[0]
            print(f"\nWiFi 연결 성공!")
            print(f"IP 주소: {ip_address}")
            display_text(["WiFi OK!", "IP Address:", f"{ip_address}"])
            time.sleep(2) 
            return ip_address
        else:
            print("\nWiFi 연결 실패!")
            display_text(["WiFi FAILED!", "Check SSID/PW", "Retrying..."])
            time.sleep(2)
            return None
    else:
        ip_address = wlan.ifconfig()[0]
        print(f"이미 WiFi 연결됨: {ip_address}")
        display_text(["WiFi Already OK", "IP Address:", f"{ip_address}"])
        time.sleep(2)
        return ip_address

# --- 9. LED/부저 제어 함수 (원본 유지) ---
def led_green():
    np[0] = (0, 255, 0)
    np.write()

def led_red():
    np[0] = (255, 0, 0)
    np.write()

def buzzer_on():
    buzzer.duty_u16(30000)

def buzzer_off():
    buzzer.duty_u16(0)

# --- 10. (추가) 마이크 센서 읽기 함수 ---
def read_mic_sensor():
    """마이크 센서의 Peak-to-Peak 값을 읽습니다."""
    sample_size = 100
    max_val = 0
    min_val = 65535
    for _ in range(sample_size):
        val = adc_sensor.read_u16()
        if val > max_val:
            max_val = val
        if val < min_val:
            min_val = val
    peak_to_peak = max_val - min_val
    return peak_to_peak

# --- 11. (추가) 수위 센서 읽기 함수 ---
def read_water_sensor():
    """
    수위 센서의 ADC 값을 읽어 0~MAX_TANK_DISTANCE(cm) 범위로 선형 매핑합니다.
    - raw ADC 범위: 0 ~ 65535
    - 거리(cm) = (adc_value / 65535) * MAX_TANK_DISTANCE
    (반환값: distance_cm, raw_adc_value)
    """
    adc_value = adc_sensor.read_u16()
    # 0~65535 범위를 0~MAX_TANK_DISTANCE(cm)로 단순 매핑
    distance_cm = (adc_value / 65535.0) * MAX_TANK_DISTANCE
    return distance_cm, adc_value

# --- 12. (수정) 모든 임계값 확인하는 알람 함수 ---
def check_alarms(temp, hum, light, mic_value=None, water_value=None):
    """모든 센서의 임계값을 확인하고 알람을 울립니다."""
    global alarm_thresholds, sensor_type # 전역 변수 사용
    
    # 기존 센서들 확인 (임계값이 비활성화 상태가 아닐 때만 확인)
    temp_alarm = False
    if alarm_thresholds["temperature"] < HIGH_THRESHOLD:
        temp_alarm = temp > alarm_thresholds["temperature"]
    
    hum_alarm = False
    if alarm_thresholds["humidity"] < HIGH_THRESHOLD:
        hum_alarm = hum > alarm_thresholds["humidity"]
    
    light_alarm = False
    if alarm_thresholds["light"] < HIGH_THRESHOLD:
        light_alarm = light > alarm_thresholds["light"]
    
    # 선택된 센서 확인
    adc_alarm = False
    if sensor_type == "mic" and mic_value is not None:
        # 마이크 임계값이 비활성화 상태가 아닐 때만 확인
        if alarm_thresholds["mic"] < HIGH_THRESHOLD:
            adc_alarm = mic_value > alarm_thresholds["mic"]
    elif sensor_type == "water" and water_value is not None:
        # 수위 센서는 수위(거리 값)가 임계값을 넘었을 때를 "위험"으로 판단
        # 임계값이 비활성화 상태가 아닐 때만 확인
        if alarm_thresholds["water"] < HIGH_THRESHOLD:
            adc_alarm = water_value > alarm_thresholds["water"]
    
    if temp_alarm or hum_alarm or light_alarm or adc_alarm:
        buzzer_on()
        led_red()
        return True
    else:
        buzzer_off()
        led_green()
        return False

# --- 13. (수정) 모든 센서 데이터 읽기 함수 ---
def read_sensors():
    global sensor_type
    try:
        temperature = aht_sensor.temperature
        humidity = aht_sensor.relative_humidity
        lux = bh_sensor.measurement

        # 선택된 센서 타입에 따라 읽기
        mic_value = None
        water_value = None
        water_adc = None
        
        if sensor_type == "mic":
            mic_value = read_mic_sensor()
        elif sensor_type == "water":
            water_value, water_adc = read_water_sensor()

        # 알람 확인
        alarm_active = check_alarms(temperature, humidity, lux, mic_value, water_value)

        result = {
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "light": round(lux, 1),
            "sensor_type": sensor_type,
            "timestamp": time.time(),
            "alarm": alarm_active,
        }
        
        # 선택된 센서 데이터 추가
        if sensor_type == "mic":
            result["mic"] = mic_value
        elif sensor_type == "water":
            result["water_distance"] = round(water_value, 2)
            result["water_adc"] = water_adc

        return result
    except Exception as e:
        print(f"센서 읽기 오류: {e}")
        buzzer_off()
        return { "error": str(e) }

# --- 12. HTTP 응답 생성 함수 (원본 유지) ---
def create_response(status_code, content_type, body):
    response = f"HTTP/1.1 {status_code}\r\n"
    response += f"Content-Type: {content_type}\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
    response += "Access-Control-Allow-Headers: Content-Type\r\n"
    response += f"Content-Length: {len(body)}\r\n"
    response += "Connection: close\r\n"
    response += "\r\n"
    response += body
    return response

# --- 14. 메인 서버 함수 (POST 처리 수정) ---
def start_server():
    global alarm_thresholds, sensor_type # 전역 변수 수정 허용
    
    ip_address = connect_wifi()
    if not ip_address:
        print("WiFi 연결 실패로 서버 시작 불가")
        display_text(["WiFi FAILED!", "Server STOP."])
        return

    addr = socket.getaddrinfo("0.0.0.0", 8080)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(addr)
        s.listen(5)
    except OSError as e:
        if e.errno == 98:  # EADDRINUSE
            print(f"포트 8080이 이미 사용 중입니다. 다른 프로그램이 실행 중인지 확인하세요.")
            display_text(["Port 8080", "Already in use", "Check running apps"])
            return
        else:
            print(f"소켓 바인딩 오류: {e}")
            display_text(["Socket Error", str(e)])
            return

    led_green() 

    print(f"서버 시작됨: http://{ip_address}:8080")

    display_text(["Server Running", f"IP: {ip_address}", "Port: 8080"])

    try:
        while True:
            try:
                cl, addr = s.accept()

                request_raw = cl.recv(1024)
                request = request_raw.decode("utf-8")

                if not request:
                    cl.close()
                    continue

                if "OPTIONS" in request:
                    response = create_response(200, "text/plain", "")
                    cl.send(response.encode("utf-8"))

                # (추가) POST /sensor_type 요청 처리 (센서 타입 변경)
                elif "POST /sensor_type" in request:
                    try:
                        content_length_start = request.find("Content-Length: ") + 16
                        content_length_end = request.find("\r\n", content_length_start)
                        content_length = int(request[content_length_start:content_length_end])

                        body_start = request.find("\r\n\r\n") + 4
                        body = request[body_start : body_start + content_length]

                        data = json.loads(body)

                        if "type" in data and data["type"] in ["mic", "water"]:
                            sensor_type = data["type"]
                            print(f"센서 타입 변경됨: {sensor_type}")
                            display_text(["Sensor Type", f"Changed to:", f"{sensor_type.upper()}"])
                            response = create_response(200, "application/json", json.dumps({"status": "ok", "sensor_type": sensor_type}))
                        else:
                            response = create_response(400, "text/plain", "Invalid sensor type")
                    except Exception as e:
                        print(f"센서 타입 변경 오류: {e}")
                        response = create_response(400, "text/plain", "Bad Request")

                    cl.send(response.encode("utf-8"))

                # (수정) POST /alarm_threshold 요청 처리
                elif "POST /alarm_threshold" in request:
                    try:
                        # HTTP Body 부분 찾기
                        content_length_start = request.find("Content-Length: ") + 16
                        content_length_end = request.find("\r\n", content_length_start)
                        content_length = int(request[content_length_start:content_length_end])

                        body_start = request.find("\r\n\r\n") + 4
                        body = request[body_start : body_start + content_length]

                        new_thresholds = json.loads(body)

                        # 전역 변수 업데이트
                        if "temperature" in new_thresholds:
                            alarm_thresholds["temperature"] = float(new_thresholds["temperature"])
                        if "humidity" in new_thresholds:
                            alarm_thresholds["humidity"] = float(new_thresholds["humidity"])
                        if "light" in new_thresholds:
                            alarm_thresholds["light"] = float(new_thresholds["light"])
                        if "mic" in new_thresholds:
                            alarm_thresholds["mic"] = float(new_thresholds["mic"])
                        if "water" in new_thresholds:
                            alarm_thresholds["water"] = float(new_thresholds["water"])

                        print(f"임계값 업데이트됨: {alarm_thresholds}")

                        # (수정) OLED 표시에 format_threshold 함수 적용
                        t_str = format_threshold(alarm_thresholds['temperature'])
                        h_str = format_threshold(alarm_thresholds['humidity'])
                        l_str = format_threshold(alarm_thresholds['light'])
                        m_str = format_threshold(alarm_thresholds['mic'])
                        w_str = format_threshold(alarm_thresholds['water'])
                        display_text(["Thresholds SET", f"T:{t_str} H:{h_str}", f"L:{l_str} M:{m_str}", f"W:{w_str}"])

                        response = create_response(200, "application/json", json.dumps({"status": "ok", "thresholds": alarm_thresholds}))
                    except Exception as e:
                        print(f"POST 요청 처리 오류: {e}")
                        response = create_response(400, "text/plain", "Bad Request")

                    cl.send(response.encode("utf-8"))

                elif "GET /sensors" in request:
                    sensor_data = read_sensors()
                    json_data = json.dumps(sensor_data)
                    response = create_response(200, "application/json", json_data)
                    cl.send(response.encode("utf-8"))

                    if "error" not in sensor_data:
                        lines = [
                            f"T: {sensor_data['temperature']} C",
                            f"H: {sensor_data['humidity']} %",
                            f"L: {sensor_data['light']} lx"
                        ]
                        if sensor_data['sensor_type'] == "mic" and "mic" in sensor_data:
                            lines.append(f"Mic: {sensor_data['mic']}")
                        elif sensor_data['sensor_type'] == "water" and "water_distance" in sensor_data:
                            lines.append(f"W: {sensor_data['water_distance']} cm")
                        display_text(lines)

                elif "GET /" in request:
                    html = f"<html>...<body><h1>Pico Client Server</h1><p>IP: {ip_address}</p><p><a href='/sensors'>/sensors</a></p></body></html>"
                    response = create_response(200, "text/html", html)
                    cl.send(response.encode("utf-8"))

                else:
                    response = create_response(404, "text/plain", "Not Found")
                    cl.send(response.encode("utf-8"))

                cl.close()

            except Exception as e:
                print(f"서버 오류: {e}")
                display_text(["Server Error", str(e)])
                if 'cl' in locals():
                    cl.close()
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
        display_text(["Server", "Shutting down", "Good bye"])
        buzzer_off()
        led_red()
        time.sleep(1)
    finally:
        # 서버 소켓 닫기 (포트 회수)
        if 's' in locals():
            s.close()
            print("포트 8080이 회수되었습니다.")


# ---- 프로그램 시작 ----
if __name__ == "__main__":
    print("Pico 센서 서버 (WiFi Client, 3-Threshold, OLED) 시작...")
    start_server()