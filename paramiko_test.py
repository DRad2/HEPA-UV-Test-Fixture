import paramiko
import sys
import shared_var
from shared_var import ADC_Value
from shared_var import command
from shared_var import ssh_status
#from shared_var import ADC_Value  # Import the shared variable

ssh = paramiko.SSHClient()

def establish_connection(ip):
    try:
        # Define SSH connection parameters
        #global ip
        print("ip = ", ip)
        host = ip  # Replace with your BBB's IP address
        username = "debian"  # Replace with your BBB username
        password = "temppwd"  # Replace with your BBB password
         # Initialize an SSH client
        print("Connecting...")
       
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to BBB")
        # Connect to the BBB
        ssh.connect(host, username=username, password=password)
        print("Connected")
        
        global ssh_status
        shared_var.ssh_status = "Connected"
        print("ssh_status = ", shared_var.ssh_status)


    except paramiko.AuthenticationException:
        print("Authentication failed")
    except paramiko.SSHException as e:
        print(f"SSH connection failed: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def end_connection():
    ssh.close()  
    print("Disconnected")
    shared_var.ssh_status = "Disconnected"

def get_ADC_value(command):
    global ADC_Value
    print("Executing Command: ", command)
    # Command to execute on the BBB
    #command = "python3 ADC_send.py"  # Replace with your script path

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
    print("Board Flash Start")
    # Execute the command
    #activate_command = f'source ~/myenv/bin/activate'
    #run_script_command = f'python sample_flash.py'
    #combined_command = f'{activate_command} && {run_script_command}'
    #run_command = f'source {virtualenv_activate} && python {script_to_run}'

    #stdin, stdout, stderr = ssh.exec_command(combined_command)
    stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python simple_flash.py")
    print("Command sent to BBB")
    print(stdout.read().decode("utf-8"))
    del stdin, stdout, stderr  

def test_can():
    msg = None
    sent = None 
    received = None
    
    print("CAN test started")
    #stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python can_test.py")
    stdin, stdout, stderr = ssh.exec_command("python can_test.py")
    print("Command sent to BBB")
    #print(stdout.read().decode("utf-8")) #use this to send a meaningful msg
    msg = (stdout.read().decode("utf-8"))
    #print(msg)

    lines = msg.split('\n')
    for line in lines:
        if "can1  5A1" in line:
            sent = line.split("[8]")[1].strip()
        elif "can1  00000023" in line:
            received = line.split("[8]")[1].strip()

    print("Sent: ", sent)
    print("Received: ", received)

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
        print ("CAN BUS OK")
    else: print ("CAN BUS NOT OK")
    can_ok = 0

    #print("Sending the output")
    #msg = stdout.read(30).decode("utf-8")
    #print ("Message = ", msg)
    del stdin, stdout, stderr

def test_EEPROM():
    msg = None
    sent = None 
    received = None
    value = None
    
    print("EEPROM test started")
    #stdin, stdout, stderr = ssh.exec_command("source myenv/bin/activate && python can_test.py")
    stdin, stdout, stderr = ssh.exec_command("python EEPROM_test.py")
    print("Command sent to BBB")
    #print(stdout.read().decode("utf-8")) #use this to send a meaningful msg
    msg = (stdout.read().decode("utf-8"))
    print(msg)

    lines = msg.split('\n')
    #print(lines)
    for line in lines[5:]:  # Consider the last two lines
        if "can1  00000023" in line:
            value = line.split("[8]")[1].strip()
            if sent is None:
                sent = value
            elif received is None:
                received = value
            
    print("Sent: ", sent)
    print("Received: ", received)

    if (sent == received):
        print("EEPROM OK")

    del stdin, stdout, stderr
        


    