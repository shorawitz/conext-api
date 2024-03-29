from flask import Flask
import flask.scaffold, requests, xmltodict
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
        "primary": 12
    },
    "cc": {
        "primary": 30,
        "secondary": 31,
        "tertiary": 170
    }
}

registers_data = {
    "battery": {
        "name": "0,8,0",
        "voltage": "70,2,1000",
        "temp": "74,2,-273",
        "soc": "76,2,0",
        "capacity_remaining": "88,2,0",
        "capacity": "146,1,0"
    },
    "inverter": {
        "name": "0,8,0",
        "state": "64,1,0",
        "enabled": "71,1,0",
        "faults": "75,1,0",
        "warnings": "76,1,0",
        "dc_voltage": "80,2,1000",
        "dc_current": "82,2,1000",
        "dc_power": "84,2,1000",
        "status": "122,1,0",
        "load": "154,2,0",
        "ac1_voltage": "126,2,1000",
        "ac1_qualified_duration": "120,2,0",
        "ac1_power": "132,2,0",
        "ac1_l1_volts": "142,2,1000",
        "ac1_l1_current": "146,2,1000",
        "ac1_l2_volts": "144,2,1000",
        "ac1_l2_current": "148,2,1000",
        "ac1_frequency": "130,2,100",
        "ac2_voltage": "162,2,1000",
        "ac2_qualified_duration": "170,2,0",
        "ac2_power": "172,2,0",
        "ac2_l1_volts": "178,2,1000",
        "ac2_l1_current": "180,2,1000",
        "ac2_l2_volts": "182,2,1000",
        "ac2_l2_current": "184,2,1000",
        "ac2_frequency": "166,2,100"
    },
    "cc": {
        "name": "0,8,0",
        "state": "64,1,0",
        "faults": "68,1,0",
        "warnings": "69,1,0",
        "status": "73,1,0",
        "pvvoltage": "76,2,1000",
        "pvcurrent": "78,2,1000",
        "pvpower": "80,2,0",
        "dcvoltage": "88,2,1000",
        "dccurrent": "90,2,1000",
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
    1038: "Grid Frequency Stabilization",
    1039: "AC Coupling",
    1040: "Reverse lbatt"
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
    779: "Engaging Charger",
    780: "Charger Fault",
    781: "Charger Suspend",
    782: "AC Good",
    783: "APS Good",
    784: "AC Fault",
    785: "Charge",
    786: "Absorption Exit Pending",
    787: "Ground Fault",
    788: "AC Good Pending"
}

solar_association = {
    21: "Solar Array 1",
    22: "Solar Array 2",
    23: "Solar Array 3",
    24: "Solar Array 4"
}

bcc_info = {
    "cell_adj": 0.03,
    "low_cell_adj": 0.03,
    "high_cell_adj": 0.02,
    "pack_adj": 0.45,
    "url": "http://bcc.connect4less.home/bcc.xml"
}

# Get the data from BCC for battery cell data
def get_bcc_values(url):
    try:
        content = requests.get(url, timeout=.2)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    # Convert XML data to dict
    cpm_data = xmltodict.parse(content.text)

    cells_total = 0.0

    # Fix cell voltages
    for i in range(1,17):
        key = 'ucell' + str(i)

        if cpm_data['data'][key] == 'N/A':
            cpm_data['data'][key] = 0
        else:
            cpm_data['data'][key] = float(cpm_data['data'][key])
            cpm_data['data'][key] += bcc_info['cell_adj']

        cells_total += cpm_data['data'][key]
        cpm_data['data'][key] = round(cpm_data['data'][key], 2)

    # Fix pack voltage, mincell and maxcell
    if cpm_data['data']['utotal'] == 'N/A':
        cpm_data['data']['utotal'] = 0
    else:
        cpm_data['data']['utotal'] = float(cpm_data['data']['utotal'])
        cpm_data['data']['utotal'] += bcc_info['pack_adj']

    cpm_data['data']['utotal'] = round(cpm_data['data']['utotal'], 2)

    if cpm_data['data']['Umincell'] == 'N/A':
        cpm_data['data']['Umincell'] = 0
    else:
        cpm_data['data']['Umincell'] = float(cpm_data['data']['Umincell'])
        cpm_data['data']['Umincell'] += bcc_info['low_cell_adj']

    cpm_data['data']['Umincell'] = round(cpm_data['data']['Umincell'], 2)

    if cpm_data['data']['Umaxcell'] == 'N/A':
        cpm_data['data']['Umaxcell'] = 0
    else:
        cpm_data['data']['Umaxcell'] = float(cpm_data['data']['Umaxcell'])
        cpm_data['data']['Umaxcell'] += bcc_info['high_cell_adj']

    cpm_data['data']['Umaxcell'] = round(cpm_data['data']['Umaxcell'], 2)

    # Fill in some extra data
    cpm_data['data']['cell_avg'] = round(cells_total / 16, 2)
    cpm_data['data']['cells_total'] = round(cells_total, 2)
    cpm_data['data']['Udiff'] = round(cpm_data['data']['Umaxcell'] - cpm_data['data']['Umincell'], 2)
    
    return cpm_data

# Get the data from ModBusTCP for the device
def get_modbus_values(device, device_instance):
    devices = device_ids[device]
    register_data = registers_data[device]
    return_data = {}
    print("DEBUG - devices: {}".format(devices))
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
            #print("DEBUG - unit_id: {}, register: {}, reg_len: {}".format(devices[device_key], register, reg_len))
            print("IS OPEN: {}".format(cxt.is_open))
            hold_reg_arr = cxt.read_holding_registers(int(register), int(reg_len))
            test_arr = cxt.read_holding_registers(0, 8)
            print("TEST - test_arr: {}".format(test_arr))
            #print("DEBUG - reg_len: {}".format(reg_len))

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

class BCC(Resource):
    def get(self):
        battery_data = get_bcc_values(url="http://bcc.connect4less.home/bcc.xml")

        if battery_data:
            return battery_data
        
        return {}

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

api.add_resource(BCC, "/bcc/")
api.add_resource(Battery, "/battery", "/battery/<string:instance>")
api.add_resource(Inverter, "/inverter", "/inverter/<string:instance>")
api.add_resource(CC, "/cc", "/cc/<string:instance>")
api.add_resource(index,"/")

if __name__ == "__main__":
    app.run(debug=False)
