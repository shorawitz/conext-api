#!/usr/bin/python3

from pyModbusTCP.client import ModbusClient
from time import sleep
import sys, getopt, re


# Default data type
data_type = "uint16"
ip = None


try:
    opts, args = getopt.getopt(sys.argv[1:],"hi:p:u:r:t:",["ip=","port=","unit_id=","register","type"])
except getopt.GetoptError:
    print('query.py -i <ip address> -p <port> -u <unit_id> -r <register> (-t <type> | default=uint16)')
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print('query.py -i <ip address> -p <port> -u <unit_id> -r <register> -t <value data type>')
        sys.exit()
    elif opt in ("-i", "--ip"):
        ip = arg
    elif opt in ("-p", "--port"):
        port = arg
    elif opt in ("-u", "--unit_id"):
        unit_id = arg
    elif opt in ("-r", "--register"):
        reg = arg
    elif opt in ("-t", "--type"):
        reg_type = arg
    else:
        print('Unknown option')
        sys.exit(2)

if not ip or not port or not unit_id or not reg:
    print('query.py -i <ip address> -p <port> -u <unit_id> -r <register> (-t <type> | default=uint16)')
    sys.exit()


client = ModbusClient(host=ip, port=port, auto_open=True, auto_close=True, debug=False, unit_id=unit_id, timeout=30)
# Setup registers with ADDRESS,REG_COUNT,TYPE
# Address: reg_count (uint16: 1, uint32: 2, str16: 8, str32: 16)

reg_dict = {}
reg_count = 1
#reg_type = "uint16"

if reg_type == "uint32":
    reg_count = 2
if reg_type == "sint32":
    reg_count = 2
if reg_type == "str16":
    reg_count = 8
if reg_type == "str20":
    reg_count = 10
if reg_type == "str32":
    reg_count = 16

print("port: {}".format(port))
print("unit_id: {}".format(unit_id))
print("reg: {}".format(reg))
print("type: {}".format(reg_type))
print("reg_count: {}".format(reg_count))

#print("reg:{} reg_count:{}".format(reg, reg_count))
#print("reg:{} reg_count:{}".format(type(reg), type(reg_count)))
hold_regs = client.read_holding_registers(int(reg), reg_count)
#input_reg = client.read_input_registers(int(reg), reg_count)
#discrete_reg = client.read_discrete_inputs(int(reg), reg_count)
#relay_reg = client.read_coils(int(reg), reg_count)

#print("holding_registers addr:{}".format(reg))
print("hold_register: {}".format(str(hold_regs)))

if reg_count == 2:
    if hold_regs[0] == 65535:
        converted_value = hold_regs[1] - hold_regs[0]
    else:
        converted_value = hold_regs[0] * 65536 + hold_regs[1]
elif reg_count == 1:
    converted_value = hold_regs[0]
elif reg_count == 8:
    string_chars = ""
    for a in hold_regs:
        if a > 0:
            hex_string = hex(a)[2:]
            bytes_object = bytes.fromhex(hex_string)
            string_chars = string_chars + bytes_object.decode("ASCII")
    
    converted_value = string_chars

    

else:
  converted_value = 0
  
print("converted value: {}".format(converted_value))

#print("input_register: {}".format(str(input_reg)))
#print("discrete_register: {}".format(str(discrete_reg)))
#print("relay_register: {}".format(str(relay_reg)))


""" last_reg = 1
while last_reg <= 84:
    test_regs = client.read_holding_registers(int(last_reg), 125)
    print("test_register: {}".format(str(test_regs)))
    last_reg = last_reg + 1 """
