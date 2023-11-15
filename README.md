# prometheus_simple_checks

A set of prometheus textfile exporter scripts that you can easily use.

You may download the imports before or just compile it into a binary. Either way it works

Maybe you do not wish to download an entire exporter and use a simple and easily maintainable script. So feel free to use them. 


To use the -s / --secret Flag inside my scripts you may generate a secrets.pickle file with the generator script. This does nothing but encode the dict inside before pickle dumps it into the file so you may not worry about 
plain text secrets. 

The reason why I use this is because I am to lazy to type in each command while testing the script.

You can use environment variables aswell.
There are plenty of ways to do this.

I do not reccomend storing secrets at all as a file you should rather use a decentralized secret management service like Hashicorp Vault.

