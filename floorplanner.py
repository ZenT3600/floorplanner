#!/usr/bin/env python3
import sys
from pprint import pprint
from PIL import Image, ImageDraw


def parseRooms(src):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines()]

    ROOM_PARSING = False
    ROOM_H = 0
    ROOM_X = -1
    ROOM_Y = -1
    COUNT_BRACES = 0
    ROOM_NAME = None
    INITIAL_X = 0
    rooms = {}
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == "[":
                COUNT_BRACES += 1
                INITIAL_X = x
                ROOM_H += 1
                ROOM_X = x // 3 if ROOM_X == -1 else ROOM_X # x // 3 to account for 3-char minimum size
                ROOM_Y = y if ROOM_Y == -1 else ROOM_Y
                ROOM_PARSING = True
                continue
            if ROOM_PARSING and char == "]":
                ROOM_PARSING = False
                rooms[ROOM_NAME] = {"x": ROOM_X, "y": ROOM_Y, "w": (x - INITIAL_X) // (3 + ((COUNT_BRACES - 1) * 2)) + 1, "h": ROOM_H}
                # print(COUNT_BRACES, INITIAL_X, x)
                ROOM_X = ROOM_Y = -1
                ROOM_H = INITIAL_X = COUNT_BRACES = 0
                ROOM_NAME = None
                continue
            if ROOM_PARSING and char not in ["[", " ", "]"]:
                ROOM_NAME = char
    return rooms

def drawRooms(rooms):
    for name, data in rooms.items():
        height = 32 * 9 * data["w"]
        width  = 32 * 9 * data["h"]
        
        step_count = 9 * data["w"]
        image = Image.new(mode="RGB", size=(height, width), color=(255,) * 3)
        draw = ImageDraw.Draw(image)
        y_start = 0
        y_end = image.height
        step_size = int(image.width / step_count)
        for x in range(0, image.width, step_size):
            line = ((x, y_start), (x, y_end))
            draw.line(line, fill=(192,) * 3)
        x_start = 0
        x_end = image.width
        for y in range(0, image.height, step_size):
            line = ((x_start, y), (x_end, y))
            draw.line(line, fill=(192,) * 3)
        del draw
        drawRoom(name, image, int(max(height / 32, width / 32)))

def _followCableHorizontal(x, y, lines, endX=None):
    num = None
    try:
        if lines[y][x-1].isnumeric():
            num = int(lines[y][x-1])
        if lines[y][x-1] == "|":
            x -= 0.5
        for i in range(int(x)+1, len(lines[y])+1):
            if lines[y][i] != "-":
                if lines[y][i].isnumeric():
                    num = int(lines[y][i])
                if lines[y][i] == "|":
                    i -= 0.5
                return x, i, num if num else 1 # Start, End, Count
    except IndexError:
        return x, x-1, 1

def _followCableVertical(x, y, lines, startY=None):
    num = None
    try:
        if lines[y-1][x].isnumeric():
            num = int(lines[y-1][x])
        if lines[y-1][x] == "-":
            y -= 0.5
        for i in range(int(y)+1, len(lines)+1):
            if lines[i][x] != "|":
                if len(lines) >= i and lines[i][x].isnumeric():
                    num = int(lines[i][x])
                if lines[i][x] == "-":
                    i -= 0.5
                return y, i-1, num if num else 1 # Start, End, Count
    except IndexError:
        return y, y-1, 1

def parseRoom(src, size):
    with open(src, "r") as f:
        lines = [line.strip().ljust(size) for line in f.readlines()]

    KNOWN_CABLE_POS = []
    room = {"cables": [], "joints": [], "objects": []}
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == ".":
                continue
            if char == "-" and (y, x) not in KNOWN_CABLE_POS:
                cable = _followCableHorizontal(x, y, lines)
                """
                pad = 0
                if len(lines[y]) > cable[1] + 1:
                    if lines[y][cable[1]+1] not in " -|0123456789":
                        pad -= 1
                if cable[2] - 1 >= 0:
                    if lines[y][cable[2]-1] not in " -|0123456789":
                        pad += 1
                """
                for i in range(int(cable[0]), int(cable[1])+1):
                    KNOWN_CABLE_POS.append((y, i))
                room["cables"].append(("h", y, *cable))
                continue
            if char == "|" and (y, x) not in KNOWN_CABLE_POS:
                cable = _followCableVertical(x, y, lines)
                """
                pad = 0
                if len(lines) > cable[1] + 1:
                    if lines[cable[1]+1] not in " -|0123456789":
                        pad -= 1
                if cable[2] - 1 >= 0:
                    if lines[cable[2]-1] not in " -|0123456788":
                        pad += 1
                """
                for i in range(int(cable[0]), int(cable[1])+2):
                    KNOWN_CABLE_POS.append((i, x))
                room["cables"].append(("v", x, *cable))
                continue
            if char in "^V><":
                joint = (char, x, y)
                room["joints"].append(joint)
            if char not in " |-^V><" and not char.isnumeric():
                room["objects"].append((char, x, y))
    return room

# Compile Coordinates Base
def cc(n):
    return n * 32 + (32 / 2)

# Compile Coordinates Plus
def ccp(n):
    return cc(n) + 16

# ... Minus
def ccm(n):
    return cc(n) - 16

def drawRoom(name, image, size):
    room = parseRoom(name + ".room", size)
    print(room)
    draw = ImageDraw.Draw(image)
    for cable in room["cables"]:
        if cable[0] == "h":
            for i in range(cable[4]):
                draw.line((ccm(cable[2]), cc(cable[1]), ccp(cable[3]), cc(cable[1])), fill=192 if i % 2 == 0 else (255,) * 3, width=2 * (cable[4] - i))
        if cable[0] == "v":
            for i in range(cable[4]):
                draw.line((cc(cable[1]), ccm(cable[2]), cc(cable[1]), ccp(cable[3])), fill=192 if i % 2 == 0 else (255,) * 3, width=2 * (cable[4] - i))

    for joint in room["joints"]:
        if joint[0] == "V":
            draw.line((ccp(joint[1]), cc(joint[2]) - 32, cc(joint[1]), ccp(joint[2])), fill=192, width=2)
        elif joint[0] == "^":
            draw.line((cc(joint[1]), cc(joint[2]), ccm(joint[1]), cc(joint[2]) + 32), fill=192, width=2)
        elif joint[0] == ">":
            draw.line((cc(joint[1]) - 32, ccm(joint[2]), ccp(joint[1]), cc(joint[2])), fill=192, width=2)
        else:
            draw.line((cc(joint[1]) - 32, cc(joint[2]), cc(joint[1]), ccp(joint[2])), fill=192, width=2)

    for obj in room["objects"]:
        draw.rectangle((cc(obj[1]) - 16, cc(obj[2]) - 16, cc(obj[1]) + 16, cc(obj[2]) + 16), outline=(64,) * 3, width=3)
    image.save(name + ".png")
        
def main():
    assert len(sys.argv) == 2
    rooms = parseRooms(sys.argv[1])
    print(rooms)
    drawRooms(rooms)


if __name__ == "__main__":
    main()
