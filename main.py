from machine import Pin, I2C
import ssd1306
import time

# MPU6050のI2Cアドレス
MPU6050_ADDR = 0x68

# レジスタアドレス
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47

# LEDのピン番号
stay_LED = Pin(9,Pin.OUT)
attack_LED = Pin(10,Pin.OUT)
defence_LED = Pin(12,Pin.OUT)

#変数宣言
stay = 0
attack = 0
defence = 0

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
    
    gyro_x = read_raw_data(i2c, GYRO_XOUT_H)
    gyro_y = read_raw_data(i2c, GYRO_YOUT_H)
    gyro_z = read_raw_data(i2c, GYRO_ZOUT_H)
    
    # 加速度の値をm/s^2に変換
    accel_x = (accel_x / 16384.0) * 9.81
    accel_y = (accel_y / 16384.0) * 9.81
    accel_z = (accel_z / 16384.0) * 9.81
    
    # ジャイロスコープの値を度/秒に変換
    gyro_x = gyro_x / 131.0
    gyro_y = gyro_y / 131.0
    gyro_z = gyro_z / 131.0
    
    return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z

# I2Cの設定
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)

# MPU6050を初期化
MPU6050_init(i2c)

# OLEDの設定（幅128ピクセル、高さ64ピクセル）
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

while True:
    # 加速度とジャイロのデータを取得
    accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = get_accel_gyro_data(i2c)
    
    # OLEDにデータを表示
    oled.fill(0)  # 画面をクリア
    oled.text('ax: {:.2f} '.format(accel_x), 0, 0)
    oled.text('ay: {:.2f} '.format(accel_y), 0, 10)
    oled.text('az: {:.2f} '.format(accel_z), 0, 20)
    oled.text('wa: {:.2f} '.format(gyro_x), 0, 30)
    oled.text('wy: {:.2f} '.format(gyro_y), 0, 40)
    oled.text('wz: {:.2f} '.format(gyro_z), 0, 50)
    oled.show()  # 画面を更新
    
    if accel_x < -8 or 8 < accel_x:
        attack = 1
    else:
        attack = 0
    if accel_y < -8 or 8 < accel_y:
        stay = 1
    else:
        stay = 0
    if accel_z < -8 or 8 < accel_z:
        defense = 1
    else:
        defence = 0
        
    if stay == 1:
        stay_LED.value(1)
    else:
        stay_LED.value(0)
    
    if attack == 1:
        attack_LED.value(1)
    else:
        attack_LED.value(0)
    
    if defence == 1:
        defence_LED.value(1)
    else:
        defence_LED.value(0)

    time.sleep(1)