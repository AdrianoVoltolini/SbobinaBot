import pandas as pd
from numpy import nan
import os

database = pd.read_csv("database.csv",sep=";",index_col=0)

for audio in os.listdir("Audio"):
    client_id = int(audio.split("_")[0])
    database.loc[client_id,"tempo_files"] = 0
    database.loc[client_id,"files"] = nan
    database.loc[client_id,"pagato"] = False
    database.loc[client_id,"tempo_pagato"] = 0


database.to_csv("database.csv",sep=";")