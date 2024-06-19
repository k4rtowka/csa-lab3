import json

from cpu.isa import Address, Opcode

start_label = "_start"

marks = dict()


def cleaning(file_name):
    file = open(file_name).readlines()

    for i in range(len(file) - 1, -1, -1):
        file[i] = file[i].strip()
        if file[i] == "":
            del file[i]
    for i in range(len(file) - 2, -1, -1):
        if file[i][-1] == ":":
            file[i] = file[i] + file[i + 1]
            del file[i + 1]
    return file


def stage_start(file_name):  # noqa: C901
    file = cleaning(file_name)
    memory = []
    i = -1
    while True:
        i += 1
        line = file[i]
        if line[: len(start_label)] == start_label:
            break
        if ":" in line:
            label, data = line.split(":")
            data = data.strip()
            marks[label] = len(memory)
        else:
            data = line

        if data[0] == "^":
            buffer_len = int(data[1:])
            memory += [0] * buffer_len
        else:
            string = data[1:-1]
            for char in string:
                memory.append(ord(char))
            memory.append(0)
    i -= 1
    while i < len(file) - 1:
        i += 1
        line = file[i]

        if ":" in line:
            label, cmd = line.split(":")
            cmd = cmd.strip()
            marks[label] = len(memory)
        else:
            cmd = line
        if cmd.count(" ") >= 1:
            opcode, args = cmd.split(" ", 1)
            args = args.split()
        else:
            opcode = cmd
            args = []
        if len(args) <= 1:
            arg_type = Address.NO_OP
        else:
            last = args[-1]
            if "#" in last:
                arg_type = Address.LABEL_ADDR
                args[-1] = args[-1][1:]
            elif "'" in last:
                arg_type = Address.DIRECT
                args[-1] = ord(args[-1][1:-1])
            elif last[0].isupper():
                arg_type = Address.REGISTER
            else:
                arg_type = Address.NUMBER
                args[-1] = int(last)
        memory.append({"opcode": Opcode(opcode), "args": args, "arg_type": arg_type, "term": line})

    return memory, marks


def stage_end(file_name):
    memory, marks = stage_start(file_name)
    for cmd in memory:
        if not isinstance(cmd, dict):
            continue
        for i in range(len(cmd["args"])):
            if cmd["args"][i] in marks.keys():
                cmd["args"][i] = marks[cmd["args"][i]]
    return memory


def translate_asm_to_me(source_name, target_name):
    memory = stage_end(source_name)
    json_text = json.dumps([memory, marks["_start"]])

    f = open(target_name, "w")
    f.write(json_text)
    f.close()

    return target_name


def main(source_file, target_file):
    translate_asm_to_me(source_file, target_file)


if __name__ == "__main__":
    translate_asm_to_me("./examples/prob2.examples", "./tmp/prob2.json")
