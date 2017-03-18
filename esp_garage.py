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
DOOR_TOGGLE_PIN = 15            # Pick a pin with internal pull-down
TRIG_PIN = 16
ECHO_PIN = 12
CHECK_DOOR_INTERVAL = .1         # Interval to check door status, in minutes
DOOR_OPEN_DISTANCE = .5         # Distance (m) from sensor to door when open
DOOR_CLOSE_DISTANCE = 3         # Distance (m) from sensor to floor when open
SPEED_OF_SOUND = 340            # Speed of sound (m/s)

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

    echo = machine.Pin(ECHO_PIN, machine.Pin.IN)
    trig = machine.Pin(TRIG_PIN, machine.Pin.OUT)
    distance = 0.0
    state = 'closed'
    await asyncio.sleep(5)

    while True:
        state = b'closed'
        # HC-SR04 is triggered by a 10us pulse on 'trig' pin
        trig.low()
        utime.sleep_us(10)
        trig.high()
        utime.sleep_us(10)
        trig.low()
        # echo pin will be high for a duration (is us) indicating distance.
        # Using a timeout of 38ms, which I believe indicates the max distance
        # this sensor supports
        try:
            pulse_width = machine.time_pulse_us(echo, 1)
        except:
            pass
        print("pulse_width: %i" % pulse_width)
        # If no pulse measured before timeout, then width is -2
        if pulse_width > 0:
            # Convert to seconds
            # Hint: div by 2 because the signal reflected off of something
            distance = (pulse_width / 2.0) * 29
            print("Measured distance of %f cm" % distance)
            if (100 * distance) <= DOOR_OPEN_DISTANCE:
                state = b'open'
            # publish state
            async with lock:
                try:
                    umqtt_client.publish(STATUS_TOPIC, state)
                except:
                    loop.create_task(reconnect(lock))
        await asyncio.sleep(CHECK_DOOR_INTERVAL * 60)


#  sub_cb: callback for mqtt client subscriptions
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

# main: start mqtt subscribe, and periodically check for new messages
async def check_subs():
    global umqtt_client

    umqtt_client.DEBUG = True
    umqtt_client.set_callback(sub_cb)

    if not umqtt_client.connect(clean_session=True):
        print("Connected to MQTT broker: %s" % MQTT_SERVER)
        umqtt_client.subscribe(CONTROL_TOPIC)
    while True:
        # non-blocking check for messages to allow other coros to do their thang
        umqtt_client.check_msg()
        await asyncio.sleep(1)
    umqtt_client.disconnect()



loop = asyncio.get_event_loop()
loop.create_task(check_subs(mqtt_lock))
loop.create_task(check_door_state(mqtt_lock))
loop.run_forever()
