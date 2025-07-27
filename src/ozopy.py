import asyncio
import struct

from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from time import sleep

from .commandType import CommandType
from .emotion import Emotion
from .led import LED 

class OzoPy:
    """Class for controlling an Ozobot-Evo
    """
    MOTOR_CHARACTERISTIC_ID = 19
    DEFAULT_CHARACTERISTIC_ID = 30

    def __init__(self, address: str) -> None:
        """Creates a new instance of OzoPy

        Args:
            address (str): Address of the robot
        """
        self.__client = BleakClient(address, address_type="random")
        
    async def connect(self) -> None:
        """Connect to the robot
        """
        await self.__client.connect()
        self.__motor_characteristic = self.__getCharacteristic(OzoPy.MOTOR_CHARACTERISTIC_ID)
        self.__default_characteristic = self.__getCharacteristic(OzoPy.DEFAULT_CHARACTERISTIC_ID)

        # disable autonomous live
        await self.__sendCommand("780000000000")
        # init motors
        await self.__sendCommand("45", CommandType.MOTOR)
        # init sound
        await self.__sendCommand("03000c6000000c006d2f617564696f2f30313031")

    async def disconnect(self) -> None:
        """Disonnect from the robot
        """
        await self.stop_movement()
        await self.__client.disconnect()

    def is_connected(self) -> bool:
        """Check the connection status

        Returns:
            bool: Return true if the robot is connected
        """
        return self.__client.is_connected

    async def set_leds(self, leds: LED = LED.ALL, red: int = 0, green: int = 0, blue: int = 0) -> None:
        """Control the leds of the robot

        Args:
            leds (LED, optional): LED selector. Defaults to LED.ALL.
            red (int, optional): Red [0:255]. Defaults to 0.
            green (int, optional): Green [0:255]. Defaults to 0.
            blue (int, optional): Blue [0:255]. Defaults to 0.
        """
        command = struct.pack('>BHBBBBB', 0x6e, leds.value, 0, red, green, blue, 0)
        await self.__sendCommand(command)

    async def control_motors(self, speed: int = 0, turn_left: int = 0, turn_right: int = 0, duration: float = 10, wait: bool = True) -> None:
        """Control the motors of the robot

        Args:
            speed (int, optional): Forward / backwards speed [-256:255]. Defaults to 0.
            turn_left (int, optional): Let the robot turn left  with the specified speed [0:255]. Defaults to 0.
            turn_right (int, optional): Let the robot turn right  with the specified speed [0:255]. Defaults to 0.
            duration (float, optional): Specify how many seconds the robot should move. Defaults to 10.
            wait (bool, optional): If true blocks until the movement is finished. Defaults to True.
        """
        speed = min(max(-2**8, speed), 2**8-1)
        turn_left = min(max(0, turn_left), 2**8-1)
        turn_right = min(max(0, turn_right), 2**8-1)
        duration = min(max(0, duration), 2**15)

        if speed < 0:
            speed = speed + 255
            direction = 255
        else:
            direction = 0
        duration_mapped = int(duration * 4)

        command = struct.pack(">BBBBBBBBBBBBBBHBB", 0x68, 0, 0, 0, 0, 0, 0, 0, speed, direction, 0, 0, turn_left, turn_right, duration_mapped, 0, 0)
        await self.__sendCommand(command)

        if wait:
            try:
                sleep(duration)
            except KeyboardInterrupt:
                self.stop_movement()

    async def rotate_left(self, wait: bool = True) -> None:
        """Rotate the robot left

        Args:
            wait (bool, optional): If true blocks until the movement is finished. Defaults to True.
        """
        self.control_motors(turn_left=255, duration=1.25, wait = wait)

    async def rotate_right(self, wait: bool = True) -> None:
        """Rotate the robot right

        Args:
            wait (bool, optional): If true blocks until the movement is finished. Defaults to True.
        """
        self.control_motors(turn_right=255, duration=1.25, wait = wait)

    async def stop_movement(self) -> None:
        """Stop the movement
        """
        await self.__sendCommand("6800015cad020000000000000000ffffffff")

    async def play_emotion(self, emotion: Emotion, wait: bool = True) -> None:
        """Play an emotion

        Args:
            emotion (Emotion): Emotion
            wait (bool, optional): If true blocks until the sound is done playing. Defaults to True.
        """
        match emotion:
            case Emotion.HAPPY:
                await self.__sendCommand("0300006000000c006c000fcefb022f7379737465")
                await self.__sendCommand("0300186000000900303130302e77617600")
                await self.__sendCommand("7e002100aafdb8e4")
            case Emotion.SAD:
                await self.__sendCommand("0300006000000c006c0010cefb022f7379737465")
                await self.__sendCommand("0300186000000900303131302e77617600")
                await self.__sendCommand("7e002100b1a739f3")
            case Emotion.SURPRISED:
                await self.__sendCommand("0300006000000c006c0011cefb022f7379737465")
                await self.__sendCommand("0300186000000900303137302e77617600")
                await self.__sendCommand("7e0021005a7a0e9e")
            case Emotion.LAUGH:
                await self.__sendCommand("0300006000000c006c0012cefb022f7379737465")
                await self.__sendCommand("0300186000000900303235302e77617600")
                await self.__sendCommand("7e002100e3553694")

        if wait:
            try:
                sleep(1)
            except KeyboardInterrupt:
                pass

    def __getCharacteristic(self, handle_id) -> BleakGATTCharacteristic:
        services = self.__client.services
        for service in services:
            for characteristic in service.characteristics:
                if characteristic.handle == handle_id:
                    return characteristic

    async def __sendCommand(self, command: str, command_type: CommandType = CommandType.DEFAULT, wait_for_response: bool = False):
        if (isinstance(command, str)):
            command = bytes.fromhex(command.replace(" ", ""))

        if command_type == CommandType.MOTOR:
            return await self.__client.write_gatt_char(self.__motor_characteristic, command, response = wait_for_response)
        else:
            return await self.__client.write_gatt_char(self.__default_characteristic, command, response = wait_for_response)

    @staticmethod
    async def serach(prefix: str = "Ozo", timeout: int = 10) -> dict[str, str]:
        """Search nearby OzoBots

        Args:
            prefix (str, optional): Prefix for the bluetooth device name. Defaults to "Ozo".
            timeout (int, optional): Search timeout in seconds. Defaults to 10.

        Returns:
            dict[str, str]: Key is the name and value is the address
        """
        devices = await BleakScanner.discover(timeout)

        results = {}
        for device in devices:
            if device.name and device.name.lower().startswith(prefix.lower()):
                results[device.name] = device.address
        
        return results
