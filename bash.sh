#! /bin/bash

scp user@ssh.pythonanywhere.com:/home/user/main_folder/Audio/* Audio/
scp user@ssh.pythonanywhere.com:/home/user/main_folder/database.csv .

cd Audio
for i in *
do
whisper --model small --condition_on_previous_text False $i 
ssh user@ssh.pythonanywhere.com "rm /home/user/main_folder/Audio/$i"
done

cd ..

python3 modifica_csv.py

mv Audio/*.txt  ~/main_folder/Transcripts/
rm Audio/*

scp Transcripts/* user@ssh.pythonanywhere.com:/home/user/main_folder/Transcripts/
scp database.csv user@ssh.pythonanywhere.com:/home/user/main_folder/

rm Transcripts/*
rm database.csv


