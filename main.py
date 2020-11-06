from queue import Queue
import requests
import random
from typing import List
import queue
import threading
import string
import logging
import time


class NitroGen:
    def __init__(
        self, numberOfCodes: int, nitroType: str, numberOfThreads: int
    ) -> None:
        logging.basicConfig(format="%(message)s", level=logging.INFO)
        self.numberOfCodes = numberOfCodes
        self.nitroType = nitroType
        self.codeLength = 16 if nitroType == "classic" else 24
        self.allProxies = []
        self.proxyQueue = queue.Queue()
        self.loadProxies()
        self.lockProxy = threading.Lock()
        self.lockCode = threading.Lock()
        self.numberOfThreads = numberOfThreads
        self.url = r"https://discordapp.com/api/v6/entitlements/gift-codes"

    def loadProxies(self) -> bool:
        with open("proxies.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.count(".") == 3:
                    self.allProxies.append(line)
                    self.proxyQueue.put(line)
        return True

    def saveProxies(self) -> bool:
        with self.lockProxy:
            with open("proxies.txt", "w") as f:
                f.write("\n".join(self.allProxies))
        return True

    def saveCode(self, code: str) -> bool:
        with self.lockCode:
            with open("working-codes.txt", "a+") as f:
                f.write(f"https://discord.gift/{code}")
            self.numberOfCodes -= 1
        return True

    def start(self) -> bool:
        threads = []
        # try:
        for i in range(self.numberOfThreads):
            logging.info(f"Started thread {i+1}")
            thread = threading.Thread(target=self.checkCode)
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for i, thread in enumerate(threads):
            thread.join()
            logging.info(f"Thread {i+1} finished")
        logging.info("All codes generated, goodbye")

    def checkCode(self) -> None:
        while self.numberOfCodes > 0:
            code = "".join(
                [
                    random.choice(string.ascii_letters + string.digits)
                    for i in range(self.codeLength)
                ]
            )
            proxy = self.proxyQueue.get()
            proxyReq = {"https": proxy}
            try:
                req = requests.get(f"{self.url}/{code}", proxies=proxyReq, timeout=10)
                if req.status_code == 200:
                    logging.info(f"\n\n!!!!!\nWorking code found : {code}\n!!!!!\n\n")
                    self.saveCode(code)
                    self.proxyQueue.put(proxy)
                elif req.status_code == 404:
                    logging.info(f"Invalid code: {code}")
                    self.proxyQueue.put(proxy)
                elif req.status_code == 429:
                    thread = threading.Thread(
                        target=self.reenableRateLimitedProxy, args=[proxy]
                    )
                    thread.setDaemon(True)
                    thread.start()
                    logging.info(f"Proxy {proxy} ratelimited")
            except (
                requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
            ):
                self.allProxies.remove(proxy)
                self.saveProxies()
                logging.info(f"Deleted bad proxy {proxy}")

    def reenableRateLimitedProxy(self, proxy: str) -> bool:
        # How long are proxies ratelimited for?
        # Assuming 30s ??
        time.sleep(30)
        self.proxyQueue.put(proxy)
        logging.info(f"Renabled proxy {proxy}")
        return True


if __name__ == "__main__":
    while True:
        try:
            numberOfCodes = int(
                input("How many working codes do you want to generate: ")
            )
            break
        except ValueError:
            print("Numbers only")

    while True:
        print("Classic Nitro is 16chars and Boost Nitro is 24 chars")
        nitroType = input("Which to generate? (classic or boost): ")
        if nitroType in ("classic", "boost"):
            break
        print("'classic' or 'boost' are the only accepted responses")

    while True:
        try:
            print(
                "The more proxies you have, the more simultaneous threads you can use"
            )
            numberOfThreads = int(input("How many simultaneous threads: "))
            break
        except ValueError:
            print("Numbers only")

    nitrogen = NitroGen(numberOfCodes, nitroType, numberOfThreads)
    nitrogen.start()


