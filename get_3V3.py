import Adafruit_BBIO.ADC as ADC

ADC.setup()
analogPin = "P9_33"

potVal = ADC.read(analogPin)
potVolt = potVal*1.8/0.27255092143 #Vdiv/(5.62kOhm/5.62kOhm+15kOhm)
print(potVolt)