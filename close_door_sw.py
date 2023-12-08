import Adafruit_BBIO.GPIO as GPIO
import time

GPIO.setup("P8_12", GPIO.OUT)
GPIO.output("P8_12", GPIO.HIGH)
time.sleep(0.1)
GPIO.output("P8_12", GPIO.LOW)
GPIO.cleanup()