from distutils.cmd import Command
import paramiko_test
import subprocess
import dearpygui.dearpygui as dpg
import sys
import shared_var
from shared_var import ADC_Value
from shared_var import command
from shared_var import ssh_status


dpg.create_context()
dpg.create_viewport(title='Custom Title', width=1000, height=700)
dpg.setup_dearpygui()

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
    ip = dpg.get_value("ip_addr")
    print("gui ip = ", ip)

    global ssh_status
    print("ssh_status_GUI ", shared_var.ssh_status)
    if(shared_var.ssh_status == "Disconnected"):
        paramiko_test.establish_connection(ip)
    
    if (shared_var.ssh_status == "Connected"):
        dpg.configure_item("ssh_btn", enabled=False)
        dpg.configure_item("ssh_disconnect", enabled=True)

def bbb_disconnect(sender, app_data):
    paramiko_test.end_connection()
    if(shared_var.ssh_status == "Disconnected"):
        dpg.configure_item("ssh_btn", enabled=True)
        dpg.configure_item("ssh_disconnect", enabled=False)


def flash(sender, app_data):
    paramiko_test.flash_MCU()

def can(sender, app_data):
    paramiko_test.test_can()

def default_ip(sender, app_data):
    dpg.set_value("ip_addr", "10.13.11.245")

def eeprom(sender, app_data):
    paramiko_test.test_EEPROM()

with dpg.window(label="Example Window", width=1000, height=700):
    with dpg.group(horizontal=True):    
        with dpg.child_window(label="Data", width=400, height=500):
            dpg.add_text("HEPA-UV TEST")          
            dpg.add_input_text(default_value="10.13.11.245", tag="ip_addr")
            dpg.add_button(label="USE DEFAULT IP ADDRESS", callback=default_ip)
            dpg.add_button(label="CONNECT TO BBB", tag="ssh_btn", callback=bbb_connect)
            dpg.add_button(label="DISCONNECT", tag="ssh_disconnect", callback=bbb_disconnect, enabled=False)           
            
        with dpg.child_window(label="Data 2", width=400, height=500):
            with dpg.table():
                dpg.add_table_column(label="Test")
                dpg.add_table_column(label="Test Output")
                dpg.add_table_column(label="Test Result")
                with dpg.table_row():
                    dpg.add_button(label="24VDC Voltage", callback=button_callback)
                    dpg.add_text(0, tag="Voltage")
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="5V Voltage", callback=ADC2)
                    dpg.add_text(0, tag="ADC2")
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="3.3V Voltage", callback=ADC2)
                    dpg.add_text(0, tag="3V3")
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="5V_AUX Voltage", callback=ADC2)
                    dpg.add_text(0, tag="5VAUX")
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="FLASH MCU", callback=flash)
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="TEST CAN BUS", callback=can)
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="TEST EEPROM", callback=eeprom)
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="TEST UV LIGHT") #ADD CALLBACK
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL")
                with dpg.table_row():
                    dpg.add_button(label="TEST HEPA FAN") #ADD CALLBACK
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL")

            #with dpg.group(horizontal=True): 
            #    dpg.add_button(label="MEASURE VOLTAGE", callback=button_callback)
            #    dpg.add_text(0, tag="Voltage")
            #with dpg.group(horizontal=True): 
            #    dpg.add_button(label="MEASURE ADC2", callback=ADC2)
            #    dpg.add_text(0, tag="ADC2")

            

with dpg.theme() as disabled_theme:
    with dpg.theme_component(dpg.mvButton, enabled_state=False):
        dpg.add_theme_color(dpg.mvThemeCol_Text, [128, 128, 128])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [50, 50, 50])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [50, 50, 50])

dpg.bind_theme(disabled_theme)

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
