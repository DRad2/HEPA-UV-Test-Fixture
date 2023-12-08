import Adafruit_BBIO.ADC as ADC

ADC.setup()
analogPin = "P9_39"

potVal = ADC.read(analogPin)
#print(potVolt)
potVolt = potVal*1.8/0.4520547945205479 #Vdiv/(8.25kOhm/8.25kOhm+10kOhm)
print(potVolt)