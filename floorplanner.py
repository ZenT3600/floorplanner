#!/usr/bin/env python3
import sys
from PIL import Image, ImageDraw


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
        size=((maxX + maxXwidth) * 9 * 32, (maxY + maxYheight) * 9 * 32),
        color=(255,) * 3,
    )
    for room in rooms:
        image.paste(
            Image.open(str(room.uid) + ".png", "r"),
            (room.anchor[0] * 32 * 9, room.anchor[1] * 32 * 9),
        )
    draw = ImageDraw.Draw(image)
    for room in rooms:
        width = room.width * 32 * 9
        height = room.height * 32 * 9
        x = room.anchor[0] * 32 * 9
        y = room.anchor[1] * 32 * 9
        for door in room.doors:
            o = door.on
            a = door.at
            if door.on == "left":
                draw.line(
                    (
                        (x, (a - 1) * 32),
                        (x, (a + 1) * 32),
                    ),
                    fill=(220,) * 3,
                    width=6,
                )
            elif door.on == "right":
                draw.line(
                    (
                        (width + x, (a - 1) * 32),
                        (width + x, (a + 1) * 32),
                    ),
                    fill=(220,) * 3,
                    width=6,
                )
            elif door.on == "top":
                draw.line(
                    (
                        ((a - 1) * 32, y),
                        ((a + 1) * 32, y),
                    ),
                    fill=(220,) * 3,
                    width=6,
                )
            elif door.on == "bottom":
                draw.line(
                    (
                        ((a - 1) * 32, height + y),
                        ((a + 1) * 32, height + y),
                    ),
                    fill=(220,) * 3,
                    width=6,
                )
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
    assert len(sys.argv) == 2, "Invalid arguments length"
    rooms = parseRooms(sys.argv[1])
    drawRooms(rooms)


if __name__ == "__main__":
    main()
