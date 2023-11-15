#!/usr/bin/env python3
import pickle
import base64
# Theese Values are default values and are ment to be changed
# Edit this DICT with the Values needed for the Secrets File inside the Script

dicts = {
        "server": "",
        "port": 22,
        "user": "root",
        "key": "/root/.ssh/keyfile",
        }

encoded_dict = str(dicts).encode("utf-8")
encoded_dict = base64.b64encode(encoded_dict)
pickle.dump(encoded_dict, open("secrets.pickle", "wb"))
