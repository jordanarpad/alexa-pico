import network
import secrets
import time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.SSID, secrets.PASSWORD)

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
    print('Wi-Fi connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

from machine import Timer, Pin, PWM
import tm1637
from umqtt.simple import MQTTClient
import json

tim = Timer()
alm = Timer()
rem = Timer()
led = Pin('LED', Pin.OUT)
buzzer = PWM(Pin(13))
buzzer.freq(500)
tm = tm1637.TM1637(clk=Pin(27), dio=Pin(28))

def active(timer):
    global remain, sec
    sec -= 1
    if (sec % 2 == 0):
        led.toggle()
    if (sec % 3 == 0):
        tm.numbers(remain-1, sec//3)

def expired(timer):
    global remain, sec
    rem.init()
    remain = 0
    sec = 0
    print('Published remain')
    print(remain)
    client.publish(topic="remain", msg=json.dumps({"message":str(remain)}))
    tm.numbers(remain, sec)
    tim.init(freq=3, mode=Timer.PERIODIC, callback=alarm)

def alarm(timer):
    global remain, sec
    led.toggle()
    buzzer.duty_u16(1000)
    tm.write([0, 0, 0, 0])
    time.sleep(0.1)
    tm.numbers(remain, sec)
    buzzer.duty_u16(0)

def update(timer):
    global remain, sec
    if remain > 0:
        remain -= 1
        sec = 0
        print('Published remain')
        print(remain)
        client.publish(topic="remain", msg=json.dumps({"message":str(remain)}))
        tm.numbers(remain, sec)
        sec = 180
        tim.init(freq=3, mode=Timer.PERIODIC, callback=active)
    client.ping()
    rem.init(mode=Timer.ONE_SHOT, period=60000, callback=update)

def mqtt_connect():
    endpoint = secrets.ENDPOINT
    port_no = 8883
    cert_file = secrets.CERT_FILE
    key_file = secrets.KEY_FILE
    with open(cert_file, 'rb') as f:
        cert = f.read()
    with open(key_file, 'rb') as f:
        key = f.read()
    print('Certificate and Private Key loaded')
    sslparams = {'cert':cert, 'key':key}
    client = MQTTClient(client_id='picow', server=endpoint, port=port_no, keepalive=60, ssl=True, ssl_params=sslparams)
    client.connect()
    print('Connected to AWS IoT Core MQTT Broker')
    return client

def callback_handler(topic, message_receive):
    global remain, sec
    print('Received message')
    minutes = int(message_receive.decode('UTF-8'))
    print(minutes)
    if minutes == 0:
        tim.init()
        alm.init()
        remain = 0
        sec = 0
        print('Published remain')
        print(remain)
        client.publish(topic="remain", msg=json.dumps({"message":str(remain)}))
        rem.init(mode=Timer.ONE_SHOT, period=60000, callback=update)
        tm.write([0, 0, 0, 0])
        led.value(1)
    else:
        remain = minutes
        sec = 0
        print('Published remain')
        print(remain)
        client.publish(topic="remain", msg=json.dumps({"message":str(remain)}))
        tm.numbers(remain, sec)
        sec = 180
        tim.init(freq=3, mode=Timer.PERIODIC, callback=active)
        alm.init(mode=Timer.ONE_SHOT, period=minutes*60000, callback=expired)
        rem.init(mode=Timer.ONE_SHOT, period=60000, callback=update)

client = mqtt_connect()
client.set_callback(callback_handler)
client.subscribe(topic="picow")
remain = 0
sec = 0
print('Published remain')
print(remain)
client.publish(topic="remain", msg=json.dumps({"message":str(remain)}))
rem.init(mode=Timer.ONE_SHOT, period=60000, callback=update)
tm.write([0, 0, 0, 0])
led.value(1)


while True:
    try:
        client.check_msg()
    except OSError as e:
        machine.reset()
