from yapapi import Golem
from yapapi.engine import NoPaymentAccountError
from yapapi.payload import vm
from yapapi.log import enable_default_logger
from yapapi.services import Service
from datetime import timedelta
import asyncio
import os
import threading
from uuid import uuid4
import string
import random
import time
import argparse


import ssh_tcp_connection

# alpine based image
HASH = "07146c50ed1d35945063742e60daf35f7d76b2ef781df0f7152c04f0"
# ssh example image
# HASH = "1e06505997e8bd1b9e1a00bd10d255fc6a390905e4d6840a22a79902"

SSH_PUBKEY=None

class NetworkProvider(Service):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        with open(os.path.expanduser(SSH_PUBKEY),"r") as key:
            self.ssh_pubkey = key.read().strip()
    @staticmethod
    async def get_payload():
        return await vm.repo(
            image_hash=HASH,
            min_mem_gib=2.0,
            min_storage_gib=1.0,
            min_cpu_threads=1,
            capabilities=[vm.VM_CAPS_VPN]
        )
    async def start(self):
        print("starting")
        async for script in super().start():
            yield script
        script = self._ctx.new_script(timeout=timedelta(seconds=30))

        # set up SSH server
        script.run("/bin/bash", "-c", "syslogd")
        script.run("/bin/bash", "-c", "mkdir /root/.ssh")
        script.run("/bin/bash", "-c", "ssh-keygen -A")
        script.run("/bin/bash", "-c", "ssh-keygen -t rsa -f /root/.ssh/id_rsa -N '' -q")
        
        # copy over our public key
        script.run("/bin/bash", "-c", f"echo -n \"{self.ssh_pubkey}\" > /root/.ssh/authorized_keys")
        # script.run("/bin/bash", "-c", "cat /root/.ssh/authorized_keys")
        script.run("/bin/bash","-c","mkdir -p /run/sshd")

        # we still need to set a password even though we wont use it for ssh
        password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        script.run("/bin/bash", "-c", f'echo -e "{password}\n{password}" | passwd')
        script.run("/bin/bash", "-c", "/usr/sbin/sshd")

        yield script

        connection_uri = self.network_node.get_websocket_uri(22)
        app_key = os.environ.get("YAGNA_APPKEY")

        ssh_cmd = f"ssh -tt -o ProxyCommand='websocat asyncstdio: {connection_uri} --binary -H=Authorization:\"Bearer {app_key}\"' -o StrictHostKeyChecking=accept-new -i {os.path.splitext(SSH_PUBKEY)[0]} root@{uuid4().hex}"
        print(ssh_cmd)
        print("starting proxy server")
        threading.Thread(target=ssh_tcp_connection.main,args=(ssh_cmd,),daemon=True).start()

        # wait for ssh connection to open
        time.sleep(15)
        
    async def run(self):
        print("running")

        script = self._ctx.new_script(timeout=timedelta(seconds=100))
        print("running curl")
        script.run("/bin/bash","-c","touch /golem/output/output.txt")
        script.upload_file("get_payload.sh","/golem/work/get_payload.sh")
        script.run("/bin/bash","-c","chmod +x /golem/work/get_payload.sh")
        script.run("/bin/bash","-c","/golem/work/get_payload.sh")
        script.run("/bin/bash", "-c", f"echo from provider {self._ctx.provider_name} >> /golem/output/output.txt")
        yield script


    async def shutdown(self):
        print("shutting")
        script = self._ctx.new_script(timeout=timedelta(seconds=10))
        print("fetching output")
        script.download_file("/golem/output/output.txt",f"output/{self._ctx.provider_name}_output.txt")
        yield script

async def main(budget,subnet_tag,payment_driver,payment_network,log_file=None):
    if not log_file is None:
        enable_default_logger(log_file=log_file,debug_activity_api=True,debug_payment_api=True)
    
    async with Golem(
        budget=budget,
        subnet_tag=subnet_tag,
        payment_driver=payment_driver,
        payment_network=payment_network
    ) as golem:
        network = await golem.create_network("192.168.0.1/24")
        async with network:
            cluster = await golem.run_service(NetworkProvider, network=network, num_instances=1)
            def instances():
                if len(cluster.instances) > 0:
                    return [f"{s.provider_name}: {s.state.value}" for s in cluster.instances]
                else:
                    return "No instances"
            while True:
                print(instances())
                try:
                    await asyncio.sleep(5)
                    if all(s.state.value == 'terminated' for s in cluster.instances) and len(cluster.instances) > 0:
                        break
                except (KeyboardInterrupt, asyncio.CancelledError):
                    break
            cluster.stop()
            
def parse_args():
    parser = argparse.ArgumentParser(description="demo of netowrk access from within a provider")
    golem_options = parser.add_argument_group("Golem Options","Settings for the golem network configuration. Default is to run on testnet")
    golem_options.add_argument("--budget",default=1,type=float, help="bugdet in GLM or tGML for the task")
    golem_options.add_argument("--mainnet",action="store_true",help="equivalent to --subnet_tag=mainnet --payment_driver=zksync --payment_network=mainnet")
    golem_options.add_argument("--subnet_tag",default="devnet-beta",help="golem subnet [default: devnet-beta] [suggested values: devnet-beta, mainnet]")
    golem_options.add_argument("--payment_driver",default="zksync", help="golem payment driver [default: zksync] [possible values: zksync, erc20]")
    golem_options.add_argument("--payment_network",default="rinkeby", help="golem payment network [default: rinkeby] [possible values: mainnet, rinkeby]")
    golem_options.add_argument("--ssh_pubkey",default="~/.ssh/id_rsa.pub", help="public ssh key needed to connect to provider [default: ~/.ssh/id_rsa.pub]")
    golem_options.add_argument("--log_file",help="path to output for log file")
    golem_options.set_defaults(budget=1,subnet_tag="devnet-beta",payment_driver="zksync",payment_network="rinkeby",ssh_pubkey="~/.ssh/id_rsa.pub")

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    SSH_PUBKEY=args.ssh_pubkey
    print("using key:",SSH_PUBKEY)

    if not os.path.exists("output"):
        print("creating output dir")
        os.mkdir("output")
    
    loop = asyncio.get_event_loop()
    task = loop.create_task(
        main(
            budget=args.budget,
            subnet_tag=args.subnet_tag,
            payment_driver=args.payment_driver,
            payment_network=args.payment_network,
            log_file=args.log_file
        )
    )
    try:
        loop.run_until_complete(task)
    except NoPaymentAccountError as e:
        handbook_url = (
            "https://handbook.golem.network/requestor-tutorials/"
            "flash-tutorial-of-requestor-development"
        )
        print(
            f"No payment account initialized for driver `{e.required_driver}` "
            f"and network `{e.required_network}`.\n\n"
            f"See {handbook_url} on how to initialize payment accounts for a requestor node."
        )
    except KeyboardInterrupt:
        print(
            "Shutting down gracefully, please wait a short while "
            "or press Ctrl+C to exit immediately..."
        )
        task.cancel()
        try:
            loop.run_until_complete(task)
            print(
                f"Shutdown completed, thank you for waiting!"
            )
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass