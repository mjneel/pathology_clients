import pandas as pd
import numpy as np
import re
import os
import sys

# scans the inputted string to check if its a valid directory and valid file type (.csv)
def directory_checker(path):
    if os.path.exists(path) == True:
        for fp in path: 
            ext = os.path.splitext(path)[1]
            if ext == '.csv':
                return True
            else: 
                print("Please enter a valid file type (.csv only).")
                return False
    else:   
        print("Please enter a valid directory.")
        return False

x = 0
paths = []
# enter results.csv for appending. Make sure the results are chronological
while True:
    print("Enter File Directory " + str(x + 1) + ". Type done to continue. Type exit to leave the program: ")
    path = input()
    if re.search("^d(one)?$", path, re.IGNORECASE):
        break
    elif re.search("^e(xit)?$", path, re.IGNORECASE):
        sys.exit()
    elif directory_checker(path) == True:
        paths.append(path)
        print(paths[x] + " entered")
        x += 1

# dataframe parsed here
df = pd.read_csv(paths[0], usecols = ["Angle", "Length", "File Name"])

# append more data on after
if x > 1:
    for i in range(1, len(paths)):
        datatmp = pd.read_csv(paths[i], usecols = ["Angle", "Length", "File Name"])
        df = df.append(datatmp, ignore_index = True)



# scans filename to get the name of the body 
def fileNameGet(name):
    if re.search("False", name, re.IGNORECASE):
        return "Green Spear"
    elif re.search("Green(Spear)? (?!_Spear)(?! Spear)",name, re.IGNORECASE):
        return "Green Spear"
    elif re.search("Spear", name, re.IGNORECASE):
        return "Spear"
    elif re.search("Cre(scent)?", name, re.IGNORECASE):
        return "Crescent"

# get number of body 
def fileNumberGet(name):
    for x in range(len(name) - 1, 0, -1): # gets the index position of the last number in the string
        if name[x].isdigit():
            endNumber = x 
            break
    for i in range(endNumber, 0, -1): # gets the index position of when the last string of numbers begins
        if name[i].isdigit() == False:
            startNumber = i + 1
            break
    return name[startNumber : endNumber + 1]

def checkData(frame, fileName):
    if len(frame) != 3:
        print("Too many measurements " + fileName)
        print(len(frame))
        return False
    elif frame['Angle'].count() != 1:
        print("Too many angles at " + fileName)
        return False
    elif frame["Length"].count() != 2:
        print("Too many lengths at " + fileName)
        return False
    else:
        return True

def createData(groups):
    data = []
    for name, group in groups:
        fileFrame = gk.get_group(name)
        fileFrame = fileFrame.replace(0,np.nan)
        if checkData(fileFrame, name):
            bodyName = fileNameGet(name)
            bodyNumber = fileNumberGet(name)
            ang = round(fileFrame['Angle'].max(), 3)
            ang2 = 180 - ang
            shorter = round(fileFrame['Length'].min(0), 3)
            longer = round(fileFrame["Length"].max(), 3)
            symm = round(shorter / longer, 3)
            nextRow = [bodyName, bodyNumber, ang, ang2, shorter, longer, symm]
            data.append(nextRow)
    return data

gk = df.groupby('File Name')
finalData = pd.DataFrame(createData(gk), columns = ['Annotator Label', 'Annotator Number', 'Angle', 
                                        '180-angle', 'Shorter Prong', 'Longer Prong', 'Symmetry'])

finalData.to_csv("a.csv")


