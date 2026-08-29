# bus.py
# 设备状态：True 表示通电/开启，False 表示断电/关闭
devices = {
    "LAMP": False,
    "FAN": False,
    "PUMP": False,
    "FEEDER": False,
}

# 传感器数据：由地图模块每帧更新
sensors = {
    "TEMP": 25,
    "PRESSURE": 100,
    "LIGHT": 0,
    "SOUND": 0,
}