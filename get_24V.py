import Adafruit_BBIO.ADC as ADC

ADC.setup()
analogPin = "P9_35"

potVal = ADC.read(analogPin)
#print(potVolt)
potVolt = (potVal*1.8)/0.03772378516 #Vdiv/(1.18kOhm/(1.18kOhm+30.1kOhm))
print(potVolt)