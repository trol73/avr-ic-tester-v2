# -*- coding: utf-8 -*-
import device

__author__ = 'Trol'


def convert_pin(pin, from_size, to_size):
    """
    Перевод номера пина для микосхемы
    :param pin: номер пина, нумерация от 0
    :param from_size: число выводов микросхемы
    :param to_size: число выводов ZIF-панели (40)
    :return:
    """
    return pin if pin < from_size / 2 else pin + to_size - from_size


class Tester:
    def __init__(self, port_name):
        self.dev = device.Device(port_name, 57600)
        self.buses = {}
        self.cached_state = None
        self.power_plus = []
        self.power_minus = []

    def connect(self):
        self.dev.connect()
        self.dev.enter_test_mode()

    def close(self):
        self.dev.exit_test_mode()
        self.dev.close()

    def define_bus(self, name, *pins):
        """
        Определение шины из пинов
        :param name:
        :param pins: список пинов (1..40). Первый пин - старший бит шины, последний - младший
        """
        bus = {'name': name, 'pins': []}
        if type(pins) is tuple:
            if len(pins) != 1:
                raise Exception('expected one list of pins')
            for p in pins[0]:
                bus['pins'].append(p - 1)
        else:
            for p in pins:
                bus['pins'].append(p - 1)
        self.buses[name] = bus

    def define_bus_for_chip(self, chip_size, name, *pins):
        pins40 = []
        for p in pins:
            pins40.append(convert_pin(p - 1, chip_size, 40) + 1)
        self.define_bus(name, pins40)

    def config_bus(self, bus_name, out):
        write_int = False
        if type(out) is str:
            out = out.lower()
            if out == 'out' or out == 'write_int' or out == "output":
                write_int = True
            elif out == 'in' or out == 'read' or out == "input":
                write_int = False
            else:
                raise Exception('wrong argument ' + out + '( "read"/"write_int" or "in/out" expected')
        elif type(out) is int:
            write_int = not (out == 0)
        for pin in self.buses[bus_name]['pins']:
            if (pin in self.power_plus or pin in self.power_minus) and write_int:
                raise Exception('Pin ' + str(pin+1) + ' used as power pin!')
            self.dev.set_pin_direction(pin, write_int)
        self.cached_state = None

    def get_bus(self, bus_name):
        if bus_name not in self.buses.keys():
            raise Exception('Undefined bus: ' + bus_name)
        return self.buses[bus_name]

    def write(self, bus_name, val):
        bus = self.get_bus(bus_name)
        bus_size = len(bus['pins'])
        pin_vals = []
        if type(val) is str:
            val = val.replace(':', '')
            if len(val) != bus_size:
                raise Exception('wrong value ' + val + ' for bus[' + str(bus_size) + ']')
            for c in val:
                if c == '0':
                    pin_vals.append(0)
                elif c == '1':
                    pin_vals.append(1)
                else:
                    raise Exception('Wrong value ' + val)
        elif type(val) is int:
            if val < 0 or val > 2 ** bus_size:
                raise Exception('value out of range: ' + val)
            for b in range(0, bus_size):
                mask = 2 ** (bus_size - b - 1)
                if val & mask == mask:
                    pin_vals.append(1)
                else:
                    pin_vals.append(0)
        elif type(val) is bool:
            if bus_size != 1:
                raise Exception('bus size is ' + str(bus_size) + ', int expected')
            pin_vals.append(1 if val else 0)
        else:
            raise Exception('integer expected')
        set_to_0 = []
        set_to_1 = []
        for i in range(0, bus_size):
            pin = bus['pins'][i]
            if pin_vals[i] == 1:
                set_to_1.append(pin)
            else:
                set_to_0.append(pin)
        self.dev.set_pins(set_to_0, set_to_1)
        self.cached_state = None

    def read(self, bus_name, force=False):
        bus = self.get_bus(bus_name)
        # bus_size = len(bus['pins'])
        if force or self.cached_state is None:
            self.cached_state = self.dev.read_chip()
        result = []
        for pin in bus['pins']:
            state = self.cached_state[pin]
            result.append(state['pin'])
        return result

    def read_val(self, bus_name, force=False):
        res = self.read(bus_name, force)
        val = 0
        for b in res:
            val = b + (val << 1)
        return val

    def enable_power_plus(self, bus_name):
        bus = self.get_bus(bus_name)
        for p in bus['pins']:
            if p not in self.power_plus:
                self.power_plus.append(p)
            self.dev.set_power_plus(p)

    def enable_power_minus(self, bus_name):
        bus = self.get_bus(bus_name)
        for p in bus['pins']:
            if p not in self.power_minus:
                self.power_minus.append(p)
            self.dev.set_power_minus(p)

    def disable_power(self):
        self.dev.disable_power()


def print_pins(tester):
    pins = []
    for p in range(0, 40):
        pins.append(tester.dev.get_pin(p))
    print 'read', pins


def print_chip(tester):
    res = tester.dev.read_chip()
    pin = 1
    for r in res:
        print pin, r
        pin += 1


