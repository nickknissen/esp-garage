# Copyright(c) 2017 by craftyguy "Clayton Craft" <clayton@craftyguy.net>
# Distributed under GPLv3+ (see COPYING) WITHOUT ANY WARRANTY.

import uasyncio as asyncio
import machine
from umqtt.robust import MQTTClient

# Settings
MQTT_SERVER = '192.168.1.5'     # MQTT Broker to subscribe with
PWM_FREQUENCY = 1000            # in Hz, should be 0 < freq < 1000 for esp8266
CONTROL_TOPIC = 'home/garage/door/control'
STATUS_TOPIC = 'home/garage/door/status'
DOOR_TOGGLE_PIN = 2
TRIG_PIN = 16
ECHO_PIN = 13

# Globals
door_open = False
# Generate unique name based on uid and start mqtt client
umqtt_uid = "umqtt_client_" + ''.join('%02X' % b for b in machine.unique_id())
umqtt_client = MQTTClient(umqtt_uid, MQTT_SERVER)

# 0 <= start_illum < stop_illum < 100
# durations are in minutes
async def open_door():
    # pick pin to use to toggle relay
    # maybe sep. functions for toggling door aren't needed, since they do the exact same thing..

async def close_door():
    # pick pin to use to toggle relay

async def check_door_state():
    global door_open
    #TODO: Add logic for using ultrasonic sensor
    #door_open = True

async def publish_status():
    global umqtt_client
    if door_open:
        umqtt_client.publish(STATUS_TOPIC, b'open')
    else:
        umqtt_client.publish(STATUS_TOPIC, b'closed')
    await asyncio.sleep(30)

def sub_cb(topic, msg):
    t = topic.decode('ASCII')
    m = msg.decode('ASCII')
    print("received new topic/msg: %s / %s" % (t, m))
    loop = asyncio.get_event_loop()

    if t == CONTROL_TOPIC:
        if m == 'open':
            pass
            loop.create_task(open_door())
        elif m == 'close':
            pass
            loop.create_task(close_door())
        else:
            print("Unable to parse message: %s" % m)
            return
    else:
        print("Unknown topic")

async def main():
    global umqtt_client

    umqtt_client.DEBUG = True
    umqtt_client.set_callback(sub_cb)

    if not umqtt_client.connect(clean_session=True):
        print("Connected to MQTT broker: %s" % MQTT_SERVER)
        umqtt_client.subscribe(START_TOPIC)
        umqtt_client.subscribe(STOP_TOPIC)
    while True:
        # non-blocking check for messages to allow other coros to do their thang
        umqtt_client.check_msg()
        await asyncio.sleep(1)

    umqtt_client.disconnect()


# Make sure we don't overdo the PWM frequency for the esp8266,
# which is limited to 1kHz
if PWM_FREQUENCY < 0:
    PWM_FREQUENCY = 100
elif PWM_FREQUENCY > 1000:
    PWM_FREQUENCY = 1000

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.create_task(publish_status())
loop.run_forever()
