from flask import Flask
import flask.scaffold, requests, yaml
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api, Resource, reqparse
from pyModbusTCP.client import ModbusClient
from time import sleep

app = Flask(__name__)
api = Api(app)

# Read in the configuration.yaml file
with open("configuration.yaml") as config_file:
    configuration = yaml.load(config_file, Loader=yaml.FullLoader)

device_ids = configuration['device_ids']
registers_data = configuration['registers_data']
operating_state = configuration['operating_state']
inverter_status = configuration['inverter_status']
cc_status = configuration['cc_status']
solar_association = configuration['solar_association']
conext_gateway = configuration['conext_gateway']
modbus_port = configuration['modbus_port']
conext_gateway_timeout = configuration['conext_gateway_timeout']

# Get the data from ModBusTCP for the device
def get_modbus_values(device, device_instance):
    devices = device_ids[device]
    register_data = registers_data[device]
    return_data = {}
    #print("DEBUG - devices: {}".format(devices))
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
            cxt = ModbusClient(host=conext_gateway, port=modbus_port, auto_open=True, auto_close=True, debug=False, unit_id=devices[device_key], timeout=conext_gateway_timeout)
            hold_reg_arr = cxt.read_holding_registers(int(register), int(reg_len))

            if (hold_reg_arr):
                # Fix hold_reg values
                if int(reg_len) == 2:
                    #print("reg_len: {} - hold_reg_arr: {}".format(reg_len, hold_reg_arr))
                    if hold_reg_arr[0] == 65535:
                        converted_value = hold_reg_arr[1] - hold_reg_arr[0]
                    elif hold_reg_arr[0] > 0 and hold_reg_arr[0] < 50:
                        converted_value = hold_reg_arr[0] * 65536 + hold_reg_arr[1]
                    # Hack to fix Frequency values - for now
                    elif register in ["130","166"]:
                        converted_value = hold_reg_arr[0]
                    else:
                        converted_value = hold_reg_arr[1]
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
                    elif register == "74":
                        converted_value = converted_value * 0.01 + int(extra)
                    elif register in ["76","88"]:
                        converted_value = converted_value
                    else:
                        # Don't alter converted value
                        converted_value = converted_value

                if device == "inverter":
                    if register == "64":
                        converted_value = operating_state[converted_value]
                    elif register == "122":
                        converted_value = inverter_status[converted_value]
                    elif register in ["120","132","154","170","172"]:
                        #print("Inverter load: {}".format(converted_value))
                        converted_value = converted_value
                    elif register in ["126","130","142","144","146","148","162","166","178","180","182","184"]:
                        #print("Inverter load: {}".format(converted_value))
                        converted_value = converted_value / int(extra)
                    else:
                        # Don't alter converted value
                        converted_value = converted_value

                if device == "cc":
                    if register == "64":
                        converted_value = operating_state[converted_value]
                    elif register == "73":
                        converted_value = cc_status[converted_value]
                    elif register == "68":
                        if converted_value == 1:
                            converted_value = "Has Active Faults"
                        else:
                            converted_value = "No Active Faults"
                    elif register == "69":
                        if converted_value == 1:
                            converted_value = "Has Active Warnings"
                        else:
                            converted_value = "No Active Warnings"
                    elif register in  ["76","78","88","90"]:
                        converted_value = converted_value / int(extra)
                    elif register in ["80","92"]:
                        converted_value = converted_value
                    elif register == "249":
                        converted_value = solar_association[converted_value]
                    else:
                        # Don't alter converted value
                        converted_value = converted_value

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

class index(Resource):
    def get(self):
        return "Solar monitor API"

api.add_resource(Battery, "/battery", "/battery/<string:instance>")
api.add_resource(Inverter, "/inverter", "/inverter/<string:instance>")
api.add_resource(CC, "/cc", "/cc/<string:instance>")
api.add_resource(index,"/")

if __name__ == "__main__":
    app.run(debug=False)
