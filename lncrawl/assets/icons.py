# -*- coding: utf-8 -*-

from ..utils.platforms import Platform

_rich_support = not Platform.ci


class TextIcons:
    LEDGER = "[#]"
    CLOVER = "*"
    LINK = "-"
    PRAY = "-"
    ERROR = "!"
    PACKAGE = "$"
    SOUND = "<<"
    SPARKLE = "*"
    INFO = ">"
    RIGHT_ARROW = "->"
    CHECK = "Y"
    CROSS = "x"


class RichIcons(TextIcons):
    LEDGER = ":ledger:"
    CLOVER = ":four_leaf_clover:"
    LINK = ":link:"
    PRAY = ":pray:"
    ERROR = ":exclamation:"
    PACKAGE = ":package:"
    SOUND = ":loud_sound:"
    SPARKLE = ":sparkles:"
    INFO = ":light_bulb:"
    RIGHT_ARROW = ":right_arrow:"
    CHECK = ":heavy_check_mark:"
    CROSS = ":cross_mark:"


Icons = RichIcons if _rich_support else TextIcons
