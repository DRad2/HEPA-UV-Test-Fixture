from distutils.cmd import Command
import paramiko_test
import subprocess
import dearpygui.dearpygui as dpg
import sys
from shared_var import ADC_Value
from shared_var import command



dpg.create_context()
dpg.create_viewport(title='Custom Title', width=600, height=300)


#ADC_Value = 0

def button_callback(sender, app_data):
    global ADC_Value 
    global command
   
    command = "python ADC_send.py"
    print("Command: ", command)
    ADC_Value = paramiko_test.get_ADC_value(command)

    dpg.set_value("Voltage", ADC_Value)

def ADC2(sender, app_data):
    global ADC_Value
    global command 

    command = "python ADC_send2.py"
    print("Command: ", command)
    ADC_Value = paramiko_test.get_ADC_value(command)
    dpg.set_value("ADC2", ADC_Value)

def bbb_connect(sender, app_data):
    paramiko_test.establish_connection()

def bbb_disconnect(sender, app_data):
    paramiko_test.end_connection()

def flash(sender, app_data):
    paramiko_test.flash_MCU()

with dpg.window(label="Example Window"):
    dpg.add_text("HEPA-UV TEST")
    dpg.add_button(label="MEASURE VOLTAGE", callback=button_callback)
    dpg.add_button(label="MEASURE ADC2", callback=ADC2)
    dpg.add_button(label="CONNECT TO BBB", callback=bbb_connect)
    dpg.add_button(label="DISCONNECT", callback=bbb_disconnect)
    dpg.add_button(label="FLASH MCU", callback=flash)
    dpg.add_text(0, tag="Voltage")
    dpg.add_text(0, tag="ADC2")
    dpg.add_input_text(label="V")


dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
