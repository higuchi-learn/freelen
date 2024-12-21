import network
import socket
import time
from machine import Pin, ADC
from secret import ssid,password
from machine import Pin, I2C, PWM
import ssd1306
import time
import network
from secret import ssid, password
import socket

# MPU6050のI2Cアドレス
MPU6050_ADDR = 0x68

# レジスタアドレス
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F

# LED、スピーカのピン番号
stay_LED = Pin(9,Pin.OUT)
attack_LED = Pin(10,Pin.OUT)
defence_LED = Pin(12,Pin.OUT)
speaker = PWM(Pin(4, Pin.OUT))

#変数宣言
stay = 0
attack = 0
defence = 0
status = "stay"
before = "stay"

A4 = 440

#移植部分
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
       
# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

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

# OLEDの設定（幅128ピクセル、高さ64ピクセル）
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

while True:
    # 加速度とジャイロのデータを取得
    accel_x, accel_y, accel_z= get_accel_gyro_data(i2c)
    
    # OLEDにデータを表示
    oled.fill(0)  # 画面をクリア
    oled.text('ax: {:.2f} '.format(accel_x), 0, 0)
    oled.text('ay: {:.2f} '.format(accel_y), 0, 10)
    oled.text('az: {:.2f} '.format(accel_z), 0, 20)
    oled.show()  # 画面を更新
    
    if accel_x < -7 or 7 < accel_x:
        attack_LED.value(1)
        status = "attack"
    else:
        attack_LED.value(0)
    if accel_y < -7 or 7 < accel_y:
        stay_LED.value(1)
        status = "stay"
    else:
        stay_LED.value(0)
    if accel_z < -7 or 7 < accel_z:
        defence_LED.value(1)
        status = "defence"
    else:
        defence_LED.value(0)

    if before == status:
        speaker.duty_u16(0)
    else :
        speaker.freq(int(A4 + 0.5))
        speaker.duty_u16(0x8000)
    
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        print(request)

        cl.send(status)
        print("Sent:" + status)
        cl.close()

    except OSError as e:
        cl.close()
        print('connection closed')
    before = status

    time.sleep(1)