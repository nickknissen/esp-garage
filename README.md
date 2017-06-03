# esp-garage

Garage door controller using an ESP8266 and MQTT


### Summary:
The ESP266 operates as a MQTT client listening for an 'open' or 'close' message, and continuously broadcasting the garage door status ('open' or 'closed'). Pictures of it in action: http://imgur.com/a/nxKxK

![Photo](/img/photo.jpg)

### Description:
This is a MQTT client for controlling a garage door opener via a 5V relay. Exact hardware required will depend on the garage door openner installed. For mine, shorting two wires from the garage door opener briefly causes the door to toggle. This project uses [micropython for the ESP8266](https://github.com/micropython/micropython/tree/master/esp8266), with three additional libraries:

* uasyncio and umqtt from [micropython-lib](https://github.com/micropython/micropython-lib)

* asyn from [micropython-async](https://github.com/peterhinch/micropython-async)

In this configuration, the ESP8266 is intended to listen for messages over 1 MQTT topic: `home/garage/door/control`. This topic is customizable by setting the appropriate variable at the beginning of the `esp_garage.py` file.

Valid messages for this control topic are `open` and `close`. Anything else will be ignored.

Example:

    $ mosquitto_pub -h 10.1.1.1 -t home/garage/door/control -m 'open'

** Caution ** Be mindful of the retain flag when publishing commands to the esp.. if the retain flag is set and the esp is offline for whatever reason, this will cause the door to toggle when the esp comes back online.. which might be when you least expect it! I recommend publishing messages with the retain flag set to false.

`home/garage/door/status` is the topic where the device will send either `open` or `closed`, indicating whether or not the garage door is opened. This status is determined by using the HC-SR04 ultrasonic distance sensor. The interval for reporting status over MQTT is configurable via a variable at the top of the `esp_garage.py` file.

Example:

    $ mosquitto_sub -h 10.1.1.1 -t home/garage/door/status
    open
    closed
    closed

### Installation:

- [Build the esp-open-sdk](https://github.com/pfalcon/esp-open-sdk).

- Download micropython-lib, micropython-async, and micropython from their respective project pages.

- [Include uasyncio, umqtt, and asyn modules as frozen modules in micropython](https://learn.adafruit.com/micropython-basics-loading-modules/frozen-modules)
  - Note: Building uasyncio as frozen bytecode is no longer necessary in Micropython 1.9, since it is included by default!
  
- Also include [micropython-async](https://github.com/peterhinch/micropython-async) (asyn.py) as a frozen module. Note: if you run out of space, consider removing the web_repl applications, or prune something else that is not a requirement here.

- Edit `app.py` in this project to include your MQTT broker IP, along with any other settings you would like to modify.

- Install `main.py` and `boot.py` from the [esp-bootstrap](https://github.com/craftyguy/esp-bootstrap) project. Also pay attention to instructions for creating the `secrets.py` file, which also needs to be installed on the device.

- Build micropython. I suggest including the files in this project under `esp8266/scripts` in your micropython directory so you don't have to manually copy these files to the device

  - Hint: You'll need python2 env. for esptool.py to run successfully at the end of the build..


- [Flash the ESP8266 using esptool](https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/intro.html#intro), using your fresh firmware-combined.bin image of course!

Power on device and send it a command! Here's an example with [Mosquitto](http://mosquitto.org/):

    mosquitto_pub -h 10.1.1.1 -t home/garage/door/control -m 'open'


### Hardware BOM:

![Schematic](/img/schematic.png)

1x Wemos D1 Mini ESP8266

2x 100k resistors

1x 22k resistor

1x 10k resistor

1x 100 or 200uF decoupling capacitor (which was needed to stabilize 5V VCC to the Wemos D1)

1x HC-SR04 ultrasonic sensor

1x Keyes_sr1y 5V relay

Power was provided by a sacrificial USB cable and a 5V usb wall wart.

A schematic is included in the project (schematic.png).
