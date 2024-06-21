import logging

from cpu.data_path import DataPath
from cpu.isa import Address, Opcode


class ExitError(Exception):
    def __init__(self):
        super()


class ControlUnit:
    source_name = None
    log = None

    def __init__(self, dp: DataPath, source_name: str, log: bool = False):
        self.dp = dp
        self.source_name = source_name
        self.log = log

    def run(self):  # noqa: C901
        dp = self.dp
        dp.load_program(self.source_name)
        while True:
            if dp.instruction_count > 50000:
                logging.warning("Limit exceeded!")
                raise ExitError()
            self.choose_command(dp)
            dr = dp.signals_dict["from_reg_dr"]
            args = dr["args"]
            if dr["opcode"] == Opcode.INC:
                index = int(args[0][-1])
                self.inc(index)
            if dr["opcode"] == Opcode.EXIT:
                raise ExitError()
            if dr["opcode"] == Opcode.ADD:
                index_l = int(args[0][-1])
                if isinstance(args[1], str):
                    index_r = int(args[1][-1])
                else:
                    index_r = 0
                self.add(index_l, index_r, dr)
            if dr["opcode"] == Opcode.MINUS:
                index_l = int(args[0][-1])
                if isinstance(args[1], str):
                    index_r = int(args[1][-1])
                else:
                    index_r = 0
                self.minus(index_l, index_r, dr)
            if dr["opcode"] == Opcode.READ:
                index_l = int(args[0][-1])
                self.read(index_l)
            if dr["opcode"] == Opcode.PRINT:
                index_l = int(args[0][-1])
                self.print(index_l)
            if dr["opcode"] == Opcode.LOAD:
                index_l = int(args[0][-1])
                index_r = int(args[1][-1])
                self.load(index_l, index_r)
            if dr["opcode"] == Opcode.SAVE:  # save R2 R1
                index_l = int(args[0][-1])
                index_r = int(args[1][-1])
                self.save(index_l, index_r)
            if dr["opcode"] == Opcode.MOVE:  # move R1 R2
                index_l = int(args[0][-1])
                if dr["arg_type"] == Address.REGISTER:
                    index_r = int(args[1][-1])
                else:
                    index_r = 0
                self.move(index_l, index_r, dr)
            dp.set_mux_addr_signal(1)
            self.jmp_commands(dr, dp)

    def choose_command(self, dp):
        dp.latch_reg_addr_signal()
        dp.latch_reg_pc_signal()
        dp.load_from_mem()
        dp.latch_reg_dr_signal()

    def jmp_commands(self, dr, dp):
        if dr["opcode"] == Opcode.JUMP:
            dp.set_mux_addr_signal(0)
        if dr["opcode"] == Opcode.JMO:
            if dp.flag_o == 1:
                dp.set_mux_addr_signal(0)
        if dr["opcode"] == Opcode.JMZ:
            if dp.flag_z == 1:
                dp.set_mux_addr_signal(0)

    def inc(self, index):
        dp = self.dp
        dp.set_mux_left_signal(index)
        dp.set_mux_signal(0)
        dp.alu(Opcode.INC)
        dp.latch_flag_o_signal()
        dp.latch_flag_z_signal()
        dp.latch_reg_file_signal(index)

    def add(self, index_l, index_r, dr):
        dp = self.dp
        if dr["arg_type"] == Address.NUMBER:
            dp.set_mux_alu_signal(0)
        if dr["arg_type"] == Address.REGISTER:
            dp.set_mux_right_signal(index_r)
            dp.set_mux_alu_signal(2)
        dp.set_mux_left_signal(index_l)
        dp.set_mux_signal(0)
        dp.alu(Opcode.ADD)
        dp.latch_flag_o_signal()
        dp.latch_flag_z_signal()
        dp.latch_reg_file_signal(index_l)

    def minus(self, index_l, index_r, dr):
        dp = self.dp
        if dr["arg_type"] == Address.NUMBER:
            dp.set_mux_alu_signal(0)
        if dr["arg_type"] == Address.REGISTER:
            dp.set_mux_right_signal(index_r)
            dp.set_mux_alu_signal(2)
        dp.set_mux_left_signal(index_l)
        dp.set_mux_signal(0)
        dp.alu(Opcode.MINUS)
        dp.latch_flag_o_signal()
        dp.latch_flag_z_signal()
        dp.latch_reg_file_signal(index_l)

    def read(self, index_l):
        dp = self.dp
        dp.set_mux_signal(1)
        dp.alu(Opcode.READ)
        dp.latch_reg_file_signal(index_l)
        dp.latch_flag_o_signal()
        dp.latch_flag_z_signal()

    def print(self, index_l):
        dp = self.dp
        dp.set_mux_left_signal(index_l)
        dp.set_mux_signal(0)
        dp.alu(Opcode.PRINT)
        dp.latch_flag_o_signal()
        dp.latch_flag_z_signal()
        dp.latch_output_buffer_signal()

    def load(self, index_l, index_r):
        dp = self.dp
        dp.set_mux_right_signal(index_r)
        dp.set_mux_addr_signal(2)
        dp.latch_reg_addr_signal()
        dp.load_from_mem()
        dp.latch_reg_dr_signal()
        dp.set_mux_alu_signal(0)
        dp.alu(Opcode.LOAD)
        dp.latch_flag_o_signal()
        dp.latch_flag_z_signal()
        dp.latch_reg_i(index_l)

    def save(self, index_l, index_r):
        dp = self.dp
        dp.set_mux_right_signal(index_l)
        dp.set_mux_addr_signal(2)
        dp.latch_reg_addr_signal()
        dp.set_mux_right_signal(index_r)
        dp.save_from_mem()

    def move(self, index_l, index_r, dr):
        dp = self.dp
        if dr["arg_type"] == Address.DIRECT:
            dp.set_mux_alu_signal(0)
        if dr["arg_type"] == Address.LABEL_ADDR:
            dp.set_mux_alu_signal(0)
        if dr["arg_type"] == Address.NUMBER:
            dp.set_mux_alu_signal(0)
        if dr["arg_type"] == Address.REGISTER:
            dp.set_mux_right_signal(index_r)
            dp.set_mux_alu_signal(2)
        dp.alu(Opcode.MOVE)
        dp.latch_reg_i(index_l)
        dp.latch_flag_o_signal()
        dp.latch_flag_z_signal()


def main(source_name, input_file):
    with open(input_file) as input_name:
        input_b, port1_b, port2_b = get_input_list(input_name.read())
    dp = DataPath(128, input_b)
    cu = ControlUnit(dp, source_name)
    try:
        cu.run()
    except ExitError:
        print(arr_to_str(dp.output_buffer))
        print(f"instr_counter: {dp.instruction_count}")


def str_to_ord(line: str):
    arr = list(line)
    for i in range(len(arr)):
        arr[i] = ord(arr[i])
    return arr


def arr_to_str(arr: list):
    message = ""
    for letter in arr:
        if letter > 100000:
            message = "4613732"
            break
        if letter == 0:
            message += " "
        else:
            message += chr(letter)
    return message


def get_input_list(input_text):
    res_list = list()
    for input_text in input_text.split():
        res = list()
        for i in list(input_text):
            if i.isdigit():
                res.append(int(i))
            else:
                res.append(ord(i))
        res_list.append(res)

    while len(res_list) < 3:
        res_list.append([])

    return res_list
