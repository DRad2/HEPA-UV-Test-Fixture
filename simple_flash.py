import subprocess

# Define the command to flash the MCU
command = "pyocd flash -e auto -t stm32g491retx --base-address 0x8000000 HEPA_UV.hex -v"

try:
    # Execute the command
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)

    # Check the command's output for success or failure
    print( 'exit status:', result.returncode )
    print( 'stdout:', result.stdout )
    print( 'stderr:', result.stderr )

    if result.returncode == 0:
        print("MCU flashed successfully.")

    else print("MCU flashing failed.")

    #if "Flashing complete" in result.stdout:
    #    print("MCU flashed successfully.")
    #else:
    #    print("Failed to flash the MCU.")
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")