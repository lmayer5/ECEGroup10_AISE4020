import random
import time
from Motor import *
from servo import *
from Led import Led
import RPi.GPIO as GPIO
from PCA9685 import PCA9685
from rpi_ws281x import *

THRESHOLD_DIST = 30
INIT_SPEED = 800

class Ultrasonic:
    '''Copies utility functions from the Freenove tutorial pdf and implements a custom object avoidance algo'''
    def __init__(self):
        GPIO.setwarnings(False)
        self.trigger_pin = 27
        self.echo_pin = 22
        self.MAX_DISTANCE = 300               # define the maximum measuring distance, unit: cm
        self.timeOut = self.MAX_DISTANCE*60   # calculate timeout according to the maximum measuring distance
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin,GPIO.OUT)
        GPIO.setup(self.echo_pin,GPIO.IN)
        self.PWM = Motor()
        self.pwm_S = Servo()

    def pulseIn(self,pin,level,timeOut): # obtain pulse time of a pin under timeOut
        t0 = time.time()
        while(GPIO.input(pin) != level):
            if((time.time() - t0) > timeOut*0.000001):
                return 0;
        t0 = time.time()
        while(GPIO.input(pin) == level):
            if((time.time() - t0) > timeOut*0.000001):
                return 0;
        pulseTime = (time.time() - t0)*1000000
        return pulseTime

    def get_distance(self):     # get the measurement results of ultrasonic module,with unit: cm
        distance_cm=[0,0,0,0,0]
        for i in range(5):
            GPIO.output(self.trigger_pin,GPIO.HIGH)      # make trigger_pin output 10us HIGH level
            time.sleep(0.00001)     # 10us
            GPIO.output(self.trigger_pin,GPIO.LOW) # make trigger_pin output LOW level
            pingTime = self.pulseIn(self.echo_pin,GPIO.HIGH,self.timeOut)   # read plus time of echo_pin
            distance_cm[i] = pingTime * 340.0 / 2.0 / 10000.0     # calculate distance with sound speed 340m/s
        distance_cm=sorted(distance_cm)
        return  int(distance_cm[2])

    def turnServo(self,angle):
        self.pwm_S.setServoPwm('0', angle)

    def setMotorSpeed(self, TL, TR, BL, BR):
        self.PWM.setMotorModel(TL, TR, BL, BR)

    def run(self):
        ### NOTES ###
        ## Can change servo angle with the following
        # self.pwm_S.setServoPwm('0', angle)
        ## sets each motor's speed. which arg is which? ()
        #
        ## get distance from US sensor using the followung
        # self.get_distance() -> float

        # intial state is stopped
        self.PWM = Motor()
        self.pwm_S = Servo()

        # define the directions (angles) to check distance
        left = 30
        middle = 90
        right = 150

        # define stopping threshold
        STOPPING_DIST = 30

        driving = True

        while driving:
            self.turnServo(middle)
            m_dist = self.get_distance()

            # if dist is greater than stopping dist, turn motors on
            if m_dist > STOPPING_DIST:
                self.setMotorSpeed(1500,1500,1500,1500)
            else:
                self.setMotorSpeed(0,0,0,0)
                driving = False

        while not driving:

            self.turnServo(left)
            time.sleep(0.5)
            l_dist = self.get_distance()

            self.turnServo(middle)
            time.sleep(0.5)
            m_dist = self.get_distance()

            self.turnServo(right)
            time.sleep(0.5)
            r_dist = self.get_distance

            # check if max value is greater than stopping distance
            distances = [l_dist, m_dist, r_dist]

            currentMax = l_dist
            maxIndex = 0
            for i in range(1,3):
                if distances[i] > currentMax:
                    currentMax = distances[i]
                    maxIndex = i

            if (maxIndex == 0):
                print("Left")
            elif (maxIndex == 1):
                print("Middle")
            elif (maxIndex == 2):
                print("Right")
            else:
                print("yo u fucked something up O_O")

            if currentMax > STOPPING_DIST:
                driving=True

class Line_Tracking:
    def __init__(self):
        self.IR01 = 14
        self.IR02 = 15
        self.IR03 = 23
        self.LED = Led()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR01,GPIO.IN)
        GPIO.setup(self.IR02,GPIO.IN)
        GPIO.setup(self.IR03,GPIO.IN)
        self.ultrasonic = Ultrasonic()
    def stop(self):
        PWM.setMotorModel(0,0,0,0)
    def set_led(self, color):
        if color == 'red':
            rgb = (255,0,0)
        elif color == 'green':
            rgb = (0,255,0)
        else:
            rgb = (0,0,0)
        for i in (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80):
            self.LED.ledIndex(i, *rgb)
    def parseDistance(self, rawDist):
        if rawDist >= THRESHOLD_DIST or rawDist == 0:
            return 999
        else:
            return rawDist
    def testMotor(self):
        speeds = []
        for i in range(10):
            speeds.append(100*i)

        for speed in speeds:
            print(f"Speed:\t{speed}")
            PWM.setMotorModel(speed, speed, speed, speed)
            time.sleep(3)

        print("test complete.")
        PWM.setMotorModel(0,0,0,0)

    def avoid(self):
        # go around
        PWM.setMotorModel(-2000,-2000,2000,2000)
        time.sleep(0.5)
        PWM.setMotorModel(1000,1000,1000,1000)
        time.sleep(0.5)
        PWM.setMotorModel(2000,2000,-2000,-2000)
        time.sleep(0.5)
        PWM.setMotorModel(1000,1000,1000,1000)
        time.sleep(0.5)
        PWM.setMotorModel(2000,2000,-2000,-2000)
        time.sleep(0.5)

        while (GPIO.input(self.IR01) != True) and (GPIO.input(self.IR02) != True) and (GPIO.input(self.IR03) != True):
            PWM.setMotorModel(800,800,800,800)

        time.sleep(0.5)
        PWM.setMotorModel(-2000,-2000,2000,2000)
        PWM.setMotorModel(0,0,0,0)

    def run(self):
        while True:
            self.ultrasonic.turnServo(90)

            distance = self.ultrasonic.get_distance()
            distance=self.parseDistance(distance)

            while distance <= THRESHOLD_DIST:
                self.stop()
                self.set_led('red')
                print(f'Stopped! Object in the path {distance} [cm] away')
                distance = self.ultrasonic.get_distance()
                self.avoid()



            # detect current drive code (self.LMR)
            self.LMR=0x00
            if GPIO.input(self.IR01)==True:
                self.LMR=(self.LMR | 4)
            if GPIO.input(self.IR02)==True:
                self.LMR=(self.LMR | 2)
            if GPIO.input(self.IR03)==True:
                self.LMR=(self.LMR | 1)

            # movement conditions based on drive code
            if self.LMR==2:
                self.set_led('green')
                PWM.setMotorModel(INIT_SPEED, INIT_SPEED, INIT_SPEED, INIT_SPEED)
            elif self.LMR==4:
                PWM.setMotorModel(-1500,-1500,2500,2500)
                self.set_led('green')
            elif self.LMR==6:
                PWM.setMotorModel(-2000,-2000,4000,4000)
                self.set_led('green')
            elif self.LMR==1:
                PWM.setMotorModel(2500,2500,-1500,-1500)
                self.set_led('green')
            elif self.LMR==3:
                PWM.setMotorModel(4000,4000,-2000,-2000)
                self.set_led('green')

            # check if fork in the road
            elif self.LMR==5:
                print("Fork in the road")
                self.set_led('red')
                self.stop()

                # scan L and R distances
                self.ultrasonic.turnServo(45)
                left_dist = self.ultrasonic.get_distance()
                time.sleep(2)
                self.ultrasonic.turnServo(135)
                right_dist = self.ultrasonic.get_distance()
                time.sleep(2)
                self.ultrasonic.turnServo(90)

                # parse distances (uninterrupted or interrupted with dist reading?)
                l = self.parseDistance(left_dist)
                r = self.parseDistance(right_dist)

                print(f'L:{l}\tR:{r}')

                # check the distances (999 is flag for uninterrupted path)
                if l > r:
                    ## if left path is free
                    self.LMR = (self.LMR | 4)
                if l < r:
                    ## if right path is free
                    self.LMR = (self.LMR | 1)
                else:
                    dir = random.randint(0,1)
                    if dir == 0:
                        self.LMR = (self.LMR | 4)
                    if dir == 1:
                        self.LMR = (self.LMR | 1)

            elif self.LMR==7:
                #pass
                self.set_led('red')
                self.stop()


infrared=Line_Tracking()
# Main program logic follows:
if __name__ == '__main__':
    print ('Program is starting ... ')
    try:
        infrared.run()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program  will be  executed.
        infrared.set_led('off')
        PWM.setMotorModel(0,0,0,0)
