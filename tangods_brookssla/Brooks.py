#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 15:18:18 2022

@author: TS
"""

""" Driver for Brooks s-protocol """
import time
import struct
import logging
import serial
from six import b, indexbytes


class Brooks(object):
    __PressureUnits = {1: 'ln of H2O', 2: 'ln of Hg', 3: 'Ft of H2O', 6: 'PSI', 7: 'bar', 8: 'mbar', 11: 'Pa', 12: 'kPa', 13: 'Torr',
                         14: 'std. atm.', 240: 'kg/cm2', 241: 'mTorr', 242: 'mm Hg', 243: 'gr/cm2', 244: 'cm of H2O'}

    __TemperatureUnits = {32: 'Celsius', 33: 'Fahrenheit', 34: 'Udefined', 35: 'Kelvin'}

    __DensityUnits = {91: 'g/cm3', 92: 'kg/cm3', 93: 'lb/gal', 94: 'lb/ft3', 95: 'g/ml', 96: 'kg/l', 97: 'g/l', 98: 'lb/in3'}
    
    def Units(self, unitCode, parameter):
        """ Convert unit code to unit """
        try: 
            unit = parameter[unitCode]
        except NameError: 
            unit = 'Undefined'
        return unit
                
    
    """ Driver for Brooks s-protocol """
    def __init__(self, device, port='/dev/ttyBrooks'):
        self.ser = serial.Serial(port, 19200)
        self.ser.parity = serial.PARITY_ODD
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.stopbits = serial.STOPBITS_ONE
        deviceid = self.comm('8280000000000b06'
                             + self.pack(device[-8:]))
        manufactor_code = '0a'
        device_type = deviceid[12:14]
        # print(device_type)
        long_address = manufactor_code + device_type + deviceid[-6:]
        self.long_address = long_address
        # print(long_address)

    def pack(self, input_string):
        """ Turns a string in packed-ascii format """
        #This function lacks basic error checking....
        klaf = ''
        for s in input_string:
            klaf += bin((ord(s) % 128) % 64)[2:].zfill(6)
        result = ''
        for i in range(0, 6):
            result = result + hex(int('' + klaf[i * 8:i * 8 + 8],
                                      2))[2:].zfill(2)
        return result

    def crc(self, command):
        """ Calculate crc value of command """
        i = 0
        while command[i:i + 2] == 'FF':
            i += 2
        command = command[i:]
        n = len(command)
        result = 0
        for i in range(0, (n//2)):
            byte_string = command[i*2:i*2+2]
            byte = int(byte_string, 16)
            result = byte ^ result
        return hex(result)

    def comm(self, command):
        """ Implements low-level details of the s-protocol """
        check = str(self.crc(command))
        check = check[2:].zfill(2)
        final_com = 'FFFFFFFFFFFFFFFF' + command + check # minimum of 5 preamable cahracters "FF"
        # print(final_com)
        bin_comm = ''
        for i in range(0, len(final_com) // 2):
            bin_comm += chr(int(final_com[i * 2:i * 2 + 2], 16))
        bin_comm += chr(0)
        bytes_for_serial = b(bin_comm)
        # print(bytes_for_serial)
        error = 1
        while (error > 0) and (error < 10):
            self.ser.write(bytes_for_serial)
            time.sleep(0.3)
            s = self.ser.read(self.ser.inWaiting())
            # print(s)
            st = ''
            for i in range(0, len(s)):
                #char = hex(ord(s[i]))[2:].zfill(2)
                #char = hex(s[i])[2:].zfill(2)
                char = hex(indexbytes(s, i))[2:].zfill(2)
                if not char.upper() == 'FF':
                    st = st + char
            # print("response:" + st)     
            try:
                # delimiter = st[0:2]
                # address = st[2:12]
                command = st[12:14]
                byte_count = int(st[14:16], 16)
                response = st[16:16 + 2 * byte_count]
                error = 0
            except ValueError:
                error = error + 1
                response = 'Error'
        # print(response)        
        return response
    
    def read_flow(self):
        """ Read the current flow-rate #1"""
        response = self.comm('82' + self.long_address + '0100')
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            unit_code = int(response[4:6], 16)
            flow_code = response[6:]
            byte0 = chr(int(flow_code[0:2], 16))
            byte1 = chr(int(flow_code[2:4], 16))
            byte2 = chr(int(flow_code[4:6], 16))
            byte3 = chr(int(flow_code[6:8], 16))
            flow = struct.unpack('>f', b(byte0 + byte1 + byte2 + byte3)) # 'f' is IEEE 754 byte conversion same as BROOKS uses
            value = flow[0]
        except ValueError:
            value = -1
            unit_code = 171  # Satisfy assertion check, we know what is wrong
#        assert unit_code == 171  # Flow unit should always be mL/min
#	print('read flow: ' + value)
        return value
    
    def read_AddTransmitterInfo(self):
        """ Read additional transmitter status #48"""
        response = self.comm('82' + self.long_address + '3000')
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            status_byte0 = response[4:6]
            status_byte1 = response[6:8]
            status_byte2 = response[8:10]
            status_byte3 = response[10:12]
            
        except ValueError:
            status_byte1 = status_byte1 =  status_byte2 = status_byte3 = -1
            
        return status_byte0, status_byte1, status_byte2, status_byte3

    def read_DynVarAssign(self):
        """ Read the Dynamic Variable Assignments #50"""
        response = self.comm('82' + self.long_address + '3200')
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            prime_var = response[4:6]
            sec_var = response[6:8]
            tert_var = response[8:10]
            quat_var = response[10:12]
            
        except ValueError:
            prime_var = sec_var = tert_var = quat_var = -1
            
        return prime_var, sec_var, tert_var, quat_var
    
    # def read_full_range(self): #not implemented
    #      """
    #      Report the full range of the device
    #      Apparantly this does not work for SLA-series...
    #      """
    #      response = self.comm('82' + self.long_address + '980101')#Command 152
    #      # Double check what gas-selection code really means...
    #      # currently 01 is used
    #      # status_code = response[0:4]
    #      unit_code = int(response[4:6], 16)
    # #      assert unit_code == 171 #Flow controller should always be set to mL/min

    #      flow_code = response[6:]
    #      byte0 = chr(int(flow_code[0:2], 16))
    #      byte1 = chr(int(flow_code[2:4], 16))
    #      byte2 = chr(int(flow_code[4:6], 16))
    #      byte3 = chr(int(flow_code[6:8], 16))
    #      max_flow = struct.unpack('>f', byte0 + byte1 + byte2 + byte3)
    #      return max_flow[0]
    
    def read_ProcGas(self, gas_code):
        """ Read the process gas type #150"""
        response = self.comm('82' + self.long_address + '96010' + str(gas_code))
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            gas_code = response[4:6]
            gas_name = bytes.fromhex( response[6:] ).decode('utf-8')
            
        except ValueError:
            gas_name = -1
            
        return gas_name
    
    def read_FullPressureRange(self, appl_select):
        """ Read the full scale pressure range #159 """
        response = self.comm('82' + self.long_address + '9F010' + str(appl_select))
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            press_unit = int(response[4:6], 16)
            full_press = int(response[6:], 16)

        except ValueError:
            press_unit = full_press = -1
            
        return self.Units(press_unit, self.__PressureUnits), full_press
    
    def read_CalibPressureRange(self):#, appl_select): #returned values don't make sense
        """ Read the calibrated pressure range #179 """
        response = self.comm('82' + self.long_address + 'B300')# + str(appl_select) )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            press_unit = response[4:6]
            full_press = int(response[6:], 16)

        except ValueError:
            press_unit = full_press = -1
            
        return response#self.Units(press_unit, self.__PressureUnits), full_press

    def read_StandTempPress(self):
        """ Read standard temperature and pressure #190 """
        response = self.comm('82' + self.long_address + 'BE00' )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            
            temp_unit = int(response[4:6], 16) # typically 35 = Kelvin
            byte1 = chr(int(response[6:8], 16))
            byte2 = chr(int(response[8:10], 16))
            byte3 = chr(int(response[10:12], 16))
            byte4 = chr(int(response[12:14], 16))
            temp = struct.unpack('>f', b(byte1 + byte2 + byte3 + byte4)) # 'f' is IEEE 754 byte conversion same as BROOKS uses
            
            press_unit = int(response[14:16], 16) # typically 11 = Pascal
            byte6 = chr(int(response[16:18], 16))
            byte7 = chr(int(response[18:20], 16))
            byte8 = chr(int(response[20:22], 16))
            byte9 = chr(int(response[22:24], 16))
            press = struct.unpack('>f', b(byte6 + byte7 + byte8 + byte9)) # 'f' is IEEE 754 byte conversion same as BROOKS uses

        except ValueError:
            temp_unit = temp = press_unit = press = -1
            
        return  self.Units(temp_unit, self.__TemperatureUnits), temp, self.Units(press_unit, self.__PressureUnits), press  
     
    def read_OpSettings(self):
        """ Read operational settings pressure #192 """
        response = self.comm('82' + self.long_address + 'C000' )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            press_appl = response[4:6]
            press_unit = int(response[6:8], 16)
            press_ref = response[8:10]
            press_mode = response[10:12]
            press_control = response[12:14]
            
            if response[2:4] == '14':
                responseExt = self.comm('82' + self.long_address + '3000' )
                print('Extra response #48: ' + responseExt[4:])

        except ValueError:
            press_appl = press_unit = press_ref = press_mode = press_control = -1
            
        return press_appl, self.Units(press_unit, self.__PressureUnits), press_ref, press_mode, press_control
    
    
    def set_PressAppl(self, appl_select):
        """ Set the pressure application #194 """
        response = self.comm('82' + self.long_address + 'C2010' + str(appl_select) )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            press_appl = response[4:6]

        except ValueError:
            press_appl = -1

        return press_appl
    
    def set_PressureUnit(self, unit_code):
        """ Set the pressure unit #198 """
        response = self.comm('82' + self.long_address + 'C601' + f'{unit_code:02x}' )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            press_unit = int(response[4:], 16)

        except ValueError:
            press_unit = -1

        return  self.Units(press_unit, self.__PressureUnits)
    
#     def set_PressFlowMode(self, mode):# not implemented? Status code 4004
#         """ Set pressure of flow control #199 """
#         response = self.comm('82' + self.long_address + 'C7010' + str(mode) )
#         try:  # TODO: This should be handled be re-sending command
#             status_code = response[0:4]
#             press_unit = response[4:]
# 
#         except ValueError:
#             value = -1
#             unit_code = 171  # Satisfy assertion check, we know what is wrong
#  #        assert unit_code == 171  # Flow unit should always be mL/min
#         return response

    def get_ValveRangeOffset(self):
        """ Get the Valve range #222 """
        response = self.comm('82' + self.long_address + 'DE00' )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            valve_range = response[4:10]
            valve_offset = response[10:16]

        except ValueError:
            valve_status = -1

        return valve_range, valve_offset
    
    
    def get_ValveStatus(self):
        """ Set the pressure unit #230 """
        response = self.comm('82' + self.long_address + 'E600' )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            valve_status = int(response[4:], 16)

        except ValueError:
            valve_status = -1

        return valve_status
    
    def set_ValveStatus(self, valve_status ):
        """ Set the pressure unit #231 """
        response = self.comm('82' + self.long_address + 'E7010' + str(valve_status))
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            valve_status = response[4:]

        except ValueError:
            valve_status = -1

        return valve_status
    
    def get_flow(self):
        """ Get the setpoint of the flow #235 """
        response = self.comm('82' + self.long_address + 'eb00' )
        try:    # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            byte1 = chr(int(response[6:8], 16))
            byte2 = chr(int(response[8:10], 16))
            byte3 = chr(int(response[10:12], 16))
            byte4 = chr(int(response[12:14], 16))
            flowPercent = struct.unpack('>f', b(byte1 + byte2 + byte3 + byte4)) # 'f' is IEEE 754 byte conversion same as BROOKS uses
            
            byte6 = chr(int(response[16:18], 16))
            byte7 = chr(int(response[18:20], 16))
            byte8 = chr(int(response[20:22], 16))
            byte9 = chr(int(response[22:24], 16))
            flow = struct.unpack('>f', b(byte6 + byte7 + byte8 + byte9)) # 'f' is IEEE 754 byte conversion same as BROOKS uses
      
        except ValueError:
            flowPercent[0] = flow[0] = -1
            
        return flowPercent[0], flow[0]
    
    def set_flow_percent(self, flowrate):
        """ Set the setpoint of the flow #236 """
        ieee = struct.pack('>f', flowrate)
        ieee_flowrate = ''
        for i in range(0, 4):
            ieee_flowrate += hex(ieee[i])[2:].zfill(2)
        #0x39 = unit code for percent
        #0xFA = unit code for 'same unit as flowrate measurement'
        response = self.comm('82' + self.long_address + 'ec05' + '39' + ieee_flowrate)
        status_code = response[0:4]
        unit_code = int(response[4:6], 16)
        byte1 = chr(int(response[6:8], 16))
        byte2 = chr(int(response[8:10], 16))
        byte3 = chr(int(response[10:12], 16))
        byte4 = chr(int(response[12:14], 16))
        setpointPercent = struct.unpack('>f', b(byte1 + byte2 + byte3 + byte4)) # 'f' is IEEE 754 byte conversion same as BROOKS uses
        
        setpointUnit = int(response[14:16], 16)
        byte6 = chr(int(response[16:18], 16))
        byte7 = chr(int(response[18:20], 16))
        byte8 = chr(int(response[20:22], 16))
        byte9 = chr(int(response[22:24], 16))
        setpoint = struct.unpack('>f', b(byte6 + byte7 + byte8 + byte9)) # 'f' is IEEE 754 byte conversion same as BROOKS uses

        return status_code, unit_code, setpointPercent, self.Units(setpointUnit, self.__PressureUnits), setpoint[0]
    
    def set_flow_unit(self, flowrate):
        """ Set the setpoint of the flow #236 """
        ieee = struct.pack('>f', flowrate)
        ieee_flowrate = ''
        for i in range(0, 4):
            ieee_flowrate += hex(ieee[i])[2:].zfill(2)
        #0x39 = unit code for percent
        #0xFA = unit code for 'same unit as flowrate measurement'
        response = self.comm('82' + self.long_address + 'ec05' + 'FA' + ieee_flowrate)
        status_code = response[0:4]
        unit_code = int(response[4:6], 16)
        byte1 = chr(int(response[6:8], 16))
        byte2 = chr(int(response[8:10], 16))
        byte3 = chr(int(response[10:12], 16))
        byte4 = chr(int(response[12:14], 16))
        setpointPercent = struct.unpack('>f', b(byte1 + byte2 + byte3 + byte4)) # 'f' is IEEE 754 byte conversion same as BROOKS uses
        
        setpointUnit = int(response[14:16], 16)
        byte6 = chr(int(response[16:18], 16))
        byte7 = chr(int(response[18:20], 16))
        byte8 = chr(int(response[20:22], 16))
        byte9 = chr(int(response[22:24], 16))
        setpoint = struct.unpack('>f', b(byte6 + byte7 + byte8 + byte9)) # 'f' is IEEE 754 byte conversion same as BROOKS uses

        return status_code, unit_code, setpointPercent, self.Units(setpointUnit, self.__PressureUnits), setpoint[0]

    def get_ValveRange(self):
        """ Get the Valve range #237 """
        response = self.comm('82' + self.long_address + 'ED00' )
        try:  # TODO: This should be handled be re-sending command
            status_code = response[0:4]
            valve_range = int(response[4:], 16)

        except ValueError:
            valve_status = -1

        return valve_range, valve_range/62500


if __name__ == '__main__':
    # BROOKS = Brooks('04101967')
    BROOKS = Brooks('31700995')
    # print(BROOKS.long_address)
    # print("Flowrate: " + str(BROOKS.read_flow()) )
    # print("Status Bytes (0, 1, 2, 3): " + str(BROOKS.read_AddTransmitterInfo()) )
    # print("Dynamic Variables (1st, 2nd, 3rd, 4th): " + str(BROOKS.read_DynVarAssign()) )
    # print('Process Gas: ' + str(BROOKS.read_ProcGas(1)) )
    # print('Pressure range (unit, value): ' + str(BROOKS.read_FullPressureRange(2)) )
    # print('Pressure range (unitCode, value): ' + str(BROOKS.read_CalibPressureRange(2)) )
    # print('Standard values (TempUnit, Temp, PressureUnit, Pressure) ' + str(BROOKS.read_StandTempPress()) )
    # print('Pressure Settings (Application, Code, Reference, Mode, Control): ' + str(BROOKS.read_OpSettings()) )
    # print('Pressure Application: ' + str(BROOKS.set_PressAppl(2)) )
    # print('Set Pressure Unit: ' + str(BROOKS.set_PressureUnit(8)) )
    # print('Set Control Mode: ' + str(BROOKS.set_PressFlowMode(0)) ) # not implemented ?
    # print('Valve Status: ' + str(BROOKS.get_ValveStatus()) )
    # print('Valve Status: ' + str(BROOKS.set_ValveStatus(2)) )
    # print('Get Setpoint: ' + str(BROOKS.get_flow()[1]) )
    # print(BROOKS.set_flow(10))
    # BROOKS.ser.close()
    

        