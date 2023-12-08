import csv
from datetime import datetime
from csv import unregister_dialect
from distutils.cmd import Command
import paramiko
#import paramiko_test
import subprocess
import dearpygui.dearpygui as dpg
import sys
import time
#import shared_var

#from shared_var import ADC_Value
#from shared_var import command
#from shared_var import ssh_status
#from shared_var import console_msg

ssh = paramiko.SSHClient()

global file_name
global can_status
global eeprom_status
global test_fail 
global flash_status
#global door_open
test_fail = False 

def establish_connection(ip):
    try:
        # Define SSH connection parameters
        print("ip = ", ip)
        host = ip               # BBB's IP address
        username = "debian"     # BBB username
        password = "temppwd"    # BBB password
        # Initialize an SSH client
        print("Connecting...")
        write_console("Connecting...")
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Connect to the BBB
        ssh.connect(host, username=username, password=password)
        print("Connected")
        write_console("Connected")
        #print("ssh_status = ", shared_var.ssh_status)


    except paramiko.AuthenticationException:
        print("Authentication failed")
        write_console("Authentication failed")
    except paramiko.SSHException as e:
        print(f"SSH connection failed: {str(e)}")
        write_console(f"SSH connection failed: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        write_console(f"An error occurred: {str(e)}")

def end_connection():
    write_console("Disconnecting...")
    ssh.close()  

def get_ADC_value(command):
    global ADC_Value
    print("Executing Command: ", command)
   
    # Execute the command
    stdin, stdout, stderr = ssh.exec_command(command)

    # Combine stderr with stdout
    #stdout.channel.set_combine_stderr(True)
    print("Sending the output")
    # Read the output as a single string
    ADC_Value = stdout.read(30).decode("utf-8")
    
    # Print the script's output
    print("Received: ", ADC_Value)
    #print(stdout.read(18).decode("utf-8"))
         
    # Explicitly close the SSH connection
    del stdin, stdout, stderr  
    return ADC_Value

def flash_MCU():
    msg = None 
    flashed_flag = 0
    global flash_status
    print("Board Flash Start")
    write_console("MCU Flashing Started")
    # Execute the command
    #activate_command = f'source ~/myenv/bin/activate'
    #run_script_command = f'python sample_flash.py'
    #combined_command = f'{activate_command} && {run_script_command}'
    #run_command = f'source {virtualenv_activate} && python {script_to_run}'

    #stdin, stdout, stderr = ssh.exec_command(combined_command)
    stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python simple_flash.py")
    print("Command sent to BBB")
    #print(stdout.read().decode("utf-8"))
    msg = (stdout.read().decode("utf-8"))
    print(msg)
    lines = msg.split('\n')
    for line in lines:
        write_console(line)
        if "MCU flashed successfully." in line:
            flashed_flag = 1
    if (flashed_flag == 1):
        flash_status = "Flashed"
    else: flash_status = "Flashing Failed"
    print(flash_status)
    del stdin, stdout, stderr  

def test_can():
    msg = None
    sent = None 
    received = None
    global can_status   

    can_status = None
    
    print("CAN test started")
    write_console("CAN test started")
    #stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python can_test.py")
    stdin, stdout, stderr = ssh.exec_command("python can_test.py")
    print("Command sent to BBB")
    #print(stdout.read().decode("utf-8")) #use this to send a meaningful msg
    msg = (stdout.read().decode("utf-8"))
    #print(msg)
    write_console(msg)

    lines = msg.split('\n')
    for line in lines:
        if "can1  5A1" in line:
            sent = line.split("[8]")[1].strip()
        elif "can1  00000023" in line:
            received = line.split("[8]")[1].strip()

    print("Message Sent to MCU: ", sent)
    print("Message Received from MCU (expected = sent message incremented by 1): ", received)

    msg_sent = "Message Sent to MCU: "+sent
    msg_received = "Message Received from MCU (expected = sent message incremented by 1): "+received

    write_console(msg_sent)
    write_console(msg_received)

    sent_bytes = sent.split()
    received_bytes = received.split()

    #print("sent_bytes: ", sent_bytes)
    #print("received_bytes: ", received_bytes)

    can_ok = 0

    for i, (sent_byte, received_byte) in enumerate(zip(sent_bytes, received_bytes)):
        sent_byte = sent_byte.strip("'")
        received_byte = received_byte.strip("'")
        if int(sent_byte, 16) + 1 == int(received_byte, 16):
            can_ok = can_ok+1
    
    if can_ok == 8:
        can_status = "CAN BUS OK"
    else: 
        can_status = "CAN BUS NOT OK"
    can_ok = 0
    
    del stdin, stdout, stderr

    print(can_status)
    write_console(can_status)
    write_console_end_section()
    #print("Sending the output")
    #msg = stdout.read(30).decode("utf-8")
    #print ("Message = ", msg)
    

def test_EEPROM():
    msg = None
    sent = None 
    received = None
    value = None
    global eeprom_status 

    eeprom_status = None

    print("EEPROM test started")
    write_console("EEPROM test started")
    #stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python can_test.py")
    stdin, stdout, stderr = ssh.exec_command("python EEPROM_test.py")
    print("Command sent to BBB")
    #print(stdout.read().decode("utf-8")) #use this to send a meaningful msg
    msg = (stdout.read().decode("utf-8"))
    print(msg)
    write_console(msg)

    lines = msg.split('\n')
    #print(lines)
    for line in lines[5:]:  # Consider the last two lines
        if "can1  00000023" in line:
            value = line.split("[8]")[1].strip()
            if sent is None:
                sent = value
            elif received is None:
                received = value
            
    print("Sent to EEPROM: ", sent)
    print("Received from EEPRM: ", received)

    msg_sent = "String of random bytes written to EEPROM: " + sent
    msg_received = "String of random bytes read from EEPROM: " + received

    write_console(msg_sent)
    write_console(msg_received)

    if (sent == received):
        eeprom_status = "EEPROM OK"
    else:
        eeprom_status = "EEPROM NOT OK"
    
    
    del stdin, stdout, stderr
    print(eeprom_status)
    write_console(eeprom_status)
    write_console_end_section()

def UV_light_button_push():
    # Execute the command
    stdin, stdout, stderr = ssh.exec_command("python UV_pushbutton.py")
    del stdin, stdout, stderr  

def open_door():
    write_console("Opening Door...")
    stdin, stdout, stderr = ssh.exec_command("python open_door_sw.py")
    del stdin, stdout, stderr  
    write_console("Door Open")
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
    # Execute the command
    stdin, stdout, stderr = ssh.exec_command("python HEPA_pushbutton.py")
    del stdin, stdout, stderr

dpg.create_context()
dpg.create_viewport(title='Custom Title', width=1000, height=700)
dpg.setup_dearpygui()

def read_24V(sender, app_data):
    global file_name 
    global test_fail
    command = "python get_24V.py"
    write_console("24V Rail Voltage Test Start")
    ADC_Value = get_ADC_value(command)
    ADC_float = round(float(ADC_Value),3)
    msg = "24VDC: "+str(ADC_float)
    write_console(msg)
    dpg.set_value("24V", ADC_float) 
    if 23.52 <= ADC_float <= 24.48: #+-2%
        dpg.bind_item_theme("24V_RESULT", pass_theme)
        write_console("24V Rail Test Passed")
    else: 
        test_fail = True
        dpg.bind_item_theme("24V_RESULT", fail_theme)
        write_console("24V Rail Test Failed")
    print ("Test Fail in read_24V = ", test_fail)
    write_console_end_section()


    #file = open(file_name, 'a', newline ='')
    #print("function file name = ", file_name)
    #with file:    
    #    #writer = csv.DictWriter(file, fieldnames=fieldnames)    
    #    writer = csv.writer(file)
    #    writer.writerow(["24V Test"])

def read_5V(sender, app_data):
    #global ADC_Value
    global test_fail 

    command = "python get_5V.py"
    write_console("5V Rail Voltage Test Start")
    ADC_Value = get_ADC_value(command)
    ADC_float = round(float(ADC_Value),3)
    dpg.set_value("5V", ADC_float) 
    msg = "5VDC: "+str(ADC_float)
    write_console(msg)
    if 4.90 <= ADC_float <= 5.10: #+-2%
        dpg.bind_item_theme("5V_RESULT", pass_theme)
        write_console("5V Rail Test Passed")
    else:
        test_fail = True
        dpg.bind_item_theme("5V_RESULT", fail_theme)
        write_console("5V Rail Test Failed")
    write_console_end_section()

def read_3V3(sender, app_data):
    #global ADC_Value
    global test_fail  

    command = "python get_3V3.py"
    write_console("3.3V Rail Voltage Test Start")
    print("Command: ", command)
    ADC_Value = get_ADC_value(command)
    ADC_float = round(float(ADC_Value),3)
    msg = "3.3VDC: "+str(ADC_float)
    write_console(msg)
    dpg.set_value("3V3", ADC_float) 
    if 3.263 <= ADC_float <= 3.366: #+-2%
        dpg.bind_item_theme("3V3_RESULT", pass_theme)
        write_console("3.3V Rail Test Passed")
    else:
        test_fail = True
        dpg.bind_item_theme("3V3_RESULT", fail_theme)
        write_console("3.3V Rail Test Failed")
    write_console_end_section()

def read_5Vaux(sender, app_data):
    #global ADC_Value
    global test_fail 

    command = "python get_5Vaux.py"
    write_console("5V_AUX Rail Voltage Test Start")
    print("Command: ", command)
    ADC_Value = get_ADC_value(command)
    ADC_float = round(float(ADC_Value),3)
    msg = "5VauxDC: "+str(ADC_float)
    write_console(msg)
    dpg.set_value("5VAUX", ADC_float) 
    if 4.9 <= ADC_float <= 5.1: #+-2%
        dpg.bind_item_theme("5Vaux_RESULT", pass_theme)
        write_console("5V_AUX Rail Test Passed")
    else: 
        test_fail = True
        dpg.bind_item_theme("5Vaux_RESULT", fail_theme)
        write_console("5V_AUX Rail Test Failed")
    write_console_end_section()

def read_UV_current():
    global test_fail  
    #global UV_ON
    command = "python UV_sns.py"
    write_console("Running UV Current Sense Test")
    print("Command: ", command)
    ADC_Value = get_ADC_value(command)
    ADC_float = round(float(ADC_Value),3)
    msg = "UV Current ADC Value: "+str(ADC_float)
    write_console(msg)
    #dpg.set_value("UV Current Sense ADC Value:", ADC_float) #Set test output field 
    if 1.3 <= ADC_float: #With Rsns=100mR, Current Sense Op-Amp will saturate to rail voltage. Change to 25mR Rsns in next rev.
        #dpg.bind_item_theme("UV_RESULT", pass_theme)
        UV_ON = True
    else:
        #test_fail = "Test Failed"
        #dpg.bind_item_theme("UV_RESULT", fail_theme)
        UV_ON = False
    #write_console_end_section()
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
    #shared_var.ssh_status == "Disconnected"
    dpg.configure_item("ssh_btn", enabled=True)
    write_console("Disconnected")
    write_console_end_section()    

def flash(sender, app_data):
    global flash_status
    global test_fail
    flash_MCU()
    if (flash_status == "Flashed"):
        dpg.bind_item_theme("FLASH_RESULT", pass_theme)
    else: 
        dpg.bind_item_theme("FLASH_RESULT", fail_theme)
        test_fail = True
    write_console_end_section()

def can(sender, app_data):
    global can_status
    global test_fail
    test_can()
    if (can_status == "CAN BUS OK"):
        dpg.bind_item_theme("CAN_RESULT", pass_theme)
    else: 
        test_fail = True
        dpg.bind_item_theme("CAN_RESULT", fail_theme)

def default_ip(sender, app_data):
    dpg.set_value("ip_addr", "10.13.11.245")

def eeprom(sender, app_data):
    global test_fail
    global eeprom_status
    test_EEPROM()
    print("eepropm_status gui: ", eeprom_status)
    if (eeprom_status == "EEPROM OK"):
        dpg.bind_item_theme("EEPROM_RESULT", pass_theme)
    else: 
        test_fail = True
        dpg.bind_item_theme("EEPROM_RESULT", fail_theme)

def UV_light(sender, app_data):
    global test_fail
    UV_test_status = None
    door_open = None
    door_closed = None
    #global UV_ON
    write_console("UV light test start")
    door_open = open_door()             # Open door
    if door_open:
        write_console("Attempting UV Test")
        UV_light_button_push()  # Try UV light turn-on - it should fail to turn on
        time.sleep(3)
        UV_ON = read_UV_current()
        if not UV_ON:
            write_console("UV OFF (ok)")
        else: 
            write_console("UV ON")
            write_console("Stopping Test") 
            dpg.bind_item_theme("UV_RESULT", fail_theme)
            UV_light_button_push()  # Turn off UV light
            return 
    door_closed = close_door()            # Close door
    time.sleep(0.1)
    if door_closed:
        write_console("Attempting UV Test")
        UV_light_button_push()  # Try UV light turn-on - it should turn on
        time.sleep(3)
        UV_ON = read_UV_current()
        if UV_ON:
            write_console ("UV ON (ok)")
            write_console("UV OK")
        else: 
            write_console("UV OFF")
            write_console ("UV Not Detected")    
            dpg.bind_item_theme("UV_RESULT", fail_theme)   
            return 
    UV_light_button_push()  # Turn off UV light
    time.sleep(3)
    UV_ON = read_UV_current()
    if not UV_ON:
        write_console("UV light test end")
        dpg.bind_item_theme("UV_RESULT", pass_theme)
    else:
        write_console("UV light did not turn off correctly")
        write_console("Stopping Test")
        UV_light_button_push()  # Turn off UV light
        dpg.bind_item_theme("UV_RESULT", fail_theme)
        return
    write_console_end_section()
    #dpg.configure_item("CONSOLE", tracked=False)
    #dpg.configure_item("console_msg_endline", tracked=False)



def HEPA_fan(sender, app_data):
    global test_fail
    write_console("HEPA fan test start")
    HEPA_fan_button_push()
    time.sleep(3)
    HEPA_fan_button_push()
    write_console("HEPA fan test end")
    write_console_end_section()
    
def start_test(sender, app_data):
    global file_name
    global tast_fail
    #test_fail = False

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
    open_door() #Make sure door is open

    read_24V(sender, app_data)
    write_console(test_fail)
    print ("Test Fail in start_test = ", test_fail)
    if test_fail: 
        stop_test()
        return
    
    read_5V(sender, app_data)
    write_console(test_fail)
    if test_fail: return
 
    read_3V3(sender, app_data)
    write_console(test_fail)
    if test_fail: return

    read_5Vaux(sender, app_data)
    write_console(test_fail)
    if test_fail: return

    flash(sender, app_data)
    write_console(test_fail)
    if test_fail: return

    can(sender, app_data)
    write_console(test_fail)
    if test_fail: return

    eeprom(sender, app_data)
    write_console(test_fail)
    if test_fail: return

    UV_light(sender, app_data)
    write_console(test_fail)
    if test_fail: return

    HEPA_fan(sender, app_data)
    write_console(test_fail)
    if test_fail: return
    #dpg.configure_item("console_msg", tracked=False)

def stop_test():
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

