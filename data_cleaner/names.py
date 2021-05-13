import os
import re
import pandas as pd
import numpy as np


current_folder = os.getcwd() # gets the current directory
folder_path = next(os.walk(current_folder))[1] # gets a list of all folders in the current directory

df = pd.DataFrame(columns = ["Case Name", "Annotator Name", "Body Name", "Body Number", "GR", "MAF", "MP"])
for folder in folder_path: # iterates through all cases in a folder
    bodies = []
    os.chdir(current_folder + "\\" + folder)
    files = [".".join(x.split(".")[:-1]) for x in os.listdir() if os.path.isfile(x)] # splits off the extension
    for image in files: # iterating thru each image
        mp = ""
        maf = ""
        gr = ""
        name_index = 0
        number_index = 0
        words = re.split(r"[,|\s|_]+", image) # split name into a list of words
        for i in range(len(words) - 1, 0, -1):
            if bool(re.search(r"\d", words[i])): # if it contains a digit it aint a name
                number_index = i
                break
            else:
                if re.search("^MP", words[i], re.IGNORECASE):
                    mp = "MP"
                if re.search("^MAF", words[i], re.IGNORECASE):
                    maf = "MAF"
                if re.search("^GR(een)?$", words[i], re.IGNORECASE):
                    gr = "GR"
        for i in range(0, len(words) - 1):
            if not bool(re.search(r"\d", words[i])):
                if words[i].lower() != folder.split()[-1].lower():
                    name_index = i
                    break

        name = " ".join(words[name_index:number_index]) # joins the unused words into a name
        body_info = [folder.split()[0], folder.split()[-1], name, words[number_index]]
        for i in (gr, maf, mp):
            if i:
                body_info.append(i)
            else:
                body_info.append(None) # appends a none if no footnotes exist
        bodies.append(body_info)
    df = df.append(pd.DataFrame(bodies, columns = df.columns))

os.chdir(current_folder) # returns to original folder
df.to_csv("data.csv", index = False)