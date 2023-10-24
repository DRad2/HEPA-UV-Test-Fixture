import paramiko
import sys
from shared_var import ADC_Value
from shared_var import command

#from shared_var import ADC_Value  # Import the shared variable

ssh = paramiko.SSHClient()

def establish_connection():
    try:
        # Define SSH connection parameters
        host = "10.13.11.179"  # Replace with your BBB's IP address
        username = "debian"  # Replace with your BBB username
        password = "temppwd"  # Replace with your BBB password
         # Initialize an SSH client
        print("Connecting...")
       
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to BBB")
        # Connect to the BBB
        ssh.connect(host, username=username, password=password)
        print("Connected")

    except paramiko.AuthenticationException:
        print("Authentication failed")
    except paramiko.SSHException as e:
        print(f"SSH connection failed: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def end_connection():
    ssh.close()  
    print("Disconnected")

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


        