#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-


""" BrooksSLA PyTango Class (Serial connection)

Class for controlling Bronkhorst Pressure/Flow controller via serial connection

Author = Martin Hennecke
"""

# PyTango imports
from tango import DevState, AttrWriteType
from tango.server import run, Device, attribute, device_property
# Additional import
import Brooks as b


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

    Setpoint = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ_WRITE,
        unit="mbar",
        memorized=True,
        hw_memorized=True,
    )
    Readback = attribute(
        dtype='DevDouble',
        access=AttrWriteType.READ,
        unit="mbar",
    )
    PID_enable = attribute(
        label='PID enable',
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
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
        
        self.__pid_enable = False
        
        self.set_status("The device is in ON state")
        self.set_state(DevState.ON)


    def always_executed_hook(self):
        """Method always executed before any TANGO command is executed."""

    def delete_device(self):
        self.set_status("The device is in OFF state")
        self.set_state(DevState.OFF)
        

    # ------------------
    # Attributes methods
    # ------------------

    def read_Readback(self):
        return self.sla.read_flow()

    def read_Setpoint(self):
        return self.__setpoint     
    
    def write_Setpoint(self, value):
        self.sla.set_flow(value*self.__pid_enable)
        self.__setpoint=value
        
    def read_PID_enable(self):
        return self.__pid_enable     
    
    def write_PID_enable(self, value):
        self.__pid_enable=value
        self.write_Setpoint(self.__setpoint)

    # --------
    # Commands
    # --------

    def dev_state(self):
        self.set_status("The device is in ON state")
        self.debug_stream("device state: ON")
        return DevState.ON


# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    return run((BrooksSLA,), args=args, **kwargs)


if __name__ == '__main__':
    main()
