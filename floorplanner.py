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


class Variable:
    def __init__(self, name, value, linen):
        self.name = name
        self.value = value
        self.linen = linen


class Cable:
    def __init__(self, room_uid, size, start, end, vertical):
        self.room_uid = room_uid
        self.size = int(size)
        self.start = start
        self.end = end
        self.is_vertical = vertical


class Box:
    def __init__(self, room_uid, name, anchor, color):
        self.room_uid = room_uid
        self.name = name
        self.anchor = anchor
        self.color = color


class Door:
    def __init__(self, room_uid, on, at):
        self.room_uid = room_uid
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
        self.uid = uid
        self.width = int(width)
        self.height = int(height)
        self.anchor = anchor
        self.boxes = boxes if boxes else []
        self.cables = cables if cables else []
        self.doors = doors if doors else []


def parseMacros(src):
    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    macroless_src = []
    macros = {}
    current_macro = None
    for line in lines:
        if line.startswith("new macro"):
            if not "equals" in line:
                assert False, "Invalid macro syntax"
            current_macro = line.split(" ")[2]
            if current_macro == "new":
                assert False, 'Macro cannot be called "new"'
            keywords = line.split(" ")[1::2]
            values = line.split(" ")[2::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            if "params" in zipped:
                macros[current_macro] = {
                    "lines": [],
                    "params": zipped["params"].split(",")
                    if "," in zipped["params"]
                    else [
                        zipped["params"],
                    ],
                }
            else:
                macros[current_macro] = {"lines": [], "params": []}
            continue
        if line.startswith("stop macro " + str(current_macro)):
            current_macro = ""
            continue
        if not current_macro:
            macroless_src.append(line)
        else:
            macros[current_macro]["lines"].append(line)

    macroed_src = []
    for line in macroless_src:
        for k, v in macros.items():
            if line.startswith(k):
                keywords = line.split(" ")[1::2]
                values = line.split(" ")[2::2]
                zipped = {k: v for k, v in zip(keywords, values)}
                line = "\n".join(v["lines"])
                for p in v["params"]:
                    line = line.replace("@" + p + "@", zipped[p])
        macroed_src.append(line + "\n")

    return macroed_src


def parseLoops(lines):
    looped_src = []
    current_index = None
    current_times = 0
    done = False
    met_loops = 0
    i = 0
    while not done:
        if i >= len(lines):
            done = True
            continue
        line = lines[i]
        if current_index:
            l = 1
            for j in range(current_times):
                l = 1
                met_loops = 1
                while True:
                    loop_line = lines[i + l]
                    if loop_line.startswith("new loop"):
                        met_loops += 1
                    if loop_line.startswith("stop loop"):
                        met_loops -= 1
                    if loop_line.startswith("stop loop") and met_loops <= 1:
                        looped_src.append(loop_line)
                        break
                    replaced = (
                        loop_line.replace("@" + current_index + "@", str(j)) + "\n"
                    )
                    looped_src.append(replaced)
                    l += 1
            for k in range(i + l + 1, len(lines)):
                looped_src.append(lines[k])
            break
        if line.startswith("new loop"):
            if not all([keyword in line for keyword in ["times", "index", "equals"]]):
                assert False, "Invalid loop syntax"
            met_loops = 1
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            if int(zipped["times"]) < 0:
                assert False, "Loop cannot run less than 0 times"
            current_index = zipped["index"]
            current_times = int(zipped["times"])
        elif line.startswith("stop loop"):
            current_index = None
            i += 1
        else:
            looped_src.append(line)
            i += 1

    return looped_src


def parseConditionals(lines):
    i = 0
    done = False
    keep_if = False
    inside_if = False
    inside_else = False
    conditioned_src = []
    met_conditionals = 0
    while not done:
        if i >= len(lines):
            done = True
            continue
        line = lines[i]
        if inside_if:
            if keep_if:
                l = 1
                while True:
                    if lines[i + l].startswith("new if"):
                        met_conditionals += 1
                    if lines[i + l].startswith("stop if"):
                        met_conditionals -= 1
                    if any([lines[i + l].startswith(cond) for cond in ["else", "stop if"]]) and met_conditionals <= 1:
                        break
                    conditioned_src.append(lines[i + l])
                    l += 1
                l += 1
                while True:
                    if lines[i + l].startswith("new if"):
                        met_conditionals += 1
                    if lines[i + l].startswith("stop if"):
                        met_conditionals -= 1
                    if lines[i + l].startswith("stop if") and met_conditionals <= 1:
                        break
                    l += 1
                for k in range(i + l + 1, len(lines)):
                    conditioned_src.append(lines[k])
            else:
                l = 1
                while True:
                    if lines[i + l].startswith("new if"):
                        met_conditionals += 1
                    if lines[i + l].startswith("stop if"):
                        met_conditionals -= 1
                    if any([lines[i + l].startswith(cond) for cond in ["else", "stop if"]]) and met_conditionals <= 1:
                        break
                    l += 1
                l += 1
                while True:
                    if lines[i + l].startswith("new if"):
                        met_conditionals += 1
                    if lines[i + l].startswith("stop if"):
                        met_conditionals -= 1
                    if lines[i + l].startswith("stop if") and met_conditionals <= 1:
                        break
                    conditioned_src.append(lines[i + l])
                    l += 1
                for k in range(i + l + 1, len(lines)):
                    conditioned_src.append(lines[k])
            break
        if line.startswith("new if"):
            if not any([keyword in line for keyword in ["equals",]]):
                assert False, "Invalid conditional syntax"
            met_conditionals = 1
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: v for k, v in zip(keywords, values)}
            inside_if = True
            inside_else = False
            if "greater" in zipped:
                if int(zipped["greater"]) > int(zipped["than"]):
                    keep_if = True
                else:
                    keep_if = False
            elif "greater-equal" in zipped:
                if int(zipped["greater-equal"]) >= int(zipped["than"]):
                    keep_if = True
                else:
                    keep_if = False
            elif "lesser" in zipped:
                if int(zipped["lesser"]) < int(zipped["than"]):
                    keep_if = True
                else:
                    keep_if = False
            elif "lesser-equal" in zipped:
                if int(zipped["lesser-equal"]) <= int(zipped["than"]):
                    keep_if = True
                else:
                    keep_if = False
            elif "same" in zipped:
                if int(zipped["same"]) == int(zipped["and"]):
                    keep_if = True
                else:
                    keep_if = False
            elif "different" in zipped:
                if int(zipped["different"]) != int(zipped["and"]):
                    keep_if = True
                else:
                    keep_if = False
            elif "multiple" in zipped:
                if int(zipped["multiple"]) % int(zipped["of"]) == 0:
                    keep_if = True
                else:
                    keep_if = False
            else:
                assert False, "Unknown condition"
        else:
            conditioned_src.append(line)
            i += 1

    return conditioned_src


def handleVariables(value, linen):
    global variables
    returnable = value
    removeVariables(variables, linen)
    for variable in variables:
        if value.strip() == "@" + variable.name + "@":
            returnable = variable.value
            break

    return returnable

def removeVariables(variables, linen):
    to_remove = []
    for variable in variables:
        for secondVar in variables:
            if secondVar.name == variable.name and secondVar.linen > variable.linen and linen == secondVar.linen:
                to_remove.append(variable)

    for r in to_remove:
        variables.pop(variables.index(r))

    setVariables(variables)

def setVariables(varrs):
    global variables
    variables = varrs


def parseRooms(src):
    global variables

    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    h = lambda v, l: handleVariables(v, l)
    ROOMS = []
    for i, line in enumerate(lines):
        removeVariables(variables, i)
        if line.startswith("new room"):
            if not all(
                [keyword in line for keyword in ["id", "width", "height", "anchor"]]
            ):
                assert False, 'Invalid room creation syntax: "' + line + '"'
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: h(v, i) for k, v in zip(keywords, values)}
            BOXES = parseBoxesForRoom(src, zipped["id"])
            CABLES = parseCablesForRoom(src, zipped["id"])
            DOORS = parseDoorsForRoom(src, zipped["id"])
            ROOMS.append(
                Room(
                    zipped["id"],
                    zipped["width"],
                    zipped["height"],
                    [int(h(n, i)) for n in h(zipped["anchor"], i).split(",")],
                    BOXES,
                    CABLES,
                    DOORS,
                )
            )

    return ROOMS


def parseAny(src, start, required, lambda_checks, lambda_generate, addLine = False):
    global variables

    with open(src, "r") as f:
        lines = [line.strip() for line in f.readlines() if line]

    OBJS = []
    for i, line in enumerate(lines):
        if line.startswith(start):
            if not all([keyword in line for keyword in required]):
                assert False, 'Invalid creation syntax: "' + line + '"'
            keywords = line.split(" ")[2::2]
            values = line.split(" ")[3::2]
            zipped = {k: handleVariables(v, i) if variables else v for k, v in zip(keywords, values)}
            if lambda_checks and lambda_checks[-1].__name__ == "same_room":
                if not lambda_checks[-1](zipped):
                    continue
            for check in lambda_checks[:-1]:
                assert check(zipped), 'Check failed: "' + check.__name__ + '" with values "' + str(zipped) + '"'
            if not addLine:
                OBJS.append(lambda_generate(zipped))
            else:
                OBJS.append(lambda_generate(zipped, i))

    return OBJS


def parseAnyForRoom(src, room, start, required, lambda_checks, lambda_generate, addLine = False):
    def same_room(zipped):
        return zipped["room"] == room

    return parseAny(
        src,
        start,
        required,
        (*lambda_checks, same_room),
        lambda_generate,
        addLine
    )


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


def parseVariables(src):
    start = "set var"
    required = ["name", "value"]
    checks = []

    def generate(zipped, linen):
        return Variable(zipped["name"], zipped["value"], linen)

    return parseAny(src, start, required, checks, generate, True)


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
        if room.anchor[0] >= maxX:
            maxX = room.anchor[0]
            if room.width >= maxXwidth:
                maxXwidth = room.width
        if room.anchor[1] >= maxY:
            maxY = room.anchor[1]
            if room.height >= maxYheight:
                maxYheight = room.height

    image = Image.new(
        mode="RGB",
        size=(
            (maxX + maxXwidth) * Const.ROOM_SIZE * Const.CELL_SIZE,
            (maxY + maxYheight) * Const.ROOM_SIZE * Const.CELL_SIZE,
        ),
        color=Const.WHITE,
    )
    for room in rooms:
        image.paste(
            Image.open(str(room.uid) + ".png", "r"),
            (
                room.anchor[0] * Const.ROOM_SIZE * Const.CELL_SIZE,
                room.anchor[1] * Const.ROOM_SIZE * Const.CELL_SIZE,
            ),
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
            (
                a[0] * Const.CELL_SIZE,
                a[1] * Const.CELL_SIZE,
                a[0] * Const.CELL_SIZE + Const.CELL_SIZE,
                a[1] * Const.CELL_SIZE + Const.CELL_SIZE,
            ),
            fill=tuple(box.color),
            outline=(0),
        )
        draw.text(
            (a[0] * Const.CELL_SIZE + 4, a[1] * Const.CELL_SIZE + 12),
            box.name,
            Const.WHITE,
        )
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
    global variables

    src = parseMacros(sys.argv[1])

    # Handle nested loops
    tmp_src = []
    while True:
        tmp_src = parseLoops(src)
        if tmp_src != src:
            src = tmp_src
            continue
        break

    # Handle nested ifs
    tmp_src = []
    while True:
        tmp_src = parseConditionals(src)
        if tmp_src != src:
            src = tmp_src
            continue
        break

    srcf = "precompiled.src.floor"
    with open(srcf, "w") as f:
        f.writelines(src)

    # Vars and Consts can be parsed only after the src is flattened
    variables = parseVariables(srcf)

    rooms = parseRooms(srcf)
    drawRooms(rooms)


if __name__ == "__main__":
    variables = []
    main()
