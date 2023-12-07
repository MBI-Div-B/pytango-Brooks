#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-


""" BrooksSLA PyTango Class (Serial connection)

Class for controlling Bronkhorst Pressure/Flow controller via serial connection

Author = Martin Hennecke
"""

# PyTango imports
from tango import DevState, AttrWriteType, DeviceProxy
from tango.server import run, Device, attribute, command, device_property
# Additional import
import Brooks_TS as b
from enum import IntEnum

class ValveState(IntEnum):
    controlled = 0
    open = 1
    closed = 2
    unknown = 3


__all__ = ["BrooksSLA", "main"]


class BrooksSLA(Device):
    # -----------------
    # Device Properties
    # -----------------

    Port = device_property(
        dtype='DevString',
        doc='e.g., /dev/ttyBrooks'
    )
    
    ID = device_property(
        dtype='DevString',
        doc='12345678'
    )

    # ----------
    # Attributes
    # ----------
    
    Valve = attribute(
        label = 'Valve state',
        dtype = ValveState,
        access =  AttrWriteType.READ
    )

    Setpoint_p = attribute(
	label = 'Setpoint[%]',
        dtype='DevDouble',
        access = AttrWriteType.READ_WRITE,
        unit= '%',
        memorized = False,
        hw_memorized = True,
    )

    Setpoint_u = attribute(
	label = 'Setpoint',
        dtype='DevDouble',
        access = AttrWriteType.READ_WRITE,
        unit= 'mbar',
        memorized = False,
        hw_memorized = True,
    )
    
    Readback = attribute(
        dtype = 'DevDouble',
        access = AttrWriteType.READ,
        unit = "mbar",
    )
    

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        """Initialises the attributes and properties of the BrooksSLA."""
        self.info_stream("init_device()")
        Device.init_device(self)
        self.set_state(DevState.INIT)
              
        try:
            self.info_stream("Connecting on port: {:s}".format(self.Port))
            # connect to device
            self.sla = b.Brooks(self.ID, self.Port)
            self.info_stream("Connected to device ID: {:s}".format(self.ID))
        except:
            self.error_stream("Could not connect to device ID {:s} on port {:s}!".format(self.ID, self.Port))
            self.set_status("The device is in OFF state")
            self.set_state(DevState.OFF)
        
        self.sla.set_flow_percent(0)
        self.__setpoint_p = self.sla.get_flow()[0]

        self.__valvestate = 2 # initilize with closed valve        
        self.sla.set_ValveStatus(self.__valvestate)
           
        self.set_status("The device is in ON state")
        self.set_state(DevState.ON)
        
        # read units from device
        attSp = self.get_device_attr().get_attr_by_name("Setpoint_u")
        attSp_prop = attSp.get_properties()
        attSp_prop.unit = self.read_Unit()
        attSp.set_properties(attSp_prop)
        
        attRb = self.get_device_attr().get_attr_by_name("Readback")
        attRb_prop = attRb.get_properties()
        attRb_prop.unit = self.read_Unit()
        attRb.set_properties(attRb_prop)
        

    def always_executed_hook(self):
        """Method always executed before any TANGO command is executed."""


    def delete_device(self):
        self.set_status("The device is in OFF state")
        self.set_state(DevState.OFF)
    

    # ------------------
    # Attributes methods
    # ------------------
    
    def read_Valve(self):
        self.__valvestate = self.sla.get_ValveStatus()
        if self.__valvestate == 0:
            # print('read: ' + str(self.sla.get_ValveStatus()))
            self.set_status('Valve is in controlled mode')
            #self.set_state(DevState.RUNNING)
            return ValveState.controlled
        
        elif self.__valvestate == 1:
            # print('read: ' + str(self.sla.get_ValveStatus()))
            self.set_status('Valve is open')
            self.set_state(DevState.OPEN)
            return ValveState.open    
        
        elif self.__valvestate == 2:
            # print('read: ' + str(self.sla.get_ValveStatus()))
            self.set_status('Valve is closed')
            #self.set_state(DevState.CLOSE)
            return ValveState.closed
        
        elif self.__valvestate == 3:
            # print('read: ' + str(self.sla.get_ValveStatus()))
            self.set_status('Valve is in unkown state')
            #self.set_state(DevState.UNKOWN)
            return ValveState.unkown
        
        return self.__valvestate    

        
    def read_Readback(self):
        return self.sla.read_flow()
        
    def read_Setpoint_p(self):
        self.__setpoint_p = self.sla.get_flow()[0]
        return  self.__setpoint_p

    def read_Setpoint_u(self):
        self.__setpoint_u = self.sla.get_flow()[1]
        return  self.__setpoint_u
    
    def write_Setpoint_p(self, value):
        self.sla.set_flow_percent(value)

    def write_Setpoint_u(self, value):
        self.sla.set_flow_unit(value)
        

    # --------
    # Commands
    # --------

    # def dev_state(self):
    #     self.set_status("The device is in ON state")
    #     self.debug_stream("device state: ON")
    #     return DevState.ON
    
    def read_Unit(self): #TS
        return self.sla.read_OpSettings()[1]
    
    @command
    def Control(self):
        self.sla.set_ValveStatus(0)
    
    @command
    def Open(self):
        self.sla.set_ValveStatus(1)
    
    @command
    def Close(self):
        self.sla.set_ValveStatus(2)
        

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    return run((BrooksSLA,), args=args, **kwargs)


if __name__ == '__main__':
    main()
