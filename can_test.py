import subprocess
import time

# Define the command to start candump
candump_command = "candump can1"

# Start the candump process in the background
candump_process = subprocess.Popen(candump_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Define the command to send the message
cansend_command = "cansend can1 5A1#00.00.00.00.00.00.00.01"

try:
    # Execute the command to send the message
    result = subprocess.run(cansend_command, shell=True, capture_output=True, text=True, check=True)

    # Check the command's output for success or failure
    print('exit status:', result.returncode)
    print('stdout:', result.stdout)
    print('stderr:', result.stderr)

    # Read and print candump values for a few seconds
    for _ in range(2):  # Adjust the number of seconds as needed
        line = candump_process.stdout.readline().strip()
        if line:
            print("Candump:", line)

    # Terminate the candump process
    candump_process.terminate()
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
