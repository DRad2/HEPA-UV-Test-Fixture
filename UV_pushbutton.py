import Adafruit_BBIO.GPIO as GPIO
import time

GPIO.setup("P8_8", GPIO.OUT)
GPIO.output("P8_8", GPIO.HIGH)
time.sleep(0.2)
GPIO.output("P8_8", GPIO.LOW)
GPIO.cleanup()