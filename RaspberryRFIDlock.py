import serial
import smbus
import SimpleMFRC522
import RPi.GPIO as GPIO
import servoKit
import signal
import time
import Adafruit_CharLCD
import keypad
from time import sleep
from servoKit import ServoKit
from Adafruit_CharLCD import Adafruit_CharLCD

ser = serial.Serial("/dev/usbtikku", 9600)

# Oletuksena luetaan tagia
continue_reading = True

# SIGINT pys‰ytt‰‰ tagin lukemisen
def end_read(signal, frame):
    global continue_reading
    print "Ending read."
	lcd.clear()
    lcd.message("NOT READING")
    continue_reading = False
    GPIO.cleanup()
# Luodaan signaali
signal.signal(signal.SIGINT, end_read)

# Komponentit 
reader = SimpleMFRC522.MFRC522()
lcd = Adafruit_CharLCD()
kit = ServoKit(channels=16)

kit.servo[0].set_servo(180)

current_time = time.strftime("%H:%M:%S")
savedtime = current_time
lukitus = True

# Sarjaportin kautta viesti (tulee n‰kyville siin‰ virtualboxissa)
print("To permanently end the reading process, press Ctrl+C on keyboard.")

while continue_reading:
    time.sleep(1)
	lcd.clear()
    lcd.message("SCANNING CARDS...")
    (status,TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

    if status == MIFAREReader.MI_OK:
        lcd.print ("KEY DETECTED")
        (status,uid) = reader.MFRC522_Anticoll()
    # Jos RFID-tagi on tunnistettu
    if status == reader.MI_OK:
        # Printataan tagi konsoliin
        print ("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
        # Admin avain:
        key = [0x0C, 0xEE, 0xBF, 0x6D]
        # uid vastaa luettua tagia
        reader.MFRC522_SelectTag(uid)
        status = reader.MFRC522_Auth(reader.PICC_AUTHENT1A, 8, key, uid)
        # Jos saadaan tagi autentikoitua, katsotaan onko sen merkistˆ samat kuin admin-avain
        # ja tallennetaan avausaika sarjalle sek‰ k‰‰nnet‰‰n servoa jos on
        if status == reader.MI_OK:
			lcd.clear()
			lcd.message("OPEN")
            reader.MFRC522_Read(8) # Lukee 8. merkkiin asti (UID tagissa 8-merkki‰)
			print("Succesfully opened the safe!")
			time.sleep(2)
			kit.servo[0].set_servo(0)
			savedtime = timemark
            lukitus = False
            # l‰hetet‰‰n t‰‰ sinne muistitikulle
			ser.write(savedtime.encode())
			ser.close() 
			print("At: " + savedtime)
            reader.MFRC522_StopCrypto1()
        # ja sitten jos ei, ei tehd‰ mit‰‰n
        else:
			lcd.clear()
			lcd.message("UNAUTH.")
            print "Authentication error"

  while lukitus == False:
    lcd.clear()
	lcd.message("STATE: OPEN")