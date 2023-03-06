import network
import secrets
import time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.SSID, secrets.PASSWORD)
while not wlan.isconnected():
    time.sleep(0.5)

import ntptime
import ubinascii
import ssl
import json
from umqtt.simple import MQTTClient

def read_pem(file):
    with open(file, "r") as input:
        text = input.read().strip()
        split_text = text.split("\n")
        base64_text = "".join(split_text[1:-1])
        return ubinascii.a2b_base64(base64_text)

def callback_handler(topic, message_receive):
    global rem, sec, alm
    tim.init()
    buz.duty_u16(0)
    rem = int(message_receive.decode('UTF-8'))
    client.publish(topic="remain", msg=json.dumps({"message":str(rem)}))
    if rem == 0:
        tm.write([0, 0, 0, 0])
    if rem > 0:
        tm.numbers(rem, 0)
    led.value(1)
    alm = 0
    sec = 60
    tim.init(freq = 1, mode=Timer.PERIODIC, callback=timer_handler)

# optional local NTP server to minimise ntptime.settime() not handling errors
ntptime.host = 'your_local_NTP_server'
rtc = machine.RTC()
while rtc.datetime()[0] < 2023:
    ntptime.settime()
client = MQTTClient(
    client_id="picow",
    server=secrets.ENDPOINT,
    keepalive=60,
    ssl=True,
    ssl_params={
        "key": read_pem(secrets.KEY_FILE),
        "cert": read_pem(secrets.CERT_FILE),
        "server_hostname": secrets.ENDPOINT,
        "cert_reqs": ssl.CERT_REQUIRED,
        "cadata": read_pem("AmazonRootCA1.pem")
    }
)
client.connect()
client.set_callback(callback_handler)
client.subscribe(topic="picow")

from machine import Timer, Pin, PWM
import tm1637

def timer_handler(timer):
    global rem, sec, alm
    if sec > 0:
        sec -= 1
    if alm == 0 and rem > 0:
        tm.numbers(rem-1, sec)
        if sec == 0:
            rem -= 1
            client.publish(topic="remain", msg=json.dumps({"message":str(rem)}))
            sec = 60
            if rem == 0:
                alm = 1
    if alm == 1:
        if sec % 2:
            tm.write([0, 0, 0, 0])
            buz.duty_u16(0)
        else:
            tm.numbers(0, 0)
            buz.duty_u16(32768)
    if sec == 0:
        client.ping()
        sec = 60

tim = Timer()
led = Pin('LED', Pin.OUT)
buz = PWM(Pin(13))
buz.freq(500)
tm = tm1637.TM1637(clk=Pin(27), dio=Pin(28))
rem = 0
client.publish(topic="remain", msg=json.dumps({"message":str(rem)}))
tm.write([0, 0, 0, 0])
led.value(1)
alm = 0
sec = 60
tim.init(freq = 1, mode=Timer.PERIODIC, callback=timer_handler)

while True:
    try:
        client.check_msg()
    except OSError as e:
        machine.reset()
