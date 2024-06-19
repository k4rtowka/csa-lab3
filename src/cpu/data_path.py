import json
import logging

from cpu.isa import Opcode


class EmptyBufferError(Exception):
    def __init__(self):
        super()


class DataPath:
    reg_file = None
    reg_dr = None
    reg_addr_new = None
    reg_addr = None
    flag_z = None
    flag_o = None
    mux_addr_i = None
    mux_alu_i = None
    mux_i = None
    mux_left_i = None
    mux_right_i = None

    signals_dict = None
    opcode = None

    mem = None
    mem_size = None
    log = None
    instruction_count = 0

    def __init__(self, mem_size, input_buffer=None, port_in1=None, port_in2=None, log: bool = False):
        if port_in2 is None:
            port_in2 = []
        if port_in1 is None:
            port_in1 = []
        if input_buffer is None:
            input_buffer = []
        input_buffer.reverse()
        self.input_buffer = input_buffer
        self.log = log
        self.opcode = ""

        self.output_buffer = list()

        port_in1.reverse()
        self.portIn1 = port_in1

        port_in2.reverse()
        self.portIn2 = port_in2

        self.portOut1 = list()
        self.portOut2 = list()

        self.mem_size = mem_size

        self.reg_file = [0] * 4
        self.reg_dr = 0
        self.reg_addr_new = 0
        self.reg_addr = 0
        self.flag_z = 0
        self.flag_o = 0
        self.mux_addr_i = 0
        self.mux_alu_i = 0
        self.mux_i = 0
        self.mux_left_i = 0
        self.mux_right_i = 0

        self.signals_dict = {
            "from_MUX_addr": [0, 0, 0],
            "from_MUX_alu": [0, 0, 0],
            "from_MUX": [0, 0, 0, 0],
            "from_MUX_left": [0, 0, 0, 0],
            "from_MUX_right": [0, 0, 0, 0],
            "from_reg_dr": self.reg_dr,
            "from_reg_addr_new": self.reg_addr_new,
            "from_reg_addr": self.reg_addr,
            "from_alu": 0,
            "alu_to_z": self.flag_z,
            "alu_to_o": self.flag_o,
            "from_mem": 0,
        }
        self.mem = [0] * mem_size

    def set_mux_signal(self, i):
        self.instruction_count += 1
        self.mux_i = i
        self.__print__()

    def set_mux_addr_signal(self, i):
        self.instruction_count += 1
        self.mux_addr_i = i
        self.__print__()

    def set_mux_alu_signal(self, i):
        self.instruction_count += 1
        self.mux_alu_i = i
        self.__print__()

    def set_mux_left_signal(self, i):
        self.instruction_count += 1
        self.mux_left_i = i
        self.signals_dict["from_MUX_left"][i] = self.get_from_reg_i(i)
        self.__print__()

    def set_mux_right_signal(self, i):
        self.instruction_count += 1
        self.mux_right_i = i
        self.signals_dict["from_MUX_right"][i] = self.get_from_reg_i(i)
        self.signals_dict["from_MUX_alu"][2] = self.get_from_reg_i(i)
        self.signals_dict["from_MUX_addr"][2] = self.get_from_reg_i(i)
        self.__print__()

    def get_from_reg_i(self, i):
        return self.reg_file[i]

    def latch_reg_i(self, i):
        self.instruction_count += 1
        self.reg_file[i] = self.signals_dict["from_alu"]
        self.__print__()

    def latch_reg_dr_signal(self):
        self.instruction_count += 1
        self.reg_dr = self.signals_dict["from_mem"]
        self.signals_dict["from_reg_dr"] = self.reg_dr
        if isinstance(self.reg_dr, dict):
            if len(self.reg_dr["args"]) > 0:
                self.signals_dict["from_MUX_addr"][0] = self.reg_dr["args"][0]
            if len(self.reg_dr["args"]) > 1:
                self.signals_dict["from_MUX_alu"][0] = self.reg_dr["args"][1]
        else:
            self.signals_dict["from_MUX_addr"][0] = self.reg_dr
            self.signals_dict["from_MUX_alu"][0] = self.reg_dr
        self.__print__()

    def latch_reg_addr_signal(self):
        self.instruction_count += 1
        self.reg_addr = self.signals_dict["from_MUX_addr"][self.mux_addr_i]
        self.signals_dict["from_reg_addr"] = self.reg_addr
        self.signals_dict["from_MUX_alu"][1] = self.reg_dr
        self.__print__()

    def latch_reg_addr_new_signal(self):
        self.instruction_count += 1
        self.reg_addr_new = self.signals_dict["from_reg_addr"] + 1
        self.signals_dict["from_reg_addr_new"] = self.reg_addr_new
        self.signals_dict["from_MUX_addr"][1] = self.reg_addr_new
        self.__print__()

    def latch_flag_z_signal(self):
        self.instruction_count += 1
        self.flag_z = self.signals_dict["alu_to_z"]
        self.__print__()

    def latch_flag_o_signal(self):
        self.instruction_count += 1
        self.flag_o = self.signals_dict["alu_to_o"]
        self.__print__()

    def load_from_mem(self):
        self.instruction_count += 1
        self.signals_dict["from_mem"] = self.mem[self.signals_dict["from_reg_addr"]]
        self.__print__()

    def save_from_mem(self):
        self.instruction_count += 1
        self.mem[self.signals_dict["from_reg_addr"]] = self.signals_dict["from_MUX_right"][self.mux_right_i]
        self.__print__()

    def get_mux(self):  # noqa: C901
        self.instruction_count += 1
        if self.mux_i == 0:
            mux = self.signals_dict["from_MUX_left"][self.mux_left_i]
            self.signals_dict["from_MUX"][self.mux_i] = mux
        if self.mux_i == 1:
            if len(self.input_buffer) == 0:
                if self.log:
                    logging.warning("Input buffer is empty!")
                raise EmptyBufferError()
            mux = self.input_buffer.pop()
            self.signals_dict["from_MUX"][self.mux_i] = mux
        if self.mux_i == 2:
            if len(self.portIn1) == 0:
                if self.log:
                    logging.warning("Port buffer 1 is empty!")
                raise EmptyBufferError()
            mux = self.portIn1.pop()
            self.signals_dict["from_MUX"][self.mux_i] = mux
        if self.mux_i == 3:
            if len(self.portIn2) == 0:
                if self.log:
                    logging.warning("Port buffer 2 is empty!")
                raise EmptyBufferError()
            mux = self.portIn1.pop()
            self.signals_dict["from_MUX"][self.mux_i] = mux
        self.__print__()

    def latch_port_out1_signal(self):
        self.instruction_count += 1
        self.portOut1.append(self.signals_dict["from_alu"])
        self.__print__()

    def latch_port_out2_signal(self):
        self.instruction_count += 1
        self.portOut2.append(self.signals_dict["from_alu"])
        self.__print__()

    def latch_output_buffer_signal(self):
        self.instruction_count += 1
        self.output_buffer.append(self.signals_dict["from_alu"])
        self.__print__()

    def latch_reg_file_signal(self, i):
        self.instruction_count += 1
        self.reg_file[i] = self.signals_dict["from_alu"]
        self.__print__()

    # Left - first, Right - second
    def alu(self, code: Opcode):  # noqa: C901
        self.instruction_count += 1
        res = 0
        try:
            self.get_mux()
        except EmptyBufferError:
            self.signals_dict["from_MUX"][self.mux_i] = 0
        left_opp = self.signals_dict["from_MUX"][self.mux_i]
        right_opp = self.signals_dict["from_MUX_alu"][self.mux_alu_i]
        if code == Opcode.INC:
            res = left_opp + 1
        if code == Opcode.ADD:
            res += left_opp
            res += right_opp
        if code == Opcode.MINUS:
            res += left_opp
            res -= right_opp
        if code == Opcode.READ:
            res = left_opp
        if code == Opcode.PRINT:
            res = left_opp
        if code == Opcode.LOAD:
            res = right_opp
        if code == Opcode.SAVE:
            res = right_opp
        if code == Opcode.MOVE:
            res = right_opp
        self.signals_dict["from_alu"] = res
        self.signals_dict["alu_to_z"] = int(res == 0)
        self.signals_dict["alu_to_o"] = 1 - int(res % 2 == 0)
        self.__print__()

    def __print__(self):
        if isinstance(self.reg_dr, dict):
            self.opcode = self.reg_dr["opcode"]
        state_repr = (
            "exec_instruction: {:4} | AR: {:3} | AR_NEW {:3} | Z: {:1} | O: {:1} |"
            " r0: {:3} | r1: {:3} | r2: {:3} | r3: {:3} | OPCODE: {:4}"
        ).format(
            self.instruction_count,
            self.reg_addr,
            self.reg_addr_new,
            self.flag_z,
            self.flag_o,
            self.reg_file[0],
            self.reg_file[1],
            self.reg_file[2],
            self.reg_file[3],
            self.opcode,
        )
        logging.debug(state_repr)

    def load_program(self, source_name):
        with open(source_name) as p:
            program, start_addr = json.load(p)
        self.mem = program
        self.signals_dict["from_MUX_addr"][0] = start_addr
        self.set_mux_addr_signal(0)


if __name__ == "__main__":
    DataPath(12).load_program("./tmp/task1.json")
