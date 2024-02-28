#!/usr/bin/env python3
import pickle

##Theese Values are default values and are ment to be changed

dict = {
        "password": "",
        "host": "",
        "port": "6379",
        "queue": [],
        }

pickle.dump(dict, open("secrets.pickle", "wb"))
