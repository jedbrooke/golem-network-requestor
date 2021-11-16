# golem-network-requestor
golem provider runtime with network access via http (socks5 coming soon) proxy

Currently it is very limited. I have only tested it on small queries (fetching httpbin.org/uuid), so no idea if it will work on anything larger.

no HTTPS, only vanilla insecure http.

There is also a lot of hard coded jank, in the coming days I will add a proper cli with arg parsing etc.

# Usage
you will need:
 * `websocat`
 * a ssh pubkey (you can generate this with `ssh-keygen`)
    * you will need to update the `SSH_PUBKEY` variable in the `network_requestor.py` file with the appropriate path to your pubkey, default is `~/$USER/.ssh/id_rsa.pub`
 * `python3`
    * tested on python 3.8, will probably work with 3.6+


## To run:
first make sure your golem requestor environment is already set up
`python3 network_requestor.py`


# How does it work?
on the requestor we start a ssh shell into the provider, in this shell session we launch a http proxy on the provider. This proxy takes in tcp packets, and encodes then in base64 and prints that to stdout, which comes out of the stdout of our shell session. the requestor reads the packet, decodes it, and processes it by sending it off to its destination. Then it recieves the response, encodes it, and sends it to the shell's stdin, which goes into the stdin of the proxy running on the provider, which then decodes it and sends a tcp packet back to the process that requested it. 

it works!! 
hopfully a socks5 proxy will allow us to implement https, as well as many mining clients that support socks5.
