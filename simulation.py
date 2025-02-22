import random
import time
import threading
import pygame
import sys
import os

# Default values of signal timers
defaultGreen = {0:0, 1:0, 2:0, 3:0}
defaultRed = 000
defaultYellow = 5

signals = []
noOfSignals = 4
currentGreen = 0   # Indicates which signal is green currently
#nextGreen = (currentGreen+1)%noOfSignals    # Indicates which signal will turn green next
currentYellow = 0   # Indicates whether yellow signal is on or off 

signal_count=0
speeds = {'car':2.25, 'bus':1.8, 'truck':1.8, 'bike':2.5}  # average speeds of vehicles

# Coordinates of vehicles' start
x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}
directions_to_numbers = {'right': 0, 'down': 1, 'left': 2, 'up': 3} 
vehicleCount = {'right':0, 'down':0, 'left':0, 'up':0}
prevvehicleCount = {'right':0, 'down':0, 'left':0, 'up':0}
cycle_crossed = {'right':0, 'down':0, 'left':0, 'up':0}
initial_phase = True

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
stoppingGap = 25    # stopping gap
movingGap = 25   # moving gap

# set allowed vehicle types here
allowedVehicleTypes = {'car': True, 'bus': True, 'truck': True, 'bike': True}
allowedVehicleTypesList = []
vehiclesTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
vehiclesNotTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
rotationAngle = 3
mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
# set random or default green signal time here 
randomGreenSignalTimer = True
# set random green signal time range here 
randomGreenSignalTimerRange = [10,20]
cycleTime = 40
lane_count=[0,0,0,0]
# Track completed lanes and crossed vehicles
lanes_completed = 0
completed_directions = set()
cycle_count = 0

timeElapsed = 0
simulationTime = 300
timeElapsedCoods = (1100,50)
vehicleCountTexts = ["0", "0", "0", "0"]
vehicleCountCoods = [(480,210),(880,210),(880,550),(480,550)]
total_vehicles = 0

pygame.init()
simulation = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)

        if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):   
            if(direction=='right'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                - vehicles[direction][lane][self.index-1].image.get_rect().width 
                - stoppingGap         
            elif(direction=='left'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                + vehicles[direction][lane][self.index-1].image.get_rect().width 
                + stoppingGap
            elif(direction=='down'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                - vehicles[direction][lane][self.index-1].image.get_rect().height 
                - stoppingGap
            elif(direction=='up'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                + vehicles[direction][lane][self.index-1].image.get_rect().height 
                + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Set new starting and stopping coordinate
        if(direction=='right'):
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif(direction=='left'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif(direction=='down'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif(direction=='up'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        global currentGreen, currentYellow, cycle_crossed
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.image.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                cycle_crossed[self.direction] += 1 # adding to the cycle crossed vehicle count
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.x+self.image.get_rect().width<stopLines[self.direction]+40):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):               
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 2.4
                            self.y -= 2.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):
                                self.y -= self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.x+self.image.get_rect().width<mid[self.direction]['x']):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                 
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 2
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y+self.image.get_rect().height)<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):
                                self.y += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap))):                
                        self.x += self.speed
                else:
                    if((self.crossedIndex==0) or (self.x+self.image.get_rect().width<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):                 
                        self.x += self.speed
        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.image.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                cycle_crossed[self.direction] += 1 # adding to the cycle crossed vehicle count
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.y+self.image.get_rect().height<stopLines[self.direction]+50):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 1.2
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.x + self.image.get_rect().width) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):
                                self.x += self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.y+self.image.get_rect().height<mid[self.direction]['y']):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 2.5
                            self.y += 2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))): 
                                self.x -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap))):                
                        self.y += self.speed
                else:
                    if((self.crossedIndex==0) or (self.y+self.image.get_rect().height<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):                
                        self.y += self.speed
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                cycle_crossed[self.direction] += 1 # adding to the cycle crossed vehicle count
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.x>stopLines[self.direction]-70):
                        if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else: 
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 1
                            self.y += 1.2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y + self.image.get_rect().height) <(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y  -  movingGap))):
                                self.y += self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.x>mid[self.direction]['x']):
                        if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 1.8
                            self.y -= 2.5
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height +  movingGap))):
                                self.y -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x>=self.stop or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.x>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                cycle_crossed[self.direction] += 1 # adding to the cycle crossed vehicle count
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.y>stopLines[self.direction]-60):
                        if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 2
                            self.y -= 1.2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):
                                self.x -= self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.y>mid[self.direction]['y']):
                        if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 1
                            self.y -= 1
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width - movingGap))):
                                self.x += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y>=self.stop or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.y>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed 

#get the count of vehicles generated in each direction
def getVehicleCount():
    global vehicleCount, prevvehicleCount
    total = 0
    for i in range(0,4):
        vehicleCount[directionNumbers[i]] = random.randint(1, 25)
        total += vehicleCount[directionNumbers[i]]
    if initial_phase:
        print('Initial Phase is True')
        prevvehicleCount = vehicleCount.copy()
    print('Vehicle Count:', vehicleCount)
            
# Initialization of signals timings based on vehicle count
def initialize():
    global signals, currentGreen, currentYellow, nextGreen, initial_phase, cycleTime
    signals = []
    currentGreen = -1
    currentYellow = 0
    nextGreen = 0

    # Initialize all signals as red
    for i in range(noOfSignals):
        signals.append(TrafficSignal(defaultRed, defaultYellow, 0))
        signals[i].signalText = "---"
        signals[i].red = defaultRed
    
    # Wait for initial vehicles
    print("Waiting for initial vehicles to be generated...")
    while initial_phase:
        all_vehicles_ready = True
        for direction in directionNumbers.values():
            current_count = sum(len(vehicles[direction][lane]) for lane in [1, 2])
            if current_count < vehicleCount[direction]:
                all_vehicles_ready = False
                break
        
        if all_vehicles_ready:
            break
            
        printStatus()
        time.sleep(1)

    print("All initial vehicles generated, starting signals...")
    initial_phase = False
    
    # Calculate first green signal based on vehicle counts
    direction_counts = []
    for i in range(noOfSignals):
        direction = directionNumbers[i]
        count = sum(len(vehicles[direction][lane]) for lane in [1, 2])
        direction_counts.append((i, count))
    
    direction_counts.sort(key=lambda x: x[1], reverse=True)
    curr_direction = direction_counts.pop(0)
    currentGreen = curr_direction[0]
    nextGreen = direction_counts[0][0]

    print(currentGreen, nextGreen)
    print()
    
    # Set initial signal timings
    if signal_count==0 or signal_count%4==0:
        total_vehicles = sum(vehicleCount.values())
    else:
        total_vehicles = sum(prevvehicleCount.values())
    if total_vehicles > 0:
        green_time = max(
            defaultGreen[currentGreen],
            int((vehicleCount[directionNumbers[currentGreen]] / total_vehicles) * cycleTime)
        )
        signals[currentGreen].green = green_time
        signals[currentGreen].red = 0
        
        for i in range(noOfSignals):
            if i != currentGreen:
                signals[i].red = signals[currentGreen].green + defaultYellow
    
    print(f"Starting with direction {directionNumbers[currentGreen]} as green")
    repeat()
#minTime = randomGreenSignalTimerRange[0]
    #maxTime = randomGreenSignalTimerRange[1]
    #if(randomGreenSignalTimer):
        #time_ts1 = (vehicleCount['right'] // sum(vehicleCount.values()))*cycleTime
        #ts1 = TrafficSignal(0, defaultYellow, time_ts1)
        #signals.append(ts1)
        #time_ts2 = (vehicleCount['down'] // sum(vehicleCount.values()))*cycleTime
        #ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, time_ts2)
        #signals.append(ts2)
        #time_ts3 = (vehicleCount['left'] // sum(vehicleCount.values()))*cycleTime
        #ts3 = TrafficSignal(defaultRed, defaultYellow, time_ts3)
        #signals.append(ts3)
        #time_ts4 = (vehicleCount['up'] // sum(vehicleCount.values()))*cycleTime
        #ts4 = TrafficSignal(defaultRed, defaultYellow, time_ts4)
        #signals.append(ts4)
    #else:
        #ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
        #signals.append(ts1)
        #ts2 = TrafficSignal(ts1.yellow+ts1.green, defaultYellow, defaultGreen[1])
        #signals.append(ts2)
        #ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
        #signals.append(ts3)
        #ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
        #signals.append(ts4)
    #repeat()

# Print the signal timers on cmd
def printStatus():
    for i in range(0, 4):
        if(signals[i] != None):
            if(i==currentGreen):
                if(currentYellow==0):
                    print(" GREEN TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
                else:
                    print("YELLOW TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
            else:
                print("   RED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
    print()  

MIN_GREEN_TIME = 5
MAX_GREEN_TIME = 30

def repeat():
    global signals, cycle_crossed, currentGreen, currentYellow, nextGreen, signal_count, lanes_completed, prevvehicleCount, vehicleCount, total_vehicles, cycle_count, cycleTime
    
    # Calculate green time based on vehicle count and cycle time   
    if signal_count==0 or signal_count%4==0:
        prevvehicleCount = vehicleCount.copy()
        total_vehicles = sum(vehicleCount.values())
        cycle_crossed = {'right':0, 'down':0, 'left':0, 'up':0}
        signal_order = sorted(prevvehicleCount, key=prevvehicleCount.get, reverse=True)
        total_red = 0
        
        # Create a mapping from direction name to signal index
        direction_to_index = {direction: i for i, direction in directionNumbers.items()}
        
        for direction in signal_order:
            green_timer = int((prevvehicleCount[direction] / total_vehicles) * cycleTime)

            if total_red == 0:
                signals[directions_to_numbers[direction]].red = 0
                total_red = green_timer + defaultYellow
            else:
                signals[directions_to_numbers[direction]].red = total_red
                total_red += green_timer + defaultYellow
        
        for i in range(0, 4):
            print("Updated red timings : {}", signals[i].red)

        # Set currentGreen based on direction with max vehicles
        for i in range(0, 4):
            if max(prevvehicleCount.values()) == prevvehicleCount[directionNumbers[i]]:
                currentGreen = i
                break

    for i in range(noOfSignals):
        if i == currentGreen: 
            if total_vehicles > 0:
                # Get next direction's vehicle count
                direction_count = prevvehicleCount[directionNumbers[i]]
        
                # Calculate proportional time from 60-second cycle
                proportion = direction_count / total_vehicles
                green_time = int(proportion * cycleTime)
        
                # Ensure time is within bounds (5-30 seconds)
                #green_time = max(MIN_GREEN_TIME, min(green_time, MAX_GREEN_TIME))
        
                print(f"Direction {directionNumbers[i]}: {direction_count}/{total_vehicles} vehicles")
                print(f"Proportion: {proportion:.2f}, Green time: {green_time}s")
                prevvehicleCount[directionNumbers[currentGreen]] = 0
                print(prevvehicleCount)
                break
            else:
                # Default even distribution if no vehicles
                green_time = cycleTime // noOfSignals
                break
    
    # Set green signal timing
    signals[currentGreen].green = green_time
    
    # Green signal phase
    while signals[currentGreen].green > 0:
        printStatus()
        updateValues()
        time.sleep(1)
    
    # Yellow phase remains same
    currentYellow = 1
    signals[currentGreen].yellow = defaultYellow
    while signals[currentGreen].yellow > 0:
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 0
    
    # Move to next signal and update cycle
    lanes_completed += 1
    signal_count += 1
    if lanes_completed >= 2:
        lanes_completed = 0
        vehicleCount = {'right':0, 'down':0, 'left':0, 'up':0}
        getVehicleCount()
        print(f"\nNew cycle vehicle counts: {vehicleCount}")

    # Calculate next green signal based on waiting vehicles
    max_waiting = 0
    for i in range(noOfSignals):
        if i != currentGreen:
            direction = directionNumbers[i]
            waiting_count = prevvehicleCount[direction]
            if waiting_count > 0 and max(prevvehicleCount.values()) == prevvehicleCount[directionNumbers[i]]:
                nextGreen = i
                break
    
    currentGreen = nextGreen
    
    # Update all signal timings
    for i in range(noOfSignals):
        if i == currentGreen:
            signals[i].green = green_time
            signals[i].red = 0
            signals[i].yellow = 5
    
    repeat()

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 1:
                if signals[i].yellow > 0:
                    signals[i].yellow -= 1
            elif signals[i].green > 0:
                signals[i].green -= 1
        else:
            # Red signal timer should show the remaining time for entire duration
            if signals[i].red > 0:
                signals[i].red -= 1
                signals[i].signalText = str(signals[i].red)  # Show countdown for entire red duration

# Generating vehicles in the simulation based on vehicle count in that direction
def generateVehicles():
    while True:
        # Generate one vehicle at a time with proper checks
        for direction_number in range(0, 4):
            direction = directionNumbers[direction_number]
            
            # Count only non-crossed vehicles
            active_count = sum(len([v for v in vehicles[direction][lane] if not v.crossed]) 
                             for lane in [1, 2])
            
            if active_count < vehicleCount[direction]:
                # Choose lane with fewer vehicles
                lane_1_count = len(vehicles[direction][1])
                lane_2_count = len(vehicles[direction][2])
                lane_number = 1 if lane_1_count <= lane_2_count else 2
                
                # Generate vehicle
                vehicle_type = random.randint(0, 3)
                will_turn = 1 if random.randint(0, 99) < 40 and lane_number != 0 else 0
                
                try:
                    new_vehicle = Vehicle(lane_number, vehicleTypes[vehicle_type], 
                                        direction_number, direction, will_turn)
                    print(f"Generated {vehicleTypes[vehicle_type]} in {direction}, Lane {lane_number}")
                    break  # Generate one vehicle at a time
                except Exception as e:
                    print(f"Error generating vehicle: {e}")
                    
        time.sleep(0.5)  # Controlled generation rate

def showStats():
    totalVehicles = 0
    print('Direction-wise Vehicle Counts')
    for i in range(0,4):
        if(signals[i]!=None):
            print('Direction',i+1,':',vehicles[directionNumbers[i]]['crossed'])
            totalVehicles += vehicles[directionNumbers[i]]['crossed']
    print('Total vehicles passed:',totalVehicles)
    print('Total time:',timeElapsed)

def simTime():
    global timeElapsed, simulationTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simulationTime):
            showStats()
            os._exit(1) 
def render_vertical_text(screen, text, x, y, font, color):
    letter_surfaces = []
    letter_height = 0
    for letter in text:
        letter_surface = font.render(letter, True, color)
        letter_surfaces.append(letter_surface)
        if letter_height == 0:
            letter_height = letter_surface.get_height()
    
    current_y = y
    for surface in letter_surfaces:
        screen.blit(surface, (x, current_y))
        current_y += letter_height

class Main:
    global allowedVehicleTypesList
    i = 0
    for vehicleType in allowedVehicleTypes:
        if allowedVehicleTypes[vehicleType]:
            allowedVehicleTypesList.append(i)
        i += 1

    thread1 = threading.Thread(name="getVehicleCount", target=getVehicleCount, args=())  # get vehicle count
    thread1.daemon = True
    thread1.start()

    thread2 = threading.Thread(name="initialization", target=initialize, args=())  # initialization
    thread2.daemon = True
    thread2.start()

    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    print(os.getcwd())
    file_name = './images/intersection.png'
    if os.path.exists(file_name):
        background = pygame.image.load(file_name)
    # background = pygame.image.load('/images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    # Loading signal images and font
    current_dir = os.path.dirname(os.path.abspath(__file__))
    redSignal = pygame.image.load(os.path.join(current_dir, 'images', 'signals', 'red.png'))
    yellowSignal = pygame.image.load(os.path.join(current_dir, 'images', 'signals', 'yellow.png'))
    greenSignal = pygame.image.load(os.path.join(current_dir, 'images', 'signals', 'green.png'))    
    
    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(name="generateVehicles", target=generateVehicles, args=())  # Generating vehicles
    thread3.daemon = True
    thread3.start()

    thread4 = threading.Thread(name="simTime", target=simTime, args=())
    thread4.daemon = True
    thread4.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                showStats()
                sys.exit()

        screen.blit(background, (0, 0))  # display background in simulation
        for i in range(0, noOfSignals):  # display signal and set timer according to current status: green, yellow, or red
            if i == currentGreen:
                if currentYellow == 1:
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                # Show red signal countdown for entire duration
                if signals[i].red > 0:
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["", "", "", ""]

        # display signal timer
        for i in range(0, noOfSignals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], signalTimerCoods[i])

        # display vehicle count
        for i in range(0, noOfSignals):
            displayText = cycle_crossed[directionNumbers[i]]
            vehicleCountTexts[i] = font.render(str(displayText), True, black, white)
            screen.blit(vehicleCountTexts[i], vehicleCountCoods[i])

        # display time elapsed
        timeElapsedText = font.render(("Time Elapsed: " + str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText, timeElapsedCoods)

        # display the vehicles
        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
        
        for i in range(0, noOfSignals):
            # Position calculations based on signal location
            if i == 0:  # Right signal
                signal_x = signalCoods[i][0] - 20  # Left of signal
                direction_x = signalCoods[i][0] - 40  # Further left
                text_y = signalCoods[i][1] + 10
            elif i == 1:  # Down signal
                signal_x = signalCoods[i][0] + 40  # Right of signal
                direction_x = signalCoods[i][0] + 60  # Further right
                text_y = signalCoods[i][1] + 10
            elif i == 2:  # Left signal
                signal_x = signalCoods[i][0] + 40  # Right of signal
                direction_x = signalCoods[i][0] + 60  # Further right
                text_y = signalCoods[i][1] + 10
            else:  # Up signal
                signal_x = signalCoods[i][0] - 20  # Left of signal
                direction_x = signalCoods[i][0] - 40  # Further left
                text_y = signalCoods[i][1] + 10
            font = pygame.font.Font(None, 30)
            # Render vertical "Signal X" text
            render_vertical_text(screen, f"{i+1}", signal_x, text_y, font, white)
            
            # Render vertical direction text
            render_vertical_text(screen,'', direction_x, text_y, font, white)
        pygame.display.update()

Main()