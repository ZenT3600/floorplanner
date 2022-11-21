#!/usr/bin/env python3
import sys
from pprint import pprint
from typing import List
from PIL import Image, ImageDraw


class Room:
    def __init__(self, uid: str, width: str, height: str, anchor: List[int]):
        self.uid = int(uid)
        self.width = int(width)
        self.height = int(height)
        self.anchor = anchor

def parseRooms(src):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines()]

    ROOMS = []
    for line in lines:
        if line.startswith("new room"):
            if not all([keyword in line for keyword in ["id", "width", "height", "anchor"]]):
                assert False, "Invalid room creation syntax"
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            ROOMS.append(Room(zipped["id"], zipped["width"], zipped["height"], [int(n) for n in zipped["anchor"].split(",")]))
            continue

    return ROOMS

def drawRooms(rooms):
    for room in rooms:
        # inverted because of PIL's coordinate system
        height = 32 * 9 * room.width
        width  = 32 * 9 * room.height
        
        step_count = height / 32
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

        draw.line(((0, 0),(height, 0)), fill=0, width=3)
        draw.line(((0, 0),(0, width)), fill=0, width=3)
        draw.line(((height, width),(height, 0)), fill=0, width=3)
        draw.line(((height, width),(0, width)), fill=0, width=3)
        del draw

        drawRoom(room, image)

def drawRoom(room, image):
    draw = ImageDraw.Draw(image)
    image.save(str(room.uid) + ".png")
        
def main():
    assert len(sys.argv) == 2
    rooms = parseRooms(sys.argv[1])
    drawRooms(rooms)


if __name__ == "__main__":
    main()
