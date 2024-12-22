from machine import Pin, I2C, PWM
import utime
import time
import network
import urequests
import ujson
from secret import ssid, password

#ラズパイに設定した固定IPと使用するポート番号
url = 'https://prj-freeren-back.onrender.com/device/input'

# MPU6050のI2Cアドレス
MPU6050_ADDR = 0x68

# レジスタアドレス
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F

# LED、スピーカのピン番号
speaker = PWM(Pin(3, Pin.OUT))

#変数宣言
action = "collection"

A3 = 220
A4 = 440
A5 = 880
melody = A4

def MPU6050_init(i2c):
    # MPU6050をスリープモードから解除
    i2c.writeto_mem(MPU6050_ADDR, PWR_MGMT_1, b'\x00')

def read_raw_data(i2c, addr):
    high = i2c.readfrom_mem(MPU6050_ADDR, addr, 1)
    low = i2c.readfrom_mem(MPU6050_ADDR, addr + 1, 1)
    value = (high[0] << 8) | low[0]
    if value > 32768:
        value -= 65536
    return value

def get_accel_gyro_data(i2c):
    accel_x = read_raw_data(i2c, ACCEL_XOUT_H)
    accel_y = read_raw_data(i2c, ACCEL_YOUT_H)
    accel_z = read_raw_data(i2c, ACCEL_ZOUT_H)

    # 加速度の値をm/s^2に変換
    accel_x = (accel_x / 16384.0) * 9.81
    accel_y = (accel_y / 16384.0) * 9.81
    accel_z = (accel_z / 16384.0) * 9.81

    return accel_x, accel_y, accel_z

# I2Cの設定
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)

# MPU6050を初期化
MPU6050_init(i2c)

#温度取得と通信のインターバル（秒）
interval = 0.5

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])

#ユニキャスト
def com_send(text):
    print(text)
    #データをDICT型で宣言
    data = {
             "deviceId" : "1",
             "action" : text
             }
    #jsonデータで送信するという事を明示的に宣言
    header = {
        'Content-Type' : 'application/json'
         }
    res = urequests.post(
        url,
        data = ujson.dumps(data).encode("utf-8"),
        headers = header
    )
    print(res.json())
    res.close()


#一定間隔で内部温度を取得してキャスト
while True:

    # 加速度とジャイロのデータを取得
    accel_x, accel_y, accel_z= get_accel_gyro_data(i2c)

    if accel_x < -7 or 7 < accel_x:
        action = "collection"
    if accel_y < -7 or 7 < accel_y:
        action = "attack"
    if accel_z < -7 or 7 < accel_z:
        action = "defend"


    if action == "collection":
        melody = A4
    elif action == "attack":
        melody = A5
    else:
        melody = A3
    speaker.freq(int(melody + 0.5))
    speaker.duty_u16(0x8000)
    if action == "collection":
        utime.sleep(0.1)
        speaker.duty_u16(0)
    elif action == "attack":
        utime.sleep(0.03)
        speaker.duty_u16(0)
        utime.sleep(0.03)
        speaker.freq(int(melody + 0.5))
        speaker.duty_u16(0x8000)
        utime.sleep(0.03)
        speaker.duty_u16(0)
        utime.sleep(0.03)
        speaker.duty_u16(0)
        utime.sleep(0.03)
        speaker.freq(int(melody + 0.5))
        speaker.duty_u16(0x8000)
        utime.sleep(0.03)
        speaker.duty_u16(0)
    com_send(action)

    if action == "defend":
        melody = A3
        speaker.freq(int(melody + 0.5))
        speaker.duty_u16(0x8000)

    utime.sleep(interval)

