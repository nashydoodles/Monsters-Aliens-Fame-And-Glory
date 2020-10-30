description = 2
part = "grassy_field"
done = 0
yesornoaction = 0
placesdiscovered = set([])
placesdiscovered.add(part)
printplacesdiscovered = ["Grassy Field"]
inventory = {"cabin_key":1, "cabin_upstairs_bedroom_key":0, "water_bucket":1, "bucket":0}
lockeddoors = {"cabin_front_door":1}
changableobjects = {"lit_cabin_fireplace":1}
paratype = 2
cabindict = set(["cabin", "log cabin", "creepy log cabin"])
bathroomdict = set(["bathroom", "bath room", "washroom", "wash room"])
bedroomdict = set(["bedroom", "bed room"])
cabinlivingroomdict = set(["cabin living room", "living room", "cabin main room", "main room", "cabin lobby", "lobby"])

def save():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global inventory
    global lockeddoors
    global changableobjects
    if ("save" in action):
        action = action.strip()
        if action == "save":
            savepart = part
            saveplacesdiscovered = " "
            for item in placesdiscovered:
                saveplacesdiscovered = saveplacesdiscovered + item + " "
            saveinventory = " "
            for key in inventory:
                saveinventory = saveinventory + str(key) + ":" + str(inventory[key]) + " "
            savelockeddoors = " "
            for key in lockeddoors:
                savelockeddoors = savelockeddoors + str(key) + ":" + str(lockeddoors[key]) + " "
            savechangableobjects = " "
            for key in changableobjects:
                savechangableobjects = savechangableobjects + str(key) + ":" + str(changableobjects[key]) + " "
            savefile = {savepart:1, saveplacesdiscovered:2, saveinventory:3, savelockeddoors:4, savechangableobjects:5}
            print("Type: load " + str(savefile))
            print("In order to load your game.")
            print("You saved the game.")
            done = 1
            
def load():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global inventory
    global lockeddoors
    global changableobjects
    if ("load" in action):
        action = action.strip()
        action = action[5:]
        if (action[:1] == "{") and (action[-1:] == "}"):
            #Loads places discovered
            index = action.find("': 1")
            part = action[2:index]
            index2 = action.find("': 2")
            action2 = action[index + 8:index2]
            for index, word in enumerate(action2.split()):
                placesdiscovered.add(word)
            print(placesdiscovered)
            
            #Loads inventory
            index = action.find("': 3")
            action2 = action[index2 + 8:index]
            inventory = {}
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                inventory[word[:index3]] = int(word[index3 + 1:])
            print(inventory)
            
            #Loads locked/unlocked doors
            index = action.find("': 3")
            index2 = action.find("': 4")
            action2 = action[index + 8:index2]
            lockeddoors = {}    
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                lockeddoors[word[:index3]] = int(word[index3 + 1:])
            print(lockeddoors)
            index = action.find("': 4")
            index2 = action.find("': 5")
            action2 = action[index + 8:index2]
            changableobjects = {}    
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                changableobjects[word[:index3]] = int(word[index3 + 1:])
            print(changableobjects)
            print(">You loaded the game from your savefile.")
            description = 1
            done = 1

#Function to check if the action is an examine command and then determines
#what to examine and then prints the description of the examined object or
#thing
def examine():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    
    #Determines if the action is a examine command
    if ("examine" in action) or (action == "x") or ("describe" in action):
        action = action.strip()
        if action.find("examine") == 0 or action.find("inspect") == 0:
            action = action[7:]
        elif action.find("x") == 0:
            action = action[1:]
        elif action.find("describe") == 0:
            action = action[8:]
        elif action.find("check") == 0:
            action = action[5:]
        action = action.strip()
        if action[1:] == "":
            print("What do you want to examine?")
            action = input("> ").lower()
        action = action.strip()
        if part == "grassy_field":
            if action == "grass" or action == "field" or action == "brush":
                print(" There seems to be purple particles emanating from the grass.")
            elif action == "cave" or action == "mineshaft":
                print(" You would have to get closer to see it.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cavepart1":
            if action == "light" or action == "feint light" or action == "glow" or action == "feint glow" or action == "glowing light":
                if paratype == 1:
                    print(" The feint white light continues to grow brighter as you continue down the\ntunnel.")
                elif paratype == 2:
                    print(" The feint white light continues to grow brighter as you continue down the tunnel.")
            elif action == "sulfur" or action == "smell of sulfur" or action == "smell sulfur" or action == "sulfur smell":
                print(" There is a smell of sulfur in the air coming from down the tunnel.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cavepart2":
            if action == "torch" or action == "flame" or action == "fire" or action == "light":
                if paratype == 1:
                    print(" The wood burning torch seems to be perfectly block shaped and the flame\nis red with tiny white sparks flying off and little particles of smoke.")
                if paratype == 2:
                    print(" The wood burning torch seems to be perfectly block shaped and the flame is red with tiny white sparks flying off and little particles of smoke.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cabin_living_room":
            if action == "fireplace":
                print('It seems odd that fireplace was lit before you got here.')
            elif action == "table" or action == "dining table":
                print("You notice a key on the table.")
            else:
                print(" We don't know what you are trying to examine.")
        else:
            print("There is nothing to examine here.")
        done = 1

#Function to check if the action is a movement command, and then if
#true, makes you move in the specified direction
def move():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    #Determines if the action is a movement command
    if ("n" in action) or ("e" in action) or ("s" in action) or ("w" in action) or ("u" in action) or ("d" in action) or ("l" in action) or ("r" in action):
        #Determines if the direction is north
        if action == "n" or action == "north":
            if part == "grassy_field":
                part = "forestpart1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is east
        elif action == "e" or action == "east":
            if part == "mineshaft_entrance":
                part = "grassy_field"
                description = 1
            elif part == "cavepart1":
                part = "mineshaft_entrance"
                description = 1
            elif part == "cavepart2":
                part = "cavepart1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is south
        elif action == "s" or action == "south":
            if part == "forestpart1":
                part = "grassy_field"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is west 
        elif action == "w" or action == "west":
            if part == "grassy_field":
                part = "mineshaft_entrance"
                description = 1
            elif part == "mineshaft_entrance":
                part = "cavepart1"
                yesornoaction = 0
                description = 1
            elif part == "cavepart1":
                part = "cavepart2"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is northeast
        northeastdict = set(["ne", "n e", "n-e", "northeast", "north east", "north-east"])
        if action in northeastdict:
            print('You cant go that way!')
            done = 1
        #Determines if the direction is southeast
        southeastdict = set(["se", "s e", "s-e", "southeast", "south east", "south-east"])
        if action in southeastdict:
            if part == "grassy_field":
                part = "cabin_front"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is southwest
        southwestdict = set(["sw", "s w", "s-w", "southwest", "south west", "south-west"])
        if action in southwestdict:
            print('You cant go that way!')
            done = 1
        #Determines if the direction is northwest
        northwestdict = set(["nw", "n w", "n-w", "northwest", "north west", "north-west"])
        if action in northwestdict:
            if part == "cabin_front":
                part = "grassy_field"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is left
        elif action == "l" or action == "left" or action == "go left":
            if part == "cavepart2":
                part = "cavepart2_l1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is right
        elif action == "r" or action == "right" or action == "go right":
            if part == "cavepart2":
                part = "cavepart2_r1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        
                                    
def enter():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if ("go in" in action) or ("enter" in action):
        #Determines if the action is to go inside
        if "go inside" in action or "go in" in action or "enter" in action or "enter building" in action:
            if part == "cabin_front" and (action == "go inside" or action == "go in" or action == "enter" or action == "enter building"):
                if inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                    print("You will have to unlock the door first.")
                elif inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                    print("It seems to be locked. You will require a key to unlock the door.")
                elif lockeddoors["cabin_front_door"] == 0:
                    part = "cabin_living_room"
                    description = 1
                done = 1
            elif action[:9] == "go inside":
                action = action[10:]
            elif action[:5] == "go in" or action[:5] == "enter":
                action = action[6:]
            if action != "" and action != "go inside" and action != "go in" and action != "enter" and action != "enter building" and action not in cabindict and action not in bathroomdict and action not in bedroomdict:
                print('We dont know what your trying to enter.')
            elif part == "cabin_front" and action in cabindict and done == 0:
                if inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                    print("You will have to unlock the door first.")
                elif inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                    print("It seems to be locked. You will require a key to unlock the door.")
                elif lockeddoors["cabin_front_door"] == 0:
                    part = "cabin_living_room"
                    description = 1
            elif part == "cabin_living_room" and action in bathroomdict and done == 0:
                part = "cabin_1st_floor_bathroom"
                description = 1
            elif part == "cabin_living_room" and action in bedroomdict and done == 0:
                part = "cabin_1st_floor_bedroom"
                description = 1
            elif (part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom") and action in cabinlivingroomdict and done == 0:
                part = "cabin_living_room"
                description = 1
            elif action == "":
                print("What do you want to enter?")
                action = input(">").lower()
                if part == "cabin_front":
                    if action in cabindict:
                        if inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                            print("You will have to unlock the door first.")
                        elif inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                            print("It seems to be locked. You will require a key to unlock the door.")
                        elif lockeddoors["cabin_front_door"] == 0:
                            part = "cabin_living_room"
                            description = 1
                    else:
                        print('We dont know what your trying to enter.')
                elif part == "cabin_living_room":
                    if action in bathroomdict:
                        part = "cabin_1st_floor_bathroom"
                        description = 1
                    elif action in bedroomdict:
                        part = "cabin_1st_floor_bedroom"
                        description = 1
                    else:
                        print('We dont know what your trying to enter.')
                elif part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom":
                    if action in cabinlivingroomdict:
                        part = "cabin_living_room"
                        description = 1
                    else:
                        print('We dont know what your trying to enter.')
                
                else:
                    print('We dont know what your trying to enter.')
            done = 1
            
def leave():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if ("exit" in action) or ("leave" in action):
        #Determines if the action is to exit room
        if "exit" in action or "leave" in action:
            if part == "cabin_living_room" and (action == "exit" or action == "leave"):
                part = "cabin_front"
                description = 1
            elif (part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom") and (action == "exit" or action == "leave"):
                part = "cabin_living_room"
                description = 1
            elif action[:4] == "exit":
                action = action[5:]
            elif action[:5] == "leave":
                action = action[6:]
            if action != "" and action != "exit" and action != "leave" and action not in bathroomdict and action not in bedroomdict:
                print('We dont know what your trying to exit.')
            elif part == "cabin_living_room":
                if action == "cabin" or action == "main room" or action == "living room":
                    part = "cabin_front"
                    description = 1
            elif part == "cabin_1st_floor_bathroom":
                if action in bathroomdict:
                    part = "cabin_living_room"
                    description = 1
            elif action == "":
                print("What do you want to exit?")
                action = input(">").lower()
                if part == "cabin_living_room":
                    if action == "cabin" or action == "main room" or action == "living room":
                        part = "cabin_front"
                        description = 1
                    else:
                        print('We dont know what your trying to exit.')
                elif part == "cabin_1st_floor_bathroom":
                    if action in bathroomdict:
                        part = "cabin_living_room"
                        description = 1
                    else:
                        print('We dont know what your trying to exit.')
                else:
                    print('We dont know what your trying to exit.')
                
            '''else:
                print('You cant go that way!')
                '''
            done = 1

def goupstairs():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action == "go upstairs" or action == "go downstairs":
        #Determines if the action is to go inside
        if action == "go upstairs":
            if part == "cabin_living_room":
                part = "cabin_2nd_floor_bedroom_connector"
                description = 1
                done = 1
        elif action == "go downstairs":
            if part == "cabin_2nd_floor_bedroom_connector":
                part = "cabin_living_room"
                description = 1
                done = 1

#Function to check if the action is a unlock command, and then if
#true, unlocks the specified object/door
def dosomethingwithsomething():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action == "unlock" or action == "unlock door" or action == "use key" or action == "use key on door" or action == "use key on cabin door":
        if action[6:] == "" or action == "use key":
            print("What would you like to unlock?")
            action = input(">").lower()
        elif action[7:] == "door" or action[7:] == "cabin door":
            action = action[7:]
        elif action[11:] == "door" or action[11:] == "cabin door":
            action = action[11:]
        if part == "cabin_front":
            if action == "door" or action == "cabin door":
                if inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                    print("You will require a key to unlock the door.")
                elif inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                    print("You use the cabin key to unlock the front door.")
                    lockeddoors["cabin_front_door"] = 0
                    inventory["cabin_key"] = 0
                elif lockeddoors["cabin_front_door"] == 0:
                    print("The door is already unlocked.")
        else:
            print("We don't know what your trying to unlock.")
        done = 1
    elif action[:12] == "put out fire" or action[:18] == "use bucket on fire":
        if action[:17] == "put out fireplace":
            action = action[18:]
        elif action[:12] == "put out fire":
            action = action[13:]
        if action == "":
            print("What would you like to put the fire out with?")
            action = input(">").lower()
        elif action[:4] == "with":
            action = action[5:]
        if action[:18] == "use bucket on fire":
            action = action[4:10]
        if part == "cabin_living_room":
            if action == "water bucket" or "bucket":
                if inventory["bucket"] == 1 and inventory["water_bucket"] == 0:
                    print("You will have to fill the bucket with water first.")
                elif inventory["water_bucket"] == 1 and inventory["bucket"] == 0:
                    print("You put out the fire with the water bucket.")
                    inventory["water_bucket"] = 0
                    inventory["bucket"] = 1
                    changableobjects["lit_cabin_fireplace"] = 0
                elif inventory["water_bucket"] == 0 and inventory["bucket"] == 0:
                    print("You don't have a water bucket to put the fire out with.")
            else:
                print("We don't know what your trying to put out the fire with.")
        else:
            print("We don't know what fire your trying to put out.")
        done = 1
#Function to determine if a yes or no question has been asked and then
#determines if the answer was yes or no, and then acts accordingly
def yesorno():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    yesnodict = set(["yes", "no", "y", "n"])
    yesdict = set(["yes", "y"])
    nodict = set(["no", "n"])
    #Determines if a yes or no question has been asked and if a valid yes or
    #no answer has been given
    if (action in yesnodict) and (yesornoaction == 1):
        #Determines if the answer was yes and then determines the part, and
        #then acts accordingly
        if action in yesdict:
            if part == "mineshaft_entrance":
                part = "cavepart1"
                description = 1
                done = 1
        #Determines if the answer was n and then asks if the player meant no or
        #north
        elif action == "n":
            print('Did you mean no or north?')
            action = input(">").lower()
        #Determines if the answer was no and then determines the part, and then
        #acts accordingly
        if action == "no":
            if part == "mineshaft_entrance":
                print('You decide to wait a little bit before entering the cave.')
                part = "grassy_field"
                description = 1
            done = 1
        yesornoaction = 0

#Function to determine if it needs to ask a yes or no question and then if so,
#it asks the question depending on the part and then sets the yesornoaction
#variable to 1
def askyesorno():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    #When needed it asks a yes or no question, determined by the part, and
    #then sets the yesornoaction variable to 1
    if part == "mineshaft_entrance":
        print('Do you go in?')
        yesornoaction = 1
        
"""  
#Function to determine if the action is to check an object
def checkobject():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action[:5] == "check" or action[:7] == "inspect":
        if (action[:5] == "check" and action[5:] == "") or (action [:7] == "inspect" and action[7:] == ""):
            print("What would you like to " + action + "?")
            action = input(">").lower()
        else:
            if action [:5] == "check":
                action = action[6:]
            elif action[:7] == "inspect":
                action = action[8:]
        if part == "cabin_living_room":
            if action == "table" or action == "dining table":
                print("You notice a key on the table.")
        else:
            print("We don't know what your trying to check.")
        done = 1
"""

#Function to determine if the action is to take an object
def takeobject():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action[:4] == "take":
        action = action[5:]
        if action == "":
            print("What do you want to take?")
            action = input("> ").lower()
        if action == "key" or action == "key on table":
            if part == "cabin_living_room":
                inventory["cabin_upstairs_bedroom_key"] = 1
                print("You pick up the key.")
        done = 1

def listcommands():
    if action == "list commands":
        print("Commands:")
        print(" - save")
        print(" - load")
        print(" - list places")
        print(" - examine")
        print(" - take")
        print(" - unlock")
    
#Function to print a description of your surroundings when you enter a new location
def printdescription():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    #Provides a description of your surroundings when you move into a new place
    if description > 0:
        if part == "grassy_field":
            print('GRASSY FIELD')
        elif part == "mineshaft_entrance":
            print('MINESHAFT ENTRANCE')
        elif part == "cavepart1" or part == "cavepart2":
            print('CAVE')
        elif part == "forestpart1" or part == "forestpart2":
            print('FOREST')
        elif part == "cabin_front" or part == "cabin_living_room" or part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom" or part == "cabin_2nd_floor_bedroom_connector":
            print('CABIN')
        '''
        elif part == "cabin_living_room":
            print('CABIN')
            print('-LIVING ROOM')
        '''
        if paratype == 1:
            if description == 2:
                if part == "grassy_field":
                    print('  You awaken in a grassy field surrounded by mountains.\nYou have no idea who you are or how you got here.\n')
                    description = 1
                    
            if description == 1:
                if part == "grassy_field":
                    print('  There looks to be a mineshaft far off into the\ndistance, tunneling into one of the mountains, to the\nwest. There is also a creepy old looking log cabin to\nthe south east and a forest to the north.')
                    
                elif part == "forestpart1":
                    print('  You walk into a forest.')
                    
                elif part == "cabin_front":
                    print('  You stand at the front entrance of the creepy log cabin.')
                    
                elif part == "cabin_living_room":
                    print('  In the living room there is a table in the middle and a lit fireplace.')
                
                elif part == "cabin_1st_floor_bathroom":
                    print('  You enter the bathroom.')
                    
                elif part == "mineshaft_entrance":
                    print('  You stand at the entrance to the mineshaft. All you can see is')
                    print('darkness, and you smell the strong stench of sulfur emanating from')
                    print('the cave.')
                    
                elif part == "cavepart1":
                    print('  You are now in the pitch black cave. You are surrounded by darkness,')
                    print('but there is a faint light coming from down the tunnel. The smell of')
                    print('sulfur has gotten stronger although their is now a new stench, it')
                    print('smells of decaying meat. If you decide to go further into the tunnel')
                    print('like cave, go west.')
                    
                elif part == "cavepart2":
                    print('  As you continue further into the cave the potent smells continue to')
                    print('get stronger and stronger, however the light at the end of the tunnel')
                    print('proceeds to grow brighter. Eventually you come to a branching split in')
                    print('the cave where there are two tunnels, one to the left and one to the')
                    print('right. As you decide which way to go you notice something you havent')
                    print('noticed before. Being so caught up in thinking about where the tunnel')
                    print('leads, you look around and notice that everything as become very block')
                    print('like, almost as if your mind has lost the ability to perceive slopes,')
                    print('spheres or angles. You also notice where the light has been coming from')
                    print('this whole time as there is an also block like torch pinned to the wall')
                    print('between the two branching paths.')
                    
                elif part == "cavepart2_l1":
                    print('  You decide to travel down the left tunnel which eventually starts too')
                    print('open up into a large room filled with mine carts and bright block like')
                    print('torches. You also notice people but they aren\'t normal people, NO! They')
                    print('are all blocky, their arms, their legs, even their heads!')
                    
        elif paratype == 2:
            if description == 2:
                if part == "grassy_field":
                    print('  You awaken in a grassy field surrounded by mountains. You have no idea who you are or how you got here.\n')
                    description = 1
            if description == 1:
                if part == "grassy_field":
                    print('  There looks to be a mineshaft far off into the distance, tunneling into one of the mountains, to the west. There is also a creepy old looking log cabin to the south east and a forest to the north.')
                
                elif part == "forestpart1":
                    print('  You walk into a forest.')
                
                elif part == "cabin_front":
                    print('  You stand at the front entrance of the creepy log cabin.')
                
                elif part == "cabin_living_room":
                    print('  In the living room there is a table in the middle and a lit fireplace.')
                
                elif part == "cabin_1st_floor_bathroom":
                    print('  You enter the bathroom.')
                    
                elif part == "cabin_2nd_floor_bedroom_connector":
                    print('  You go upstairs.')
                    
                elif part == "mineshaft_entrance":
                    print('  You stand at the entrance to the mineshaft. All you can see is darkness, and you smell the strong stench of sulfur emanating from the cave.')
                
                elif part == "cavepart1":
                    print('  You are now in the pitch black cave. You are surrounded by darkness, but there is a faint light coming from down the tunnel. The smell of sulfur has gotten stronger although their is now a new stench, it smells of decaying meat. If you decide to go further into the tunnel like cave, go west.')
                
                elif part == "cavepart2":
                    print('  As you continue further into the cave the potent smells continue to get stronger and stronger, however the light at the end of the tunnel proceeds to grow brighter. Eventually you come to a branching split in the cave where there are two tunnels, one to the left and one to the right. As you decide which way to go you notice something you havent noticed before. Being so caught up in thinking about where the tunnel leads, you look around and notice that everything as become very block like, almost as if your mind has lost the ability to perceive slopes, spheres or angles. You also notice where the light has been coming from this whole time as there is an also block like torch pinned to the wall between the two branching paths.')
                
                elif part == "cavepart2_l1":
                    print('  You decide to travel down the left tunnel which eventually starts too open up into a large room filled with mine carts and bright block like torches. You also notice people but they aren\'t normal people, NO! They are all blocky, their arms, their legs, even their heads!')
                    
        description = 0
        done = 1

#Function to print a list of the places your character has discovered
def listplaces():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global placesdiscovered 
    global printplacesdiscovered
    printplacesdiscovered = []
    if action == "list places":
        if "grassy_field" in placesdiscovered:
            printplacesdiscovered.append("Grassy Field")
        if "forestpart1" in placesdiscovered:
            printplacesdiscovered.append("Forest")
        if "mineshaft_entrance" in placesdiscovered:
            printplacesdiscovered.append("Mineshaft Entrance")
        if "cavepart1" in placesdiscovered or "cavepart2" in placesdiscovered or "cavepart2_l1" in placesdiscovered or "cavepart2_r1" in placesdiscovered:
            printplacesdiscovered.append("Cave")
        if "cabin_front" in placesdiscovered:
            printplacesdiscovered.append("Cabin")
        print("Places Discovered: ")
        for item in printplacesdiscovered:
            print(" - " + item)
        done = 1

def listinventory():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action == "list inventory" or action == "show inventory" or action == "open inventory":
        print("Inventory: ")
        if inventory["cabin_key"] == 1:
            print(" - Cabin Key")
        if inventory["cabin_upstairs_bedroom_key"] == 1:
            print(" - Upstairs Cabin Bedroom Key")
        if inventory["water_bucket"] == 1:
            print(" - Bucket Filled With Water")
        if inventory["bucket"] == 1:
            print(" - Bucket")
        done = 1
    
while True:
    done = 0
    #Calls the description printing function
    printdescription()
    if done == 0:
        #Calls the askyesorno function
        askyesorno()
    if done == 0:
        #Lets you type in a action and puts the action into a variable
        action = input(">").lower()
    if done == 0:
        #Calls the list places function
        listplaces()
    if done == 0:
        #Calls the save function
        save()
    if done == 0:
        #Calls the load function
        load()
    if done == 0:
        #Calls the yesorno function
        yesorno()
    if done == 0:
        #Calls the examine function
        examine()
    if done == 0:
        #Calls the move function
        move()
    if done == 0:
        enter()
    if done == 0:
        leave()
    if done == 0:
        goupstairs()
    if done == 0:
        #Calls the do something with something function
        dosomethingwithsomething()
    if done == 0:
        #Calls the take object function
        takeobject()
    if done == 0:
        #Calls the list inventory function
        listinventory()
    if done == 0:
        listcommands()
    if done == 0:
        print('Thats not a valid action!')
    placesdiscovered.add(part)

