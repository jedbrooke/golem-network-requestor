# golem-network-requestor
golem provider runtime with network access via http (socks5 coming in the future) proxy

Currently it is very limited. It should work on larger queries, and consecutive queries, and can only process 1 client at a time, so concurrent queries will simply wait to be served. only tested with HTTP GET requests. CONNECT fails for sure, have not tested POST or PUT.

no HTTPS, only vanilla insecure http.

# Usage
you will need:
 * `websocat`
 * a ssh pubkey (you can generate this with `ssh-keygen`)
    * you can use the `--ssh_pubkey` arg if your ssh pubkey is in a different location. default is `~/.ssh/id_rsa.pub`
 * `python3`
    * tested on python 3.8, will probably work with 3.6+


## To run the demo:
first make sure your golem requestor environment is already set up, then run

`python3 network_requestor.py`

## To make your own networked requestors:
click the "use this template" button to make a copy (not a fork) of this repo. Then, you can change the `get_payload.sh` file and put your own workload in there.
just use `curl --proxy http://localhost:4242 [...]` for your curl requests.

If you want to make your own docker container/gvmi, look at the comments in the `Dockerfile` to see which components are required, as well as the comments in the code for setting up the ssh connection. 


# How does it work?
on the requestor we start a ssh shell into the provider, in this shell session we launch a http proxy on the provider. This proxy takes in tcp packets, and encodes then in base64 and prints that to stdout, which comes out of the stdout of our shell session. the requestor reads the packet, decodes it, and processes it by sending it off to its destination. Then it recieves the response, encodes it, and sends it to the shell's stdin, which goes into the stdin of the proxy running on the provider, which then decodes it and sends a tcp packet back to the process that requested it. 

it works!! 
hopfully a socks5 proxy will allow us to implement https, as well as many mining clients that support socks5.
