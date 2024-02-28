#!/usr/bin/env python3
import pickle
import base64
# Theese Values are default values and are ment to be changed

dicts = {
        "remote": "localhost",
        "port": 22,
        "user": "root",
        "identity": None,
        "password": None,
        "codes": ["200", "301", "302", "401", "403", "404", "500"],
        "targethost": ""
        "logging": True,
        "loglevel": "INFO"
}

encoded_dict = str(dicts).encode("utf-8")
encoded_dict = base64.b64encode(encoded_dict)
pickle.dump(encoded_dict, open("secrets.pickle", "wb"))
