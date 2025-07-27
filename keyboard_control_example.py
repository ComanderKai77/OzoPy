# this example needs getch

import asyncio

from getch import getch

from src.ozopy import OzoPy
from src.emotion import Emotion
from src.led import Led

async def main():
    ozo = OzoPy(input("Please enter the robot address: "))
    await ozo.connect()

    print("Connected")
    print("Press q to quit")
    print("Control the robot with w a s d space")

    while True:
        match getch():
            case "q":
                break
            case "w":
                await ozo.control_motors(speed=10, wait=False)
            case "2":
                await ozo.control_motors(speed=255, wait=False)
            case "s":
                await ozo.control_motors(speed=-10, wait=False)
            case "a":
                await ozo.control_motors(turn_left=255, wait=False)
            case "d":
                await ozo.control_motors(turn_right=255, wait=False)
            case "r":
                await ozo.set_leds(red=255)
            case "g":
                await ozo.set_leds(green=255)
            case "b":
                await ozo.set_leds(blue=255)
            case "e":
                await ozo.play_emotion(Emotion.HAPPY, wait=False)
            case _:
                await ozo.stop_movement()

    await ozo.disconnect()

asyncio.run(main())
