import csv
from datetime import datetime
from csv import unregister_dialect
from distutils.cmd import Command
import paramiko
import subprocess
import dearpygui.dearpygui as dpg
import sys
import time

ssh = paramiko.SSHClient()

global file_name
global test_fail 
global flash_status
test_fail = False 

##############################
# BEAGLEBONE BLACK INTERFACE
##############################

def establish_connection(ip):
    try:
        # Define SSH connection parameters
        ip_address = "ip: " + ip
        write_console(ip_address)
        host = ip               # BBB's IP address
        username = "debian"     # BBB username
        password = "temppwd"    # BBB password
        # Initialize an SSH client
        write_console("Connecting...")
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Connect to the BBB
        ssh.connect(host, username=username, password=password)
        write_console("Connected")

    except paramiko.AuthenticationException:
        write_console("Authentication failed")
    except paramiko.SSHException as e:
        write_console(f"SSH connection failed: {str(e)}")
    except Exception as e:
        write_console(f"An error occurred: {str(e)}")

def end_connection():
    write_console("Disconnecting...")
    ssh.close()  

def get_ADC_value(command):
    global ADC_Value
   
    # Execute command
    stdin, stdout, stderr = ssh.exec_command(command)

    # Read the output as a single string
    ADC_Value = stdout.read(30).decode("utf-8")
         
    del stdin, stdout, stderr  
    return ADC_Value

def flash_MCU():
    
    flashed = False
    # Execute command
    stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python simple_flash.py")
    
    # Get results
    msg = (stdout.read().decode("utf-8"))
    lines = msg.split('\n')
    for line in lines:
        write_console(line)
        if "MCU flashed successfully." in line:
            flashed = True
    
    del stdin, stdout, stderr  
    return flashed

def test_can():
    sent = None 
    received = None
    can_OK = False
    
    # Execute command
    #stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python can_test.py")
    stdin, stdout, stderr = ssh.exec_command("python can_test.py")
    write_console("Command sent to BBB")

    # Get the results
    msg = (stdout.read().decode("utf-8"))
    write_console(msg)

    lines = msg.split('\n')
    for line in lines:
        if "can1  5A1" in line:
            sent = line.split("[8]")[1].strip()
        elif "can1  00000023" in line:
            received = line.split("[8]")[1].strip()

    # Print results on the console
    msg_sent = "Message Sent to MCU: "+sent
    msg_received = "Message Received from MCU (expected = sent message incremented by 1): "+received
    write_console(msg_sent)
    write_console(msg_received)

    sent_bytes = sent.split()
    received_bytes = received.split()

    #print("sent_bytes: ", sent_bytes)
    #print("received_bytes: ", received_bytes)

    # Compare sent and received messages
    can_count = 0
    for i, (sent_byte, received_byte) in enumerate(zip(sent_bytes, received_bytes)):
        sent_byte = sent_byte.strip("'")
        received_byte = received_byte.strip("'")
        if int(sent_byte, 16) + 1 == int(received_byte, 16):
            can_count += 1
    
    if can_count == 8:
        can_OK = True
    else: 
        can_OK = False
    can_count = 0
    
    del stdin, stdout, stderr
    return can_OK
    

def test_EEPROM():
    write_console("EEPROM test started")
    written_data = None
    read_data = None
    eeprom_OK = False

    # Execute command
    stdin, stdout, stderr = ssh.exec_command("python EEPROM_test.py")
    write_console("Command sent to BBB")
    
    # Get the results
    msg = (stdout.read().decode("utf-8"))
    #print(msg)
    write_console(msg)

    lines = msg.split('\n')
    for line in lines[5:]:  # Consider the last two lines
        if "can1  00000023" in line:
            value = line.split("[8]")[1].strip()
            if written_data is None:
                written_data = value
            elif read_data is None:
                read_data = value
    
    # Write results on the console:
    msg_written_data = "Data written to EEPROM: " + written_data
    msg_read_data = "Data read from EEPROM: " + read_data
    write_console(msg_written_data)
    write_console(msg_read_data)

    # Compare data written and data read back from the EEPROM: 
    if (written_data == read_data):
        eeprom_OK = True
    else:
        eeprom_OK = False
    
    del stdin, stdout, stderr
    return eeprom_OK

def UV_light_button_push():
    # Execute command
    stdin, stdout, stderr = ssh.exec_command("python UV_pushbutton.py")
    del stdin, stdout, stderr  

def open_door():
    write_console("Opening Door...")
    # Execute command
    stdin, stdout, stderr = ssh.exec_command("python open_door_sw.py")
    write_console("Door Open")
    del stdin, stdout, stderr  
    door_open = True
    return door_open

def close_door():
    write_console("Closing Door...")
    stdin, stdout, stderr = ssh.exec_command("python close_door_sw.py")
    del stdin, stdout, stderr  
    write_console("Door Closed")
    door_closed = True
    return door_closed

def HEPA_fan_button_push():
    stdin, stdout, stderr = ssh.exec_command("python HEPA_pushbutton.py")
    del stdin, stdout, stderr



##############################
# GUI
##############################
dpg.create_context()
dpg.create_viewport(title='Custom Title', width=1000, height=700)
dpg.setup_dearpygui()

def read_24V(sender, app_data):
    write_console("24V RAIL VOLTAGE TEST START")
    global file_name 
    global test_fail
    # Execute Command
    command = "python get_24V.py"
    ADC_Value = get_ADC_value(command)

    # Print Results
    ADC_float = round(float(ADC_Value),3)
    msg = "24VDC: "+str(ADC_float)
    write_console(msg)
    dpg.set_value("24V", ADC_float) 
    if 23.52 <= ADC_float <= 24.48: #+-2%
        dpg.bind_item_theme("24V_RESULT", pass_theme)
        write_console("24V RAIL VOLTAGE TEST PASSED")
    else: 
        test_fail = True
        dpg.bind_item_theme("24V_RESULT", fail_theme)
        write_console("24V RAIL VOLTAGE TEST FAILED")
    write_console_end_section()

    # Write to csv file:
    #file = open(file_name, 'a', newline ='')
    #print("function file name = ", file_name)
    #with file:    
    #    #writer = csv.DictWriter(file, fieldnames=fieldnames)    
    #    writer = csv.writer(file)
    #    writer.writerow(["24V Test"])

def read_5V(sender, app_data):
    write_console("5V RAIL VOLTAGE TEST START")
    global test_fail 
    # Execute command
    command = "python get_5V.py"
    ADC_Value = get_ADC_value(command)
    # Print results
    ADC_float = round(float(ADC_Value),3)
    dpg.set_value("5V", ADC_float) 
    msg = "5VDC: "+str(ADC_float)
    write_console(msg)
    if 4.90 <= ADC_float <= 5.10: #+-2%
        dpg.bind_item_theme("5V_RESULT", pass_theme)
        write_console("5V RAIL VOLTAGE TEST PASSED")
    else:
        test_fail = True
        dpg.bind_item_theme("5V_RESULT", fail_theme)
        write_console("5V RAIL VOLTAGE TEST FAILED")
    write_console_end_section()

def read_3V3(sender, app_data):
    write_console("3.3V RAIL VOLTAGE TEST START")
    global test_fail  
    # Execute command
    command = "python get_3V3.py"
    ADC_Value = get_ADC_value(command)
    # Print resultS
    ADC_float = round(float(ADC_Value),3)
    msg = "3.3VDC: "+str(ADC_float)
    write_console(msg)
    dpg.set_value("3V3", ADC_float) 
    if 3.263 <= ADC_float <= 3.366: #+-2%
        dpg.bind_item_theme("3V3_RESULT", pass_theme)
        write_console("3.3V RAIL VOLTAGE TEST PASSED")
    else:
        test_fail = True
        dpg.bind_item_theme("3V3_RESULT", fail_theme)
        write_console("3.3V RAIL VOLTAGE TEST FAILED")
    write_console_end_section()

def read_5Vaux(sender, app_data):
    write_console("5V_AUX RAIL VOLTAGE TEST START")
    global test_fail 
    # Execute command
    command = "python get_5Vaux.py"
    ADC_Value = get_ADC_value(command)
    # Print results
    ADC_float = round(float(ADC_Value),3)
    msg = "5VauxDC: "+str(ADC_float)
    write_console(msg)
    dpg.set_value("5VAUX", ADC_float) 
    if 4.9 <= ADC_float <= 5.1: #+-2%
        dpg.bind_item_theme("5Vaux_RESULT", pass_theme)
        write_console("5V_AUX RAIL VOLTAGE TEST PASSED")
    else: 
        test_fail = True
        dpg.bind_item_theme("5Vaux_RESULT", fail_theme)
        write_console("5V_AUX RAIL VOLTAGE TEST START")
    write_console_end_section()

def read_UV_current():
    write_console("Running UV Current Sense Test")
    global test_fail  
    # Execute command
    command = "python UV_sns.py"
    ADC_Value = get_ADC_value(command)
    # Print results
    ADC_float = round(float(ADC_Value),3)
    msg = "UV Current ADC Value: "+str(ADC_float)
    write_console(msg)
    if 1.3 <= ADC_float: #With Rsns=100mR, Current Sense Op-Amp will saturate to rail voltage. Change to 25mR Rsns in next rev.
        UV_ON = True
    else:
        UV_ON = False
    return UV_ON

def bbb_connect(sender, app_data):
    reset_results()
    ip = dpg.get_value("ip_addr")
    dpg.configure_item("ssh_btn", enabled=False)
    establish_connection(ip)
    dpg.configure_item("ssh_disconnect", enabled=True)
    dpg.bind_item_theme("run_test", test_run_theme)
    write_console_end_section()


def bbb_disconnect(sender, app_data):
    dpg.configure_item("ssh_disconnect", enabled=False)
    end_connection()
    dpg.configure_item("ssh_btn", enabled=True)
    write_console("Disconnected")
    write_console_end_section()    

def flash(sender, app_data):
    write_console("MCU FLASH STARTED")
    global test_fail
    
    # Execute command
    flashed = flash_MCU()

    # Print results
    if flashed:
        write_console("MCU FLASHED")
        dpg.bind_item_theme("FLASH_RESULT", pass_theme)
    else: 
        write_console("MCU FLASH FAILED")
        dpg.bind_item_theme("FLASH_RESULT", fail_theme)
        test_fail = True
    write_console_end_section()

def can(sender, app_data):
    write_console("CAN BUS TEST STARTED")
    global test_fail

    # Execute Command
    can_OK = test_can()

    # Print Results
    if can_OK: 
        write_console("CAN BUS OK")
        dpg.bind_item_theme("CAN_RESULT", pass_theme)
    else: 
        test_fail = True
        write_console("CAN BUST TEST FAILED")
        dpg.bind_item_theme("CAN_RESULT", fail_theme)
    write_console_end_section()

def default_ip(sender, app_data):
    dpg.set_value("ip_addr", "10.13.11.245")

def eeprom(sender, app_data):
    global test_fail
    # Execute command
    eeprom_OK = test_EEPROM()
    
    # Print results
    if eeprom_OK: 
        write_console("EEPROM OK")
        dpg.bind_item_theme("EEPROM_RESULT", pass_theme)
    else: 
        test_fail = True
        write_console("EEPROM TEST  FAILED")
        dpg.bind_item_theme("EEPROM_RESULT", fail_theme)
    write_console_end_section()

def UV_light(sender, app_data):
    global test_fail
    test_fail = False
    door_open = None
    door_closed = None
    write_console("UV light test start")
    #Open Door
    door_open = open_door()

    # Attempt test with door open
    if door_open:
        write_console("Attempting UV Test")
        # Press the UV_pushbutton
        UV_light_button_push()  
        time.sleep(3)
        # Measure UV load current
        UV_ON = read_UV_current()
        # Print results
        if not UV_ON:
            write_console("DOOR OPEN - UV is OFF")
        else: 
            write_console("ERROR: DOOR OPEN - UV ON")
            write_console("Stopping Test") 
            dpg.bind_item_theme("UV_RESULT", fail_theme)
            UV_light_button_push()  # Turn off UV light
            test_fail = True
            return 
    # Attempt test with door closed
    door_closed = close_door()            
    time.sleep(0.1)
    if door_closed:
        write_console("Attempting UV Test")
        # Press the UV pushbutton
        UV_light_button_push()  
        time.sleep(3)
        # Measure UV load current
        UV_ON = read_UV_current()
        # Print results
        if UV_ON:
            write_console("DOOR CLOSED - UV ON")
        else: 
            write_console("ERROR: DOOR CLOSED - UV OFF")
            test_fail = True
            return 
    # Turn off UV load
    write_console("Turning off UV load...")
    UV_light_button_push() 
    time.sleep(3)
    # Verify the UV load is OFF
    UV_ON = read_UV_current()
    if not UV_ON:
        dpg.bind_item_theme("UV_RESULT", pass_theme)
    else:
        write_console("ERROR: UV lOAD did not turn off correctly")
        write_console("Stopping Test")
        test_fail = True
        UV_light_button_push()  # Turn off UV light
        return
    # Print Results
    if test_fail: 
        write_console("UV TEST FAILED")
        dpg.bind_item_theme("UV_RESULT", fail_theme)
    else: write_console("UV TEST SUCCESSFUL")
    write_console_end_section()

def HEPA_fan(sender, app_data):
    # TO DO: Add current monitoring hardware and update code
    global test_fail
    write_console("HEPA fan test start")
    HEPA_fan_button_push()
    time.sleep(3)
    HEPA_fan_button_push()
    write_console("HEPA fan test end")
    dpg.bind_item_theme("HEPA_RESULT", pass_theme)
    write_console_end_section()
    
def start_test(sender, app_data):
    global file_name
    global tast_fail

    reset_results()
    dpg.configure_item("run_test", enabled=False)
    reset_test_output()

    #Start a report csv file
    data = [['913-00072 HEPA/UV Board Level Test'], 
            ['Part Number: '],
            ['Serial Number: '],
            ['Technician: ']]

    current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    str_current_datetime = str(current_datetime)
    file_name = "TestReport_"+str_current_datetime+".csv"
    file = open(file_name, 'w+', newline ='')
    print("file name = ", file_name)
    # writing the data into the file
    with file:    
        write = csv.writer(file)
        write.writerows(data)
    
    #Run tests

    #Open door
    open_door() 

    read_24V(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return
    
    read_5V(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return
 
    read_3V3(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return

    read_5Vaux(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return

    flash(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return

    can(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return

    eeprom(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return

    UV_light(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return

    HEPA_fan(sender, app_data)
    #write_console(test_fail)
    if test_fail: 
        stop_test()
        return
    
    dpg.configure_item("reset_test", enabled=True)
    
    
    #dpg.configure_item("console_msg", tracked=False)

def stop_test():
    #reset_results()
    dpg.configure_item("reset_test", enabled=True)

def reset_test(sender, app_data):
    reset_test_output()
    reset_results()
    dpg.configure_item("run_test", enabled=True)

def reset_test_output():
     dpg.set_value("24V", 0)
     dpg.set_value("5V", 0)
     dpg.set_value("3V3", 0)
     dpg.set_value("5VAUX", 0)

def write_console(msg):
    dpg.add_text(msg, parent="CONSOLE", wrap=800, tracked=True)

def write_console_end_section():
    dpg.add_text("=====================================================", parent="CONSOLE", tracked=True)

def disable_tests():
    dpg.configure_item("24V_test", enabled=False) 
    dpg.configure_item("5V_test", enabled=False)
    dpg.configure_item("3V3_test", enabled=False)
    dpg.configure_item("5Vaux_test", enabled=False)
    dpg.configure_item("MCU_flash", enabled=False)
    dpg.configure_item("CAN_test", enabled=False)
    dpg.configure_item("EEPROM_test", enabled=False)
    dpg.configure_item("UV_test", enabled=False)
    dpg.configure_item("HEPA_test", enabled=False)

def enable_tests():
    dpg.configure_item("24V_test", enabled=True)
    dpg.configure_item("5V_test", enabled=True)
    dpg.configure_item("3V3_test", enabled=True)
    dpg.configure_item("5Vaux_test", enabled=True)
    dpg.configure_item("MCU_flash", enabled=True)
    dpg.configure_item("CAN_test", enabled=True)
    dpg.configure_item("EEPROM_test", enabled=True)
    dpg.configure_item("UV_test", enabled=True)
    dpg.configure_item("HEPA_test", enabled=True)

def reset_results():
    dpg.bind_item_theme("24V_RESULT", neutral_theme)
    dpg.bind_item_theme("5V_RESULT", neutral_theme)
    dpg.bind_item_theme("3V3_RESULT", neutral_theme)
    dpg.bind_item_theme("5Vaux_RESULT", neutral_theme)
    dpg.bind_item_theme("FLASH_RESULT", neutral_theme)
    dpg.bind_item_theme("CAN_RESULT", neutral_theme)
    dpg.bind_item_theme("EEPROM_RESULT", neutral_theme)
    dpg.bind_item_theme("UV_RESULT", neutral_theme)
    dpg.bind_item_theme("HEPA_RESULT", neutral_theme)

with dpg.window(label="Example Window", width=1000, height=700):
    with dpg.group(horizontal=True):    
        with dpg.child_window(label="Data", width=400, height=300):
            dpg.add_text("HEPA-UV TEST")          
            dpg.add_input_text(default_value="10.13.11.245", tag="ip_addr")
            dpg.add_button(label="USE DEFAULT IP ADDRESS", callback=default_ip)
            dpg.add_button(label="CONNECT TO BBB", tag="ssh_btn", callback=bbb_connect)
            dpg.add_button(label="DISCONNECT", tag="ssh_disconnect", callback=bbb_disconnect, enabled=False)
            dpg.add_button(label="START TEST", tag="run_test", callback=start_test)      
            dpg.add_button(label="RESET TEST", tag="reset_test", callback=reset_test, enabled=False)
            
        with dpg.child_window(label="Data 2", width=400, height=300):
            with dpg.table():
                dpg.add_table_column(label="Test")
                dpg.add_table_column(label="Test Output")
                dpg.add_table_column(label="Test Result")
                with dpg.table_row(tag="test_btns"):
                    dpg.add_button(label="24VDC Voltage", tag="24V_test", callback=read_24V, enabled=True)
                    dpg.add_text(0, tag="24V")
                    dpg.add_button(label="PASS/FAIL", tag="24V_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="5V Voltage", tag="5V_test", callback=read_5V, enabled=True)
                    dpg.add_text(0, tag="5V")
                    dpg.add_button(label="PASS/FAIL", tag="5V_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="3.3V Voltage", tag="3V3_test", callback=read_3V3, enabled=True)
                    dpg.add_text(0, tag="3V3")
                    dpg.add_button(label="PASS/FAIL", tag="3V3_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="5V_AUX Voltage", tag="5Vaux_test", callback=read_5Vaux, enabled=True)
                    dpg.add_text(0, tag="5VAUX")
                    dpg.add_button(label="PASS/FAIL", tag="5Vaux_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="FLASH MCU", tag="MCU_flash", callback=flash, enabled=True)
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL", tag="FLASH_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="TEST CAN BUS", tag="CAN_test", callback=can, enabled=True)
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL", tag="CAN_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="TEST EEPROM", tag="EEPROM_test", callback=eeprom, enabled=True)
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL", tag="EEPROM_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="TEST UV LIGHT", tag="UV_test", callback=UV_light, enabled=True) 
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL", tag="UV_RESULT")
                with dpg.table_row():
                    dpg.add_button(label="TEST HEPA FAN", tag="HEPA_test", callback=HEPA_fan, enabled=True)
                    dpg.add_table_cell()
                    dpg.add_button(label="PASS/FAIL", tag="HEPA_RESULT")

    with dpg.child_window(label="Console", tag="CONSOLE", width=810, height=200):
        dpg.add_text(default_value="Console") 
        
#Theme Defitions
with dpg.theme() as test_run_theme:
    with dpg.theme_component(dpg.mvAll):
        #dpg.add_theme_color(dpg.mvThemeCol_Text, [0, 153, 76])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [0, 153, 76])
        dpg.add_theme_color(dpg.mvThemeCol_Button, [0, 153, 76])
dpg.bind_theme(test_run_theme)   

with dpg.theme() as neutral_theme:
    with dpg.theme_component(dpg.mvButton, label="PASS/FAIL"):
        dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [50, 50, 50])
        dpg.add_theme_color(dpg.mvThemeCol_Button, [50, 50, 50])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [50, 50, 50])
dpg.bind_theme(neutral_theme)   

with dpg.theme() as disabled_theme:
    with dpg.theme_component(dpg.mvButton, enabled_state=False):
        dpg.add_theme_color(dpg.mvThemeCol_Text, [128, 128, 128])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [50, 50, 50])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [50, 50, 50])
dpg.bind_theme(disabled_theme)

with dpg.theme() as pass_theme:
    with dpg.theme_component(dpg.mvButton, label="PASS/FAIL"):
        #dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [50, 50, 50])
        dpg.add_theme_color(dpg.mvThemeCol_Button, [0, 153, 76])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [50, 50, 50])
#dpg.bind_theme(pass_theme)

with dpg.theme() as fail_theme:
    with dpg.theme_component(dpg.mvButton, label="PASS/FAIL"):
        #dpg.add_theme_color(dpg.mvThemeCol_Text [128, 128, 128])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [50, 50, 50])
        dpg.add_theme_color(dpg.mvThemeCol_Button, [153, 0, 0])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [50, 50, 50])
#dpg.bind_theme(fail_theme)

#dpg.show_style_editor()


dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

