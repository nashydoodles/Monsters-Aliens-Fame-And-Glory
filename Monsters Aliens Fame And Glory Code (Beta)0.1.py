description = 2
part = "grassy-field"
done = 0
yesornoaction = 0
placesdiscovered = set([])
placesdiscovered.add(part)
printplacesdiscovered = ["Grassy Field"]
paratype = 2

def save():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if ("save" in action):
        action = action.strip()
        if action == "save":
            savepart = part
            saveplacesdiscovered = " "
            for item in placesdiscovered:
                saveplacesdiscovered = saveplacesdiscovered + item + " "
            savefile = {savepart:1, saveplacesdiscovered:2}
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
    if ("load" in action):
        action = action.strip()
        action = action[5:]
        if (action[:1] == "{") and (action[-1:] == "}"):
            index = action.find("': 1")
            part = action[2:index]
            index2 = action.find("': 2")
            action = action[index + 8:index2]
            for index, word in enumerate(action.split()):
                placesdiscovered.add(word)
            print(placesdiscovered)
            #placesdiscovered = action[0:index]
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
    if ("examine" in action) or ("x" in action) or ("describe" in action):
        action = action.strip()
        if action.find("examine") == 0:
            action = action[7:]
        elif action.find("x") == 0:
            action = action[1:]
        elif action.find("describe") == 0:
            action = action[8:]
        action = action.strip()
        if action[1:] == "":
            action = input(">What do you want to examine? ").lower()
        action = action.strip()
        if part == "grassy-field":
            if action == "grass" or action == "field" or action == "brush":
                print(" There seems to be purple particles emanating from the grass.")
            elif action == " cave" or action == " mineshaft":
                print(" You would have to get closer to see it.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cavepart1":
            if action == " light" or action == " feint light" or action == " glow" or action == " feint glow" or action == " glowing light":
                print(" The feint white light continues to grow brighter as you continue down the")
                print("tunnel.")
            elif action == " sulfur" or action == " smell of sulfur" or action == " smell sulfur" or action == " sulfur smell":
                print(" There is a smell of sulfur in the air coming from down the tunnel.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cavepart2":
            if action == " torch" or action == " flame" or action == " fire" or action == " light":
                print(" The wood burning torch seems to be perfectly block shaped and the flame")
                print("is red with tiny white sparks flying off and little particles of smoke.")
            elif True:
                print()
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
            if part == "grassy-field":
                part = "forestpart1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is east
        elif action == "e" or action == "east":
            if part == "mineshaft-entrance":
                part = "grassy-field"
                description = 1
            elif part == "cavepart1":
                part = "mineshaft-entrance"
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
                part = "grassy-field"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is west 
        elif action == "w" or action == "west":
            if part == "grassy-field":
                part = "mineshaft-entrance"
                description = 1
            elif part == "mineshaft-entrance":
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
            if part == "grassy-field":
                part = "cabin-front"
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
            if part == "cabin-front":
                part = "grassy-field"
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
        #Determines if the action is to go inside
        elif action == "go inside" or action == "go in" or action == "enter" or action == "enter building":
        	if part == "cabin-front":
        		part = "cabin-living-room"
        		description = 1
        	else:
        		print('You cant go that way!')
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
            if part == "mineshaft-entrance":
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
            if part == "mineshaft-entrance":
                print('You decide to wait a little bit before entering the cave.')
                part = "grassy-field"
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
    if part == "mineshaft-entrance":
        print('Do you go in?')
        yesornoaction = 1
        
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
        if part == "grassy-field":
            print('GRASSY FIELD')
        elif part == "mineshaft-entrance":
            print('MINESHAFT ENTRANCE')
        elif part == "cavepart1" or part == "cavepart2":
            print('CAVE')
        elif part == "forestpart1" or part == "forestpart2":
            print('FOREST')
        elif part == "cabin-front" or part == "cabin-living-room":
            print('CABIN')
        if paratype == 1:
	        if description == 2:
	            if part == "grassy-field":
	                print('  You awaken in a grassy field surrounded by mountains.')
	                print(' You have no idea who you are or how you got here.')
	                description = 1
	        if description == 1:
	            if part == "grassy-field":
	                print('  There looks to be a mineshaft far off into the distance,')
	                print(' tunneling into one of the mountains, to the west. There')
	                print(' is also a creepy old looking log cabin to the south east')
	                print(' and a forest to the north.')
	            elif part == "forestpart1":
	                print('  You walk into a forest.')
	            elif part == "cabin-front":
	                print('  You stand at the front entrance of the creepy log cabin.')
	            elif part == "cabin-living-room":
	            	print('  In the cabin main room.')
	            elif part == "mineshaft-entrance":
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
		    	if part == "grassy-field":
		            print('  You awaken in a grassy field surrounded by mountains. You have no idea who you are or how you got here.')
		            description = 1
		   	if description == 1:
		   		if part == "grassy-field":
		   			print('  There looks to be a mineshaft far off into the distance, tunneling into one of the mountains, to the west. There is also a creepy old looking log cabin to the south east and a forest to the north.')
		   		elif part == "forestpart1":
		   			print('  You walk into a forest.')
		   		elif part == "cabin-front":
		   			print('  You stand at the front entrance of the creepy log cabin.')
		   		elif part == "cabin-living-room":
		   			print('  In the cabin main room.')
				elif part == "mineshaft-entrance":
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
        if "grassy-field" in placesdiscovered:
            printplacesdiscovered.append("Grassy Field")
        if "forestpart1" in placesdiscovered:
            printplacesdiscovered.append("Forest")
        if "mineshaft-entrance" in placesdiscovered:
            printplacesdiscovered.append("Mineshaft Entrance")
        if "cavepart1" in placesdiscovered or "cavepart2" in placesdiscovered or "cavepart2_l1" in placesdiscovered or "cavepart2_r1" in placesdiscovered:
            printplacesdiscovered.append("Cave")
        if "cabin-front" in placesdiscovered:
            printplacesdiscovered.append("Cabin")
        print("Places Discovered: ")
        for item in printplacesdiscovered:
            print(" - " + item)
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
        print('Thats not a valid action!')
    placesdiscovered.add(part)
