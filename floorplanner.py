#!/usr/bin/env python3
import sys
from pprint import pprint
from typing import List
from PIL import Image, ImageDraw


class Cable:
    def __init__(
        self, room_uid: str, size: str, start: List[int], end: List[int], vertical: bool
    ):
        self.room_uid = int(room_uid)
        self.size = int(size)
        self.start = start
        self.end = end
        self.is_vertical = vertical


class Box:
    def __init__(self, room_uid: str, name: str, anchor: List[int], color: List[int]):
        self.room_uid = int(room_uid)
        self.name = name
        self.anchor = anchor
        self.color = color


class Door:
    def __init__(self, room_uid: str, to_uid: str, on: str, at: str):
        self.room_uid = int(room_uid)
        self.to_uid = int(to_uid) if to_uid else None
        self.on = on
        self.at = int(at)


class Room:
    def __init__(
        self,
        uid: str,
        width: str,
        height: str,
        anchor: List[int],
        boxes: List[Box],
        cables: List[Cable],
        doors: List[Door],
    ):
        self.uid = int(uid)
        self.width = int(width)
        self.height = int(height)
        self.anchor = anchor
        self.boxes = boxes
        self.cables = cables
        self.doors = doors


def parseRooms(src):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    ROOMS = []
    for line in lines:
        if line.startswith("new room"):
            if not all(
                [keyword in line for keyword in ["id", "width", "height", "anchor"]]
            ):
                assert False, 'Invalid room creation syntax: "' + line + '"'
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            BOXES = parseBoxesForRoom(src, zipped["id"])
            CABLES = parseCablesForRoom(src, zipped["id"])
            DOORS = parseDoorsForRoom(src, zipped["id"])
            ROOMS.append(
                Room(
                    zipped["id"],
                    zipped["width"],
                    zipped["height"],
                    [int(n) for n in zipped["anchor"].split(",")],
                    BOXES,
                    CABLES,
                    DOORS,
                )
            )

    return ROOMS


def parseBoxesForRoom(src, room):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    BOXES = []
    for line in lines:
        if line.startswith("new box"):
            if not all([keyword in line for keyword in ["room", "name", "anchor"]]):
                assert False, 'Invalid box creation syntax: "' + line + '"'
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            if int(zipped["room"]) != int(room):
                continue
            if not "color" in zipped:
                zipped["color"] = "120,120,120"
            zipped["color"] = [int(n) for n in zipped["color"].split(",")]
            BOXES.append(
                Box(
                    zipped["room"],
                    zipped["name"],
                    [int(n) for n in zipped["anchor"].split(",")],
                    zipped["color"],
                )
            )

    return BOXES


def parseDoorsForRoom(src, room):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    DOORS = []
    for line in lines:
        if line.startswith("new door"):
            if not all([keyword in line for keyword in ["room", "on", "at"]]):
                assert False, 'Invalid door creation syntax: "' + line + '"'
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            if int(zipped["room"]) != int(room) and int(zipped["to"]) != int(room):
                continue
            if zipped["on"] not in ["left", "right", "top", "bottom"]:
                assert False, 'Door can only be on left, right, top or bottom'
            if "to" not in zipped:
                assert False, 'Door leads nowhere'
            opposite = ""
            if zipped["on"] in ["left", "right"]:
                opposite = "right" if zipped["on"] == "left" else "left"
            else:
                opposite = "top" if zipped["on"] == "bottom" else "bottom"
            DOORS.append(
                Door(
                    zipped["room"],
                    zipped["to"],
                    zipped["on"],
                    zipped["at"]
                ) if int(zipped["room"]) == int(room) else Door(
                    zipped["to"],
                    zipped["room"],
                    opposite,
                    zipped["at"]
                )
            )

    return DOORS


def parseCablesForRoom(src, room):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    CABLES = []
    for line in lines:
        if line.startswith("new cable"):
            if not all(
                [keyword in line for keyword in ["room", "type", "size", "from", "to"]]
            ):
                assert False, 'Invalid cable creation syntax: "' + line + '"'
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            if zipped["type"] not in ["V", "H"]:
                assert False, "Cable type can only be V or H"
            if zipped["type"] == "V":
                if [int(n) for n in zipped["from"].split(",")][0] != [
                    int(n) for n in zipped["to"].split(",")
                ][0]:
                    assert False, "Malformed vertical cable"
            else:
                if [int(n) for n in zipped["from"].split(",")][1] != [
                    int(n) for n in zipped["to"].split(",")
                ][1]:
                    assert False, "Malformed horizontal cable"
            if int(zipped["size"]) <= 0:
                assert False, "Invalid cable size"
            if int(zipped["room"]) != int(room):
                continue
            CABLES.append(
                Cable(
                    zipped["room"],
                    zipped["size"],
                    [int(n) for n in zipped["from"].split(",")],
                    [int(n) for n in zipped["to"].split(",")],
                    zipped["type"] == "V",
                )
            )

    return CABLES


def drawRooms(rooms):
    for room in rooms:
        drawRoom(room)

    glueTogether(rooms)


def glueTogether(rooms):
    maxX = -1
    maxXwidth = -1
    maxY = -1
    maxYheight = -1
    for room in rooms:
        if room.anchor[0] > maxX:
            maxX = room.anchor[0]
            maxXwidth = room.width
        if room.anchor[1] > maxY:
            maxY = room.anchor[1]
            maxYheight = room.height

    image = Image.new(mode="RGB", size=((maxX + maxXwidth) * 9 * 32, (maxY + maxYheight) * 9 * 32), color=(255,) * 3)
    for room in rooms:
        image.paste(Image.open(str(room.uid) + ".png", "r"), (room.anchor[0] * 32 * 9, room.anchor[1] * 32 * 9))
    image.save("full.png")


def drawRoom(room):
    # inverted because of PIL's coordinate system
    height = 32 * 9 * room.width
    width = 32 * 9 * room.height

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
    draw.line(((0, 0), (height, 0)), fill=0, width=3)
    draw.line(((0, 0), (0, width)), fill=0, width=3)
    draw.line(((height, width), (height, 0)), fill=0, width=3)
    draw.line(((height, width), (0, width)), fill=0, width=3)

    for box in room.boxes:
        a = box.anchor
        draw.rectangle(
            (a[0] * 32, a[1] * 32, a[0] * 32 + 32, a[1] * 32 + 32),
            fill=tuple(box.color),
            outline=(0),
        )
        draw.text((a[0] * 32 + 4, a[1] * 32 + 12), box.name, (255,) * 3)
    for cable in room.cables:
        s = cable.start
        e = cable.end
        if cable.is_vertical:
            for i in range(1, cable.size + 1):
                draw.line(
                    (
                        (s[0] * 32 + 4 * i, s[1] * 32 + 4),
                        (e[0] * 32 + 4 * i, e[1] * 32 + 4),
                    ),
                    fill=(255, 0 if i == 1 else 75, 0),
                    width=1,
                )
        else:
            for i in range(1, cable.size + 1):
                draw.line(
                    (
                        (s[0] * 32 + 4, s[1] * 32 + 4 * i),
                        (e[0] * 32 + 4, e[1] * 32 + 4 * i),
                    ),
                    fill=(255, 0 if i == 1 else 75, 0),
                    width=1,
                )
    for door in room.doors:
        o = door.on
        a = door.at
        if door.on == "left":
            draw.line(
                (
                    (0, (a - 1) * 32),
                    (0, (a + 1) * 32),
                ),
                fill=(220,) * 3,
                width=5,
            )
        elif door.on == "right":
            draw.line(
                (
                    (width, (a - 1) * 32),
                    (width, (a + 1) * 32),
                ),
                fill=(220,) * 3,
                width=5,
            )
        elif door.on == "top":
            draw.line(
                (
                    ((a - 1) * 32, 0),
                    ((a + 1) * 32, 0),
                ),
                fill=(220,) * 3,
                width=5,
            )
        elif door.on == "bottom":
            draw.line(
                (
                    ((a - 1) * 32, height),
                    ((a + 1) * 32, height),
                ),
                fill=(220,) * 3,
                width=5,
            )

    image.save(str(room.uid) + ".png")


def main():
    assert len(sys.argv) == 2
    rooms = parseRooms(sys.argv[1])
    drawRooms(rooms)


if __name__ == "__main__":
    main()
