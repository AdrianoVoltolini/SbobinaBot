import logging

import os

import pandas as pd
from numpy import nan

from datetime import datetime

from telegram import Update, LabeledPrice

from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater, PreCheckoutQueryHandler)




# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    database = pd.read_csv("main_folder/database.csv",sep=";",index_col=0)
    user = update.effective_user
    if user.id not in database.index:
        newline = pd.DataFrame({"pagato":False,"tempo_gratis":3600,"tempo_files":0,"tempo_pagato":0,"files":nan},index=[user.id])
        database = pd.concat([database, newline],axis=0)
        database.to_csv("main_folder/database.csv",sep=";")
    update.message.reply_markdown_v2('''
Ciao\!

Trascrivo audio inglesi o italiani a pagamento al costo di 2,50€ l'ora\. La prima ora è gratis\!

Consegna prevista entro 24 ore\.

Per maggiori informazioni, scrivi /aiuto
'''
        )


def aiuto(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('''
Invia come allegato i file audio che vuoi sbobinare.

Un singolo file può essere grande al massimo 100 MB.

Chiedi il preventivo e paga scrivendo /carrello
Il pagamento avverrà tramite il servizio offerto da telegram.

Controlla se i tuoi trascritti sono pronti scrivendo /pronto

I trascritti saranno inviati in questa chat.
'''
    )

def audio(update: Update, context: CallbackContext) -> None:
    database = pd.read_csv("main_folder/database.csv",sep=";",index_col=0)
    user = update.effective_user
    new_file = context.bot.get_file(update.message.audio.file_id)
    if database.loc[user.id,"pagato"] == False:
        if update.message.audio.file_size < 100000000:
            cnt = 0
            for i in os.listdir("main_folder/Audio"):
                cnt += int(os.path.getsize(f"main_folder/Audio/{i}"))
            if cnt < 650000000:
                file_name = f"{user.id}_{datetime.timestamp(datetime.now())}"
                new_file.download(f"main_folder/Audio/{file_name}")
                if type(database.loc[user.id,"files"]) != str:
                    database.loc[user.id,"files"] = file_name
                else:
                    database.loc[user.id,"files"] += ","+file_name
                database.loc[user.id,"tempo_files"] += update.message.audio.duration
                update.message.reply_text("""
    Caricamento avvenuto con successo.
    Se non procedi con il pagamento scrivendo /carrello, il file sarà eliminato tra circa un'ora.
                """)
            else:
                update.message.reply_text("Caricamento fallito. Il server è pieno, riprova più tardi.")
        else:
            update.message.reply_text("Caricamento fallito. Il file è troppo grande")
    else:
        update.message.reply_text("Caricamento fallito. Hai già fatto un ordine che deve essere ancora elaborato.")
    database.to_csv("main_folder/database.csv",sep=";")

def altro(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Caricamento fallito. Non accetto input di questo tipo.")

def carrello(update: Update, context: CallbackContext) -> None:
    database = pd.read_csv("main_folder/database.csv",sep=";",index_col=0)
    user = update.effective_user

    if database.loc[user.id,"pagato"] == False and type(database.loc[user.id,"files"]) == str:

        if database.loc[user.id,"tempo_files"] <= database.loc[user.id,"tempo_gratis"]:
            database.loc[user.id,"tempo_pagato"] = 0
            database.loc[user.id,"tempo_gratis"] -= database.loc[user.id,"tempo_files"]
        else:
            database.loc[user.id,"tempo_pagato"] = database.loc[user.id,"tempo_files"] - database.loc[user.id,"tempo_gratis"]
            database.loc[user.id,"tempo_gratis"] = 0

        prezzo = round(database.loc[user.id,"tempo_pagato"] /36*2.5)

        if prezzo == 0:
            database.loc[user.id,"pagato"] = True
            update.message.reply_text("""
Non c'è bisogno che paghi per questa volta!

I tuoi file audio sono stati presi in carico.
Controlla se sono pronti scrivendo /pronto
            """)

        elif prezzo > 0 and prezzo < 100:
            update.message.reply_text(f"""
il prezzo sarebbe di {prezzo/100}€, ma il pagamento minimo è di 1.00€.
Carica altri file audio per continuare con l'ordine""")
        else:
            out = context.bot.send_invoice(
                chat_id=update.message.chat_id,
                title="Pagamento",
                description="Il prezzo è già scontato",
                payload="test",
                provider_token="INSERT STRIPE TOKEN HERE",
                currency="EUR",
                prices=[LabeledPrice("Give", prezzo)],
                need_name=False,
            )
    else:
        update.message.reply_text("Utilizzo di /carrello non valido")
    database.to_csv("main_folder/database.csv",sep=";")


def pronto(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.message.chat_id
    cnt = False
    directory = "main_folder/Transcripts/"
    for i in os.listdir(directory):
        file_id = i.split("_")[0]
        if int(user.id) == int(file_id):
            with open(f"{directory}{i}","rb") as testo:
                context.bot.send_document(chat_id,testo)
            cnt = True
            os.remove(f"/home/Lottimismo/main_folder/Transcripts/{i}")

    if cnt == False:
        update.message.reply_text("""
Non è stato trovato alcun trascritto pronto per te.
Riprova più tardi.
        """)

def pre_checkout_handler(update: Update, context: CallbackContext):
    """https://core.telegram.org/bots/api#answerprecheckoutquery"""

    database = pd.read_csv("main_folder/database.csv",sep=";",index_col=0)
    user = update.effective_user

    query = update.pre_checkout_query

    if database.loc[user.id,"tempo_files"] <= database.loc[user.id,"tempo_gratis"]:
        da_pagare = 0
    else:
        da_pagare = database.loc[user.id,"tempo_files"] - database.loc[user.id,"tempo_gratis"]

    if int(query.total_amount) == round(da_pagare/36*2.5):
        query.answer(ok=True)
    else:
        query.answer(ok=False,error_message="Pagamento non corrisponde al servizio richiesto.")


def successful_payment_callback(update: Update, context):
    database = pd.read_csv("main_folder/database.csv",sep=";",index_col=0)
    user = update.effective_user
    database.loc[user.id,"pagato"] = True
    database.to_csv("main_folder/database.csv",sep=";")
    update.message.reply_text("""
Pagamento avvenuto con successo. I tuoi file audio sono stati presi in carico.
Controlla se sono pronti scrivendo /pronto
    """)

def main() -> None:
    #Start the bot.
    # Create the Updater and pass it your bot's token.
    updater = Updater("INSERT TELEGRAM TOKEN HERE")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("aiuto", aiuto))
    dispatcher.add_handler(CommandHandler("carrello", carrello))
    dispatcher.add_handler(CommandHandler("pronto", pronto))

    # on non command i.e message - echo the message on Telegram
    # dispatcher.add_handler(MessageHandler(Filters.text and ~Filters.command, echo))

    dispatcher.add_handler(MessageHandler(Filters.audio , audio))
    dispatcher.add_handler(MessageHandler(Filters.voice or Filters.video, altro))

    dispatcher.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    dispatcher.add_handler(MessageHandler(Filters._SuccessfulPayment, successful_payment_callback))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()