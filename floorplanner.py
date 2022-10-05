#!/usr/bin/env python3
import sys
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
        drawRoom(name, image)

def _followCableHorizontal(x, y, lines, endX=None):
    if lines[y][x-1].isnumeric():
        x -= 1
        num = int(lines[y][x])
    if not endX:
        endX = len(lines[y]) - 1
        while not lines[y][endX] == "-":
            endX -= 1
    for i in range(x, endX+1):
        if lines[y][i] == "-" or lines[y][i].isnumeric():
            if i == endX:
                if lines[y][endX+1].isnumeric():
                    endX += 1
                    num = int(lines[y][endX])
                return x, endX, num if num else 1 # Start, End, Count
        else:
            #This means we picked the wrong cable
            return _followCableHorizontal(x, y, lines, endX=i-1)

def _followCableVertical(x, y, lines, endY=None):
    if lines[y-1][x].isnumeric():
        y -= 1
        num = int(lines[y][x])
    if not endY:
        endY = len(lines) - 1
        while not lines[endY][x] == "|":
            endY -= 1
    for i in range(y, endY+1):
        if lines[i][x] == "|" or lines[i][x].isnumeric():
            if i == endY:
                if lines[endY+1][x].isnumeric():
                    endY += 1
                    num = int(lines[endY][x])
                return y, endY, num if num else 1 # Start, End, Count
        else:
            #This means we picked the wrong cable
            return _followCableVertical(x, y, lines, endX=i-1)

def parseRoom(src):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines()]

    KNOWN_CABLE_POS = []
    room = []
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == "-" and (y, x) not in KNOWN_CABLE_POS:
                cable = _followCableHorizontal(x, y, lines)
                for i in range(cable[0], cable[1]+1):
                    KNOWN_CABLE_POS.append((y, i))
                room.append(("cable-h", y, *cable))
                continue
            if char == "|" and (y, x) not in KNOWN_CABLE_POS:
                cable = _followCableVertical(x, y, lines)
                for i in range(cable[0], cable[1]+1):
                    KNOWN_CABLE_POS.append((i, x))
                room.append(("cable-v", x, *cable))
                continue
    return room

def drawRoom(name, image):
    room = parseRoom(name + ".room")
    print(room)
    image.save(name + ".png")
        
def main():
    assert len(sys.argv) == 2
    rooms = parseRooms(sys.argv[1])
    print(rooms)
    drawRooms(rooms)


if __name__ == "__main__":
    main()
