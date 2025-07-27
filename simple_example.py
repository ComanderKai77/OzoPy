import asyncio

from src.ozopy import OzoPy
from src.emotion import Emotion
from src.led import LED

async def main():
    # search robots
    robots = await OzoPy.search() # {'Ozobot': 'xx:xx:xx:xx:xx:xx'}
    print(robots)

    # connect to a robot
    robot = OzoPy(robots["OzoBlue"])
    await robot.connect()

    # control the leds of the robot
    await robot.set_leds(leds=LED.ALL, red=0, green=255, blue=0)

    # drive forwards
    await robot.control_motors(speed=10, duration=5)

    # drive slightly left for 5 seconds
    await robot.control_motors(speed=10, turn_left=50, duration=5)

    # play an emotion
    await robot.play_emotion(Emotion.HAPPY)

    # disconnect from the robot
    await robot.disconnect()

asyncio.run(main())
