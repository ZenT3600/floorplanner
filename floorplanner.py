#!/usr/bin/env python3
import sys
from PIL import Image, ImageDraw


class Const:
    WHITE = (255,) * 3
    BLACK = (0,) * 3
    GRAY_NORMAL = (128,) * 3
    GRAY_LIGHT = (200,) * 3
    GRAY_DARK = (75,) * 3
    RED_NORMAL = (255, 0, 0)
    RED_DARK = (75, 0, 0)
    CELL_SIZE = 32
    ROOM_SIZE = 9


class Cable:
    def __init__(self, room_uid, size, start, end, vertical):
        self.room_uid = int(room_uid)
        self.size = int(size)
        self.start = start
        self.end = end
        self.is_vertical = vertical


class Box:
    def __init__(self, room_uid, name, anchor, color):
        self.room_uid = int(room_uid)
        self.name = name
        self.anchor = anchor
        self.color = color


class Door:
    def __init__(self, room_uid, on, at):
        self.room_uid = int(room_uid)
        self.on = on
        self.at = int(at)


class Room:
    def __init__(
        self,
        uid,
        width,
        height,
        anchor,
        boxes,
        cables,
        doors,
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


def parseAnyForRoom(src, room, start, required, lambda_checks, lambda_generate):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    OBJS = []
    for line in lines:
        if line.startswith(start):
            if not all([keyword in line for keyword in required]):
                assert False, 'Invalid creation syntax: "' + line + '"'
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            for check in lambda_checks:
                assert check(zipped), 'Check failed: "' + check + '"'
            if int(zipped["room"]) != int(room):
                continue
            OBJS.append(lambda_generate(zipped))

    return OBJS


def parseBoxesForRoom(src, room):
    start = "new box"
    required = ["room", "name", "anchor"]

    def correct_color(zipped):
        if not "color" in zipped:
            zipped["color"] = "120,120,120"
        zipped["color"] = [int(n) for n in zipped["color"].split(",")]
        return True

    checks = [
        correct_color,
    ]

    def generate(zipped):
        return Box(
            zipped["room"],
            zipped["name"],
            [int(n) for n in zipped["anchor"].split(",")],
            zipped["color"],
        )

    return parseAnyForRoom(src, room, start, required, checks, generate)


def parseDoorsForRoom(src, room):
    start = "new door"
    required = ["room", "on", "at"]

    def validate_positions(zipped):
        if zipped["on"] not in ["left", "right", "top", "bottom"]:
            return False
        return True

    checks = [
        validate_positions,
    ]

    def generate(zipped):
        return Door(zipped["room"], zipped["on"], zipped["at"])

    return parseAnyForRoom(src, room, start, required, checks, generate)


def parseCablesForRoom(src, room):
    start = "new cable"
    required = ["room", "type", "size", "from", "to"]

    def validate_type(zipped):
        if zipped["type"] not in ["V", "H"]:
            return False
        return True

    def validate_malformed_cables(zipped):
        if zipped["type"] == "V":
            if [int(n) for n in zipped["from"].split(",")][0] != [
                int(n) for n in zipped["to"].split(",")
            ][0]:
                return False
        else:
            if [int(n) for n in zipped["from"].split(",")][1] != [
                int(n) for n in zipped["to"].split(",")
            ][1]:
                return False
        return True

    def validate_size(zipped):
        if int(zipped["size"]) <= 0:
            return False
        return True

    checks = [validate_type, validate_malformed_cables, validate_size]

    def generate(zipped):
        return Cable(
            zipped["room"],
            zipped["size"],
            [int(n) for n in zipped["from"].split(",")],
            [int(n) for n in zipped["to"].split(",")],
            zipped["type"] == "V",
        )

    return parseAnyForRoom(src, room, start, required, checks, generate)


def drawRooms(rooms):
    for room in rooms:
        drawRoom(room)
    drawFullRoom(rooms)


def drawFullRoom(rooms):
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

    image = Image.new(
        mode="RGB",
        size=((maxX + maxXwidth) * Const.ROOM_SIZE * Const.CELL_SIZE, (maxY + maxYheight) * Const.ROOM_SIZE * Const.CELL_SIZE),
        color=Const.WHITE,
    )
    for room in rooms:
        image.paste(
            Image.open(str(room.uid) + ".png", "r"),
            (room.anchor[0] * Const.ROOM_SIZE * Const.CELL_SIZE, room.anchor[1] * Const.ROOM_SIZE * Const.CELL_SIZE),
        )
    draw = ImageDraw.Draw(image)
    for room in rooms:
        width = room.width * Const.ROOM_SIZE * Const.CELL_SIZE
        height = room.height * Const.ROOM_SIZE * Const.CELL_SIZE
        x = room.anchor[0] * Const.ROOM_SIZE * Const.CELL_SIZE
        y = room.anchor[1] * Const.ROOM_SIZE * Const.CELL_SIZE
        for door in room.doors:
            o = door.on
            a = door.at
            if door.on == "left":
                draw.line(
                    (
                        (x, (a - 1) * Const.CELL_SIZE),
                        (x, (a + 1) * Const.CELL_SIZE),
                    ),
                    fill=Const.GRAY_LIGHT,
                    width=6,
                )
            elif door.on == "right":
                draw.line(
                    (
                        (width + x, (a - 1) * Const.CELL_SIZE),
                        (width + x, (a + 1) * Const.CELL_SIZE),
                    ),
                    fill=Const.GRAY_LIGHT,
                    width=6,
                )
            elif door.on == "top":
                draw.line(
                    (
                        ((a - 1) * Const.CELL_SIZE, y),
                        ((a + 1) * Const.CELL_SIZE, y),
                    ),
                    fill=Const.GRAY_LIGHT,
                    width=6,
                )
            elif door.on == "bottom":
                draw.line(
                    (
                        ((a - 1) * Const.CELL_SIZE, height + y),
                        ((a + 1) * Const.CELL_SIZE, height + y),
                    ),
                    fill=Const.GRAY_LIGHT,
                    width=6,
                )
    image.save("full.png")


def drawRoom(room):
    # inverted because of PIL's coordinate system
    height = room.width * Const.ROOM_SIZE * Const.CELL_SIZE
    width = room.height * Const.ROOM_SIZE * Const.CELL_SIZE

    step_count = height / Const.CELL_SIZE
    image = Image.new(mode="RGB", size=(height, width), color=Const.WHITE)
    draw = ImageDraw.Draw(image)
    y_start = 0
    y_end = image.height
    step_size = int(image.width / step_count)
    for x in range(0, image.width, step_size):
        line = ((x, y_start), (x, y_end))
        draw.line(line, fill=Const.GRAY_LIGHT)
    x_start = 0
    x_end = image.width
    for y in range(0, image.height, step_size):
        line = ((x_start, y), (x_end, y))
        draw.line(line, fill=Const.GRAY_LIGHT)
    draw.line(((0, 0), (height, 0)), fill=0, width=3)
    draw.line(((0, 0), (0, width)), fill=0, width=3)
    draw.line(((height, width), (height, 0)), fill=0, width=3)
    draw.line(((height, width), (0, width)), fill=0, width=3)

    for box in room.boxes:
        a = box.anchor
        draw.rectangle(
            (a[0] * Const.CELL_SIZE, a[1] * Const.CELL_SIZE, a[0] * Const.CELL_SIZE + Const.CELL_SIZE, a[1] * Const.CELL_SIZE + Const.CELL_SIZE),
            fill=tuple(box.color),
            outline=(0),
        )
        draw.text((a[0] * Const.CELL_SIZE + 4, a[1] * Const.CELL_SIZE + 12), box.name, Const.WHITE)
    for cable in room.cables:
        s = cable.start
        e = cable.end
        if cable.is_vertical:
            for i in range(1, cable.size + 1):
                draw.line(
                    (
                        (s[0] * Const.CELL_SIZE + 4 * i, s[1] * Const.CELL_SIZE + 4),
                        (e[0] * Const.CELL_SIZE + 4 * i, e[1] * Const.CELL_SIZE + 4),
                    ),
                    fill=Const.RED_NORMAL if i == 1 else Const.RED_DARK,
                    width=1,
                )
        else:
            for i in range(1, cable.size + 1):
                draw.line(
                    (
                        (s[0] * Const.CELL_SIZE + 4, s[1] * Const.CELL_SIZE + 4 * i),
                        (e[0] * Const.CELL_SIZE + 4, e[1] * Const.CELL_SIZE + 4 * i),
                    ),
                    fill=Const.RED_NORMAL if i == 1 else Const.RED_DARK,
                    width=1,
                )
    for door in room.doors:
        o = door.on
        a = door.at
        if door.on == "left":
            draw.line(
                (
                    (0, (a - 1) * Const.CELL_SIZE),
                    (0, (a + 1) * Const.CELL_SIZE),
                ),
                fill=Const.GRAY_LIGHT,
                width=5,
            )
        elif door.on == "right":
            draw.line(
                (
                    (width, (a - 1) * Const.CELL_SIZE),
                    (width, (a + 1) * Const.CELL_SIZE),
                ),
                fill=Const.GRAY_LIGHT,
                width=5,
            )
        elif door.on == "top":
            draw.line(
                (
                    ((a - 1) * Const.CELL_SIZE, 0),
                    ((a + 1) * Const.CELL_SIZE, 0),
                ),
                fill=Const.GRAY_LIGHT,
                width=5,
            )
        elif door.on == "bottom":
            draw.line(
                (
                    ((a - 1) * Const.CELL_SIZE, height),
                    ((a + 1) * Const.CELL_SIZE, height),
                ),
                fill=Const.GRAY_LIGHT,
                width=5,
            )

    image.save(str(room.uid) + ".png")


def main():
    assert len(sys.argv) == 2, "Invalid arguments length"
    rooms = parseRooms(sys.argv[1])
    drawRooms(rooms)


if __name__ == "__main__":
    main()
