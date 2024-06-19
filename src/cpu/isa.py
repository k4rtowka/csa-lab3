from enum import StrEnum


class Address(StrEnum):
    NO_OP = "no_op"
    DIRECT = "direct_addr"
    LABEL_ADDR = "label_addr"
    REGISTER = "register"
    NUMBER = "number"


class Opcode(StrEnum):
    INC = "inc"  # acc operations

    ADD = "add"  # + and -
    MINUS = "minus"

    READ = "read"
    PRINT = "print"

    LOAD = "load"
    SAVE = "save"
    MOVE = "move"

    JUMP = "jump"
    JMZ = "jmz"
    JMO = "jmo"

    EXIT = "exit"  # stop
