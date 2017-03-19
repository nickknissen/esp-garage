# Copyright(c) 2017 by craftyguy "Clayton Craft" <clayton@craftyguy.net>
# Distributed under GPLv3+ (see COPYING) WITHOUT ANY WARRANTY.

import uasyncio as asyncio
import machine
import utime
import asyn
from umqtt.simple import MQTTClient

### Settings
MQTT_SERVER = '1.1.1.1'     # MQTT Broker to subscribe with
CONTROL_TOPIC = 'home/garage/door/control'  # mqtt topic to subscribe to for cmds
STATUS_TOPIC = 'home/garage/door/status'    # mqtt topic to publish to for status
# esp8266 pins
DOOR_TOGGLE_PIN = 15            # Pick a pin with internal pull-down
TRIG_PIN = 16
ECHO_PIN = 12
# data for calculating door state
CHECK_DOOR_INTERVAL = .05       # Interval to check door status, in minutes
DOOR_OPEN_DISTANCE = .5         # Distance (m) from sensor to door when open
SPEED_OF_SOUND = 29.1           # Speed of sound (cm/us)

### Globals
# Generate unique name based on uid and start mqtt client
umqtt_uid = "umqtt_client_" + ''.join('%02X' % b for b in machine.unique_id())
umqtt_client = MQTTClient(umqtt_uid, MQTT_SERVER)
# Lock for accessing mqtt client
umqtt_lock = asyn.Lock()
mqtt_connected = False

# On my garage door opener, door is toggled by shorting the two bell wires
# that come from it. They are fed to a relay, which is controlled by
# the DOOR_TOGGLE_PIN
async def toggle_door():
    p = machine.Pin(DOOR_TOGGLE_PIN, machine.Pin.OUT)
    p.high()
    await asyncio.sleep_ms(100)
    p.low()


# open_door and close_door just call toggle_door for now, since my
# garage door opener uses the same mechanism to do both. keeping these separate
# for, uh, modularity.
async def open_door():
    loop.create_task(toggle_door())


async def close_door():
    loop.create_task(toggle_door())


# check door state (open or closed) by using HC-SR04
# to measure distance from sensor to door. Parameters
# can be adjusted by editing variables at top of this file.
async def check_door_state(lock):
    global umqtt_client
    global mqtt_connected
    global door_opened

    echo = machine.Pin(ECHO_PIN, machine.Pin.IN)
    trig = machine.Pin(TRIG_PIN, machine.Pin.OUT)
    distance = 0.0
    state = 'closed'
    await asyncio.sleep(5)

    while True:
        # HC-SR04 is triggered by a 10us pulse on 'trig' pin
        # Set trigger pin to low to make sure there's a good rise when set high
        trig.low()
        utime.sleep_us(100)
        # Toggle trigger pin for 10us
        trig.high()
        utime.sleep_us(10)
        trig.low()
        # echo pin will be high for a duration (is us) indicating distance.
        try:
            pulse_width = machine.time_pulse_us(echo, 1)
        except:
            # Something weird happened
            print("Unable to time echo pulse")
            pass
        # If no pulse measured before timeout or no drop at end of pulse,
        # then width is < 0
        if pulse_width > 0:
            # Hint: 29 = cm / us for sound, divided by 2 since we want half
            # the distance measured
            distance_cm = ((pulse_width / 2) / SPEED_OF_SOUND )
            print("Measured distance of %f cm" % distance_cm)
            # DOOR_OPEN_DISTANCE is in meters
            if (distance_cm / 100.0) <= DOOR_OPEN_DISTANCE:
                door_state = b'open'
                door_opened = True
            else:
                door_state = b'closed'
                door_opened = False
            # publish state
            async with lock:
                try:
                    umqtt_client.publish(STATUS_TOPIC, door_state)
                except:
                    loop.create_task(reconnect(lock))
        else:
            print("Unable to get distance.")
        await asyncio.sleep(CHECK_DOOR_INTERVAL * 60)


#  sub_cb: callback for mqtt client subscriptions
def sub_cb(topic, msg):
    t = topic.decode('ASCII')
    m = msg.decode('ASCII')
    print("received new topic/msg: %s / %s" % (t, m))
    loop = asyncio.get_event_loop()

    if t == CONTROL_TOPIC:
        if m == 'open':
            if not door_opened:
                loop.create_task(open_door())
            else:
                print("Door already OPENED")
        elif m == 'close':
            if door_opened:
                loop.create_task(close_door())
            else:
                print("Door already CLOSED")
        else:
            print("Unable to parse message: %s" % m)
            return
    else:
        print("Unknown topic")

async def reconnect(lock):
    global umqtt_client
    global mqtt_connected
    retry_delay = 5
    umqtt_client.DEBUG = True
    umqtt_client.set_callback(sub_cb)
    mqtt_connected = False
    async with lock:
        while not mqtt_connected:
            try:
                umqtt_client.connect(clean_session=True)
                mqtt_connected = True
            except:
                # Unable to connect, retry
                print("Unable to connect to mqtt server %s, trying again in %i seconds" % (MQTT_SERVER, retry_delay))
                await asyncio.sleep(retry_delay)
        print("Connected to MQTT broker: %s" % MQTT_SERVER)
        umqtt_client.subscribe(CONTROL_TOPIC)


# main: start mqtt subscribe, and periodically check for new messages
async def check_subs(lock):
    global umqtt_client
    global mqtt_connected

    while True:
        if mqtt_connected:
            async with lock:
                try:
                    umqtt_client.check_msg()
                except:
                    loop.create_task(reconnect(lock))
        await asyncio.sleep(1)
    async with lock:
        umqtt_client.disconnect()


loop = asyncio.get_event_loop()
loop.create_task(check_subs(umqtt_lock))
loop.create_task(check_door_state(umqtt_lock))
loop.run_forever()
