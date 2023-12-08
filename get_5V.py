import Adafruit_BBIO.ADC as ADC

ADC.setup()
analogPin = "P9_36"

potVal = ADC.read(analogPin)
potVolt = (potVal*1.8)/0.18122270742 #Vdiv/(3.32kOhm/(3.32kOhm+15kOhm))
print(potVolt)