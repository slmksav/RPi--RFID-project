import serial
import smbus
import SimpleMFRC522
import RPi.GPIO as GPIO
import servoKit
import signal
import time
import Adafruit_CharLCD
import Adafruit_GPIO.PCF8574 as PCF
import keypad
import json
from time import sleep
from servoKit import ServoKit
from Adafruit_CharLCD import Adafruit_CharLCD
from keypad_library import Keypad, ROW, COL

# Luodaan signaali
signal.signal(signal.SIGINT, end_read)

# SIGINT pysäyttää tagin lukemisen
def end_read(signal, frame):
    global continue_reading
    print("Ending read.")
	lcd.clear()
    lcd.print("NOT READING")
    continue_reading = False
    GPIO.cleanup()

# Komponentit 
led_pin = 21
GPIO = PCF.PCF8574(address=0x20)
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT)
lcd_rs        = 4
lcd_en        = 6
d4,d5,d6,d7   = 0,1,2,3
cols,lines    = 16,2
lcd = Adafruit_CharLCD(lcd_rs, lcd_en, d4, d5, d6, d7, cols, lines, gpio=GPIO)

ser = serial.Serial("/dev/usbtikku", 9600)
reader = SimpleMFRC522.MFRC522() #SPI-väylä

kit = ServoKit(channels=16, address=0x40, busnum=1) #PWM
kit.servo[0].set_pwm(12)
kit.servo[0].set_servo(180)
keypad = Keypad(ROW, COL)

ROW = [18, 23, 24, 25]
COL = [4, 17, 22]

# Oletuksena luetaan tagia
continue_reading = True
# Muuttujat
current_time = time.strftime("%H:%M:%S")
savedtime = current_time
timeshow = False
lukitus = True
tags = {}
current_tag_id = 1

def save_tag(hex_code):
    global current_tag_id
    tags[current_tag_id] = {"id": current_tag_id, "hex_code": hex_code}
    current_tag_id += 1

def print_tag_info(id):
    if id in tags:
        print("Tag with ID {} and hex code {} saved.".format(tags[id]["id"], tags[id]["hex_code"]))
    else:
        print("Tag with ID {} not found in saved tags.".format(id))

# Terminaalin kautta viesti
print("To end the reading process, press Ctrl+C on keyboard.")

while continue_reading:
    lcd.show_cursor(False)
	lcd.clear()
    lcd.print("SCANNING CARDS...")
    (status,TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

    if status == reader.MI_OK:
        lcd.print("KEY DETECTED")
        (status,uid) = reader.MFRC522_Anticoll()
    # jos RFID-tagi on tunnistettu
    if status == reader.MI_OK:
        # Printataan tagi konsoliin
        print ("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
        # Admin avain:
        key = [0x0C, 0xEE, 0xBF, 0x6D] # 0C EE BF 6D
        # uid vastaa luettua tagia
        reader.MFRC522_SelectTag(uid)
        status = reader.MFRC522_Auth(reader.PICC_AUTHENT1A, 8, key, uid)
        # Jos saadaan tagi autentikoitua, katsotaan onko sen merkistä samat kuin admin-avain
        # ja tallennetaan avausaika talteen sekä käännetään servo auki
        if uid == key:
			lcd.clear()
			lcd.print("OPEN")
            reader.MFRC522_Read(8) # Lukee 8. merkkiin asti (UID tagissa 8-merkkiä)
			print("Succesfully opened the safe!")
			time.sleep(2)
            # avaus
			kit.servo[0].set_servo(0)
			savedtime = timemark
            lukitus = False
            # lähetetään tää sinne muistitikulle lokeja varten
			data = {"time_opened": savedtime}
            json_data = json.dumps(data)
            ser.write(json_data.encode())
            ser.close()
			print("At: " + savedtime)
            # luetun tagin talletus taulukkoon
            hex_code = ''.join(["%02X" % x for x in uid])
            save_tag(hex_code)
            print_tag_info(current_tag_id) #kun halutaan viimeiseksi käytetty tagi avauksen jälkeen, niin printataan: current_tag_id - 1
            print("-----------------\n")

            reader.MFRC522_StopCrypto1()
            
        # ja sitten jos ei, ei tehdä mitään
        else:
			lcd.clear()
			lcd.print("UNAUTH.")
            print("It did not recognize your tag")

while lukitus == False:
    open_safe()
    GPIO.output(led_pin, False)
while lukitus == True:
    GPIO.output(led_pin, True)
    
def open_safe():
        lcd.clear()
        if time_display:
            lcd.print("TIME: \n" + current_time)
        else:
            lcd.print("STATE: OPEN")
            
        # sulje tai tallenna lokit
        input = keypad.get_key()
        if input == "#":
            lcd.clear()
            lcd.print("CLOSING IN 5s...")
            time.sleep(5)
            kit.servo[0].set_servo(180)
            lukitus = True
            lcd.clear()
            lcd.print("STATE: LOCKED")
        if input == "1":
            time_display = not time_display
        if input == "3388":
            save_tags_to_usb()

def save_logs_to_usb():
    # Lokien tallennus
    logs = {}
    for tag in tags.values():
        logs[tag["id"]] = {"id": tag["id"], "hex_code": tag["hex_code"]}
        json_data = json.dumps(data)
        ser.write(json_data.encode())
    ser.close()
    print("Tags saved to USB device!!")
G