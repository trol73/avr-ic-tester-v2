# -*- coding: utf-8 -*-
import time
import serial

__author__ = 'Trol'


class Device:
    CMD_SYNC = 1
    CMD_ENTER_TEST_MODE = 2
    CMD_TEST_INSTRUCTION = 3
    CMD_READ_CHIP = 4
    CMD_EXIT_TEST_MODE = 5
    CMD_SEND_BYTE_TO_DISPLAY = 6
    CMD_SEND_BYTES_TO_DISPLAY =  7
    CMD_READ_BYTE_FROM_DISPLAY = 8
    CMD_SET_DIRECTION = 9
    CMD_GET_PIN = 10
    CMD_SET_POWER = 11
    CMD_POWER_OFF = 12
    CMD_TEST_LOGIC = 13
    CMD_TEST_RAM = 14
    CMD_READ_ROM_START = 15
    CMD_READ_ROM_NEXT = 16
    CMD_GOTO_BOOTLOADER	= 17
    CMD_ABOUT = 18
    CMD_CONFIGURE_POWER = 19
    CMD_POWER_OUT_BYTE = 20
    CMD_POWER_SET_ALL = 21

    TEST_CMD_SET_40 = 8
    TEST_CMD_SET_TO_0 = 43
    TEST_CMD_SET_TO_1 = 44

    def __init__(self, port_name, bauds):
        self.serial = serial.serial_for_url(port_name, baudrate=bauds, timeout=0.5)
        self.connected = False

    def connect(self):
        # self.connected = True
        # try:
        #     if self.sync(123) == 123 and self.sync(0xAB) == 0xAB:
        #         self.connected = True
        #         return
        # except:
        #     pass
        # try:
        #     if self.sync(123) == 123 and self.sync(0xAB) == 0xAB:
        #         self.connected = True
        #         return
        # except:
        #     pass
        # try:
        #     if self.sync(123) == 123 and self.sync(0xAB) == 0xAB:
        #         self.connected = True
        #         return
        # except:
        #     pass
        #
        # self.connected = False
        try:
            self._read()
        except:
            pass

        for i in range(1, 10):
            #print '?', i
            try:
                if self.sync(Device.CMD_SYNC) == i:
                    break
            except:
                print '.',
                pass
        for i in range(100, 200, 10):
            try:
                if self.sync(i) == i:
                    break
            except:
                print '.',
                pass
        print
        self.connected = True

    def close(self):
        self.serial.close()
        self.connected = False

    def sync(self, v):
        #print 'sync', v
        self._cmd(Device.CMD_SYNC, v)
        resp = self._read()
        #print 'resp', resp
        return resp

    def enter_test_mode(self):
        self._cmd(Device.CMD_ENTER_TEST_MODE, 13)
        if self._read() != 0:
            raise Exception("Can't enter remote mode")

    def exit_test_mode(self):
        self._cmd(Device.CMD_EXIT_TEST_MODE)
        return self._read() == 0

    def exec_test_instruction(self, *args):
        self._cmd(Device.CMD_TEST_INSTRUCTION)
        for a in args:
            self._cmd(a)
        return self._read() == 0

    def set_pin_direction(self, pin40, out):
        self._cmd(Device.CMD_SET_DIRECTION, pin40, 1 if out else 0)
        # try:
        #     resp = self._read()
        #     print 'r1', resp
        # except:
        #     print '.'
        # try:
        #     resp = self._read()
        #     print 'r2', resp
        # except:
        #     print '.'
        # try:
        #     resp = self._read()
        #     print 'r3', resp
        # except:
        #     print '.'
        # if resp != 0:
        #     raise Exception('set_pi_direction() error, resp = ' + str(resp))
        if self._read() != 0:
            raise Exception("Can't set pin direction")

    def power_out_byte(self, b):
        self._cmd(Device.CMD_POWER_OUT_BYTE, b)

    def power_set_all(self):
        self._cmd(Device.CMD_POWER_SET_ALL)

    def rom_read_start(self, rom_type):
        self._cmd(Device.CMD_READ_ROM_START, rom_type)

    def rom_read_next(self):
        self._cmd(Device.CMD_READ_ROM_NEXT)
        return self._read()

    def set_pin_to(self, pin, val):
        if type(val) is bool:
            if val:
                self.exec_test_instruction(Device.TEST_CMD_SET_TO_1, pin)
            else:
                self.exec_test_instruction(Device.TEST_CMD_SET_TO_0, pin)
        elif type(val) is int:
            if val == 1:
                self.exec_test_instruction(Device.TEST_CMD_SET_TO_1, pin)
            elif val == 0:
                self.exec_test_instruction(Device.TEST_CMD_SET_TO_0, pin)
            else:
                raise Exception('wrong pin value ' + str(val))
        else:
            raise Exception('wrong pin value, bool or int expected')

    def set_pins(self, to_0_list, to_1_list):
        m0 = [0, 0, 0, 0, 0]
        m1 = [0, 0, 0, 0, 0]
        for i in range(0, 5):
            for bit in range(0, 8):
                pin = 8*i + bit
                if pin in to_0_list:
                    m0[i] |= 1 << bit
                if pin in to_1_list:
                    m1[i] |= 1 << bit
        self.exec_test_instruction(Device.TEST_CMD_SET_40, m0, m1)

    def get_pin(self, pin):
        self._cmd(Device.CMD_GET_PIN, pin)
        val = self._read()
        #print 'get pin ', pin, ' -> ', val
        return val

    def set_power_plus(self, pin):
        self._cmd(Device.CMD_SET_POWER, pin+1, 2)
        resp = self._read()
        if resp != 0:
            raise Exception("Can't set_power_plus for " + str(pin) + " pin (response=" + str(resp) + ')')

    def set_power_minus(self, pin):
        self._cmd(Device.CMD_SET_POWER, pin+1, 1)
        resp = self._read()
        if resp != 0:
            raise Exception("Can't set_power_minus for " + str(pin) + " pin (response=" + str(resp) + ')')

    def disable_power(self):
        self._cmd(Device.CMD_POWER_OFF)

    def read_chip(self):
        self._cmd(Device.CMD_READ_CHIP)
        result = []
        for i in range(0, 40):
            v = self._read()
            ddr = 'i' if (v & 4) == 0 else 'o'
            port = 0 if (v & 2) == 0 else 1
            pin = 0 if (v & 1) == 0 else 1
            rec = {'ddr': ddr, 'port': port, 'pin': pin}
            result.append(rec)
        return result

    def _cmd(self, *args):
        if not self.connected:
            raise Exception("Device doesn't connected")
        # if self.prefix >= 0:
        #     self._write(self.prefix)
        #     self._write(len(args))
        for a in args:
            #print a
            if type(a) is tuple:
                for v in a:
                    self._write(v)
            elif type(a) is str:
                for c in a:
                    self._write(ord(c))
                self._write(0)
            elif type(a) is list:
                for v in a:
                    self._write(v)
            else:
                self._write(a)



    def _write(self, b):
        # print '>> ', b
        self.serial.write(chr(b))

    def _read(self):
        b = ord(self.serial.read())
        # print '<< ', b
        return b


#t = Device('com3', 57600)
#t.connect()
#print 10, t.sync(10)

#t.enter_test_mode()
# raw_input('power+')
# t.exec_test_instruction_2(41, 40)  # POWER+ 40
# raw_input('power-')
# t.exec_test_instruction_2(42, 12)  # POWER- 12
# raw_input('init')
# t.exec_test_instruction_3(1, 0, 0)  # INIT 0, 0
# raw_input('power_connected')


# t.power_out_byte(0)
# t.power_out_byte(0xff)
# t.power_out_byte(0xff)
# t.power_set_all()

# t.rom_read_start(6)        # 512
# t.rom_read_start(5)        # 256
# t.rom_read_start(4)         # 128
# t.rom_read_start(3)         # 64
# t.rom_read_start(1)         # 16
# t.rom_read_start(7)        # 155RE3
# t.rom_read_start(8)        # 556PT4
#t.rom_read_start(9)  # 556PT5

#s = ''
# for i in range(0, 512):
#     if (i % 16) == 0:
#         print s
#         s = ''
#
#     s += chr(t.rom_read_next()).encode('hex') + ' '

# raw_input('power_connected')

#t.exit_test_mode()
# t.exit_test_mode()
