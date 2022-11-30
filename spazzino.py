import pandas as pd
from numpy import nan
import os
from datetime import datetime


database = pd.read_csv("main_folder/database.csv",sep=";",index_col=0)

da_cancellare = []

for riga in database.iterrows():
    if riga[1]["pagato"] == False:
        if type(riga[1]["files"]) == str:
            da_cancellare += riga[1]["files"].split(",")

for i in da_cancellare:
    if datetime.timestamp(datetime.now()) - float(i.split("_")[1]) > 3600:
        os.remove(f"main_folder/Audio/{i}")
        database.loc[int(i.split("_")[0]),"files"] = nan
        database.loc[int(i.split("_")[0]),"tempo_files"] = 0

database.to_csv("main_folder/database.csv",sep=";")