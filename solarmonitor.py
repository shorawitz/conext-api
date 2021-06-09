from flask import Flask
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api, Resource, reqparse
from pyModbusTCP.client import ModbusClient
from time import sleep

app = Flask(__name__)
api = Api(app)

device_ids = {
    "battery": {
        "primary": 190
    },
    "inverter": {
        "primary": 11
    },
    "cc": {
        "primary": 30,
        "secondary": 31
    }
}

registers_data = {
    "battery": {
        "name": "0,8,0",
        "voltage": "70,2,1000",
        "temp": "74,2,-273",
        "soc": "76,2,0",
        "capacity": "88,2,0"
    },
    "inverter": {
        "name": "0,8,0",
        "state": "64,1,0",
        "enabled": "71,1,0",
        "faults": "75,1,0",
        "warnings": "76,1,0",
        "status": "122,1,0",
        "load": "154,2,0"
    },
    "cc": {
        "name": "0,8,0",
        "state": "64,1,0",
        "faults": "68,1,0",
        "warnings": "69,1,0",
        "status": "73,1,0",
        "pvpower": "80,2,0",
        "dcpower": "92,2,0",
        "solararray": "249,1,0"
    }
}

operating_state = {
    0: "Hibernate",
    1: "Power Save",
    2: "Safe Mode",
    3: "Operating",
    4: "Diagnostic Mode",
    5: "Remote Power Off",
    255: "Data Not Available",
}

inverter_status = {
    1024: "Invert",
    1025: "AC Pass Through",
    1026: "APS Only",
    1027: "Load Sense",
    1028: "Inverter Disabled",
    1029: "Load Sense Ready",
    1030: "Engaging Inverter",
    1031: "Invert Fault",
    1032: "Inverter Standby",
    1033: "Grid-Tied",
    1034: "Grid Support",
    1035: "Gen Support",
    1036: "Sell-to-Grid",
    1037: "Load Shaving",
    1038: "Grid Frequency Stabilization"
}

cc_status = {
    768: "No Charging",
    769: "Bulk",
    770: "Absorption",
    771: "Overcharge",
    772: "Equalize",
    773: "Float",
    774: "No Float",
    775: "Constant VI",
    776: "Charger Disabled",
    777: "Qualifying AC",
    778: "Qualifying APS",
    779: "Engaging Charger"
}

solar_association = {
    21: "Solar Array 1",
    22: "Solar Array 2",
    23: "Solar Array 3",
    24: "Solar Array 4"
}

# Get the data from ModBusTCP for the device
def get_modbus_values(device, device_instance):
    devices = device_ids[device]
    register_data = registers_data[device]
    return_data = {}
    #print("devices: {}".format(devices))
    for device_key in devices:
        # If we're looking for a specific device, let's check
        if device_instance and device_instance != device_key:
            continue
        
        return_data[device_key] = {}
        # Loop over our register_data and query for the values for the device
        for register_name in register_data:
            register_data_values = register_data[register_name].split(',')
            register = register_data_values[0]
            reg_len = register_data_values[1]
            extra = register_data_values[2]

            # Connect to Conext GW, then get the value
            cxt = ModbusClient(host="192.168.0.152", port=503, auto_open=True, auto_close=True, debug=False, unit_id=devices[device_key], timeout=30)
            #print("unit_id: {}, register: {}, reg_len: {}".format(devices[device_key], register, reg_len))
            hold_reg_arr = cxt.read_holding_registers(int(register), int(reg_len))
            #print("reg_len: {}".format(reg_len))

            # Fix hold_reg values
            if int(reg_len) == 2:
                #print("reg_len: {} - hold_reg_arr: {}".format(reg_len, hold_reg_arr))
                converted_value = hold_reg_arr[1] - hold_reg_arr[0]
            elif int(reg_len) == 8:
                #print("reg_len: {} - hold_reg_arr: {}".format(reg_len, hold_reg_arr))
                string_chars = ""
                for a in hold_reg_arr:
                    if a > 0:
                        hex_string = hex(a)[2:]
                        if hex_string.endswith("00"):
                            hex_string = hex_string[:len(hex_string) - 2]
                        #print("hex_string: {}".format(hex_string))
                        bytes_object = bytes.fromhex(hex_string)
                        string_chars = string_chars + bytes_object.decode("ASCII")
        
                converted_value = string_chars
            else:
                #print("reg_len: {} - hold_reg_arr: {}".format(reg_len, hold_reg_arr))
                converted_value = hold_reg_arr[0]

            # Bad hack to convert value to proper decimal or dict[item] (if needed) and designation
            if device == "battery":
                if register == "70":
                    converted_value = converted_value / int(extra)
                    converted_value = converted_value
                elif register == "74":
                    converted_value = converted_value * 0.01 + int(extra)
                elif register == "76":
                    converted_value = converted_value
                elif register == "88":
                    converted_value = converted_value
                else:
                    converted_value = 0

            if device == "inverter":
                if register == "64":
                    converted_value = operating_state[converted_value]
                elif register == "122":
                    converted_value = inverter_status[converted_value]
                elif register == "154":
                    #print("Inverter load: {}".format(converted_value))
                    converted_value = converted_value
                else:
                    converted_value = 0

            if device == "cc":
                if register == "64":
                    converted_value = operating_state[converted_value]
                elif register == "73":
                    converted_value = cc_status[converted_value]
                elif register == "80":
                    converted_value = converted_value
                elif register == "92":
                    converted_value = converted_value
                elif register == "249":
                    converted_value = solar_association[converted_value]
                else:
                    converted_value = 0

            #print("device_key: {} register_name: {}".format(device_key, register_name))
            return_data[device_key][register_name] = converted_value
            sleep(0.1)
    
    return return_data

class Battery(Resource):
    def get(self, instance=None):
        modbus_values = get_modbus_values("battery", instance)
        
        if instance:
            return modbus_values[instance]

        return modbus_values

class Inverter(Resource):
    def get(self, instance=None):
        modbus_values = get_modbus_values("inverter", instance)
        
        #print(modbus_values)
        if instance:
            return modbus_values[instance]

        return modbus_values

    def put(self, instance):
        #args = invter_put_args.parse_args()
        return {"command": "received for instance: {}".format(instance)}

class CC(Resource):
    def get(self, instance=None):
        modbus_values = get_modbus_values("cc", instance)
        
        #if instance:
        #    return modbus_values[instance]

        return modbus_values

    def put(self, instance):
        #args = cc_put_args.parse_args()
        return {"command": "received for instance: {}".format(instance)}

api.add_resource(Battery, "/battery", "/battery/<string:instance>")
api.add_resource(Inverter, "/inverter", "/inverter/<string:instance>")
api.add_resource(CC, "/cc", "/cc/<string:instance>")

if __name__ == "__main__":
    app.run(debug=False)
