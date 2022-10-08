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
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('network connection failed')

from machine import Timer, Pin, PWM
import tm1637
from umqtt.simple import MQTTClient
import json

tim = Timer()
led = Pin('LED', Pin.OUT)
buz = PWM(Pin(13))
buz.freq(500)
tm = tm1637.TM1637(clk=Pin(27), dio=Pin(28))

def timer_handler(timer):
    global rem, sec, alm
    if sec > 0:
        sec -= 1
    if alm == 0 and rem > 0:
        if (sec % 2 == 0):
            led.toggle()
        if (sec % 3 == 0):
            tm.numbers(rem-1, sec//3)
        if sec == 0:
            rem -= 1
            client.publish(topic="remain", msg=json.dumps({"message":str(rem)}))
            sec = 180
            if rem == 0:
                alm = 1
    if alm == 1:
        led.toggle()
        buz.duty_u16(1000)
        tm.write([0, 0, 0, 0])
        time.sleep(0.1)
        tm.numbers(0, 0)
        buz.duty_u16(0)
    if sec == 0:
        client.ping()
        sec = 180

def mqtt_connect():
    endpoint = secrets.ENDPOINT
    port_no = 8883
    cert_file = secrets.CERT_FILE
    key_file = secrets.KEY_FILE
    with open(cert_file, 'rb') as f:
        cert = f.read()
    with open(key_file, 'rb') as f:
        key = f.read()
    sslparams = {'cert':cert, 'key':key}
    client = MQTTClient(client_id='picow', server=endpoint, port=port_no, keepalive=60, ssl=True, ssl_params=sslparams)
    client.connect()
    return client

def callback_handler(topic, message_receive):
    global rem, sec, alm
    tim.init()
    rem = int(message_receive.decode('UTF-8'))
    client.publish(topic="remain", msg=json.dumps({"message":str(rem)}))
    if rem == 0:
        tm.write([0, 0, 0, 0])
    if rem > 0:
        tm.numbers(rem, 0)
    led.value(1)
    alm = 0
    sec = 180
    tim.init(freq = 3, mode=Timer.PERIODIC, callback=timer_handler)

client = mqtt_connect()
client.set_callback(callback_handler)
client.subscribe(topic="picow")

rem = 0
client.publish(topic="remain", msg=json.dumps({"message":str(rem)}))
tm.write([0, 0, 0, 0])
led.value(1)
alm = 0
sec = 180
tim.init(freq = 3, mode=Timer.PERIODIC, callback=timer_handler)

while True:
    try:
        client.check_msg()
    except OSError as e:
        machine.reset()
