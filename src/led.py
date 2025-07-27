from enum import Flag

class LED(Flag):
    """Bit flags for each led
    """
    TOP = 1
    LEFT = 2
    CENTER_LEFT = 4
    CENTER = 8
    CENTER_RIGHT = 16
    RIGHT = 32
    BACK = 128
    ALL = 255
