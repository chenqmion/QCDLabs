# import nidaqmx
# from nidaqmx.system import System
#
# device = nidaqmx.system.Device("//10.0.100.199/AT1212_0")
# print(device.product_type)
#
# # for device in sys.devices:
# #     print(device.name, device.product_type)

# from nifpga import Session
#
# Session
# resource_address = 'rio://10.0.100.199/AT1212_0'
#
# session =

import pyvisa
rm = pyvisa.ResourceManager()
# visa_resource = 'TCPIP::10.0.100.199::3537::SOCKET'
# visa_resource = 'TCPIP0::10.0.100.199::PXI0::11::INSTR::INSTR'
# # visa_resource = 'visa://10.0.100.199/NI-5654-LO'
#
# instr = rm.open_resource(visa_resource)

# resources = rm.list_resources('visa://10.0.100.199/PXI?*::INSTR')

import nirfsg
visa_resource = 'TCPIP::10.0.100.199::PXI26::15::INSTR'

with nirfsg.Session(resource_name=visa_resource, id_query=False, reset_device=False) as session:
    print('1')
