import random
import os
import time
import ctypes
from sys import platform

basedir = os.path.abspath(os.path.dirname(__file__))

if platform == "linux" or platform == "linux2":
    tpdir = os.path.join(basedir, 'lib/libtp.so')
elif platform == "win32":
    tpdir = os.path.join(basedir, 'lib/libtp.dll')

tplib = ctypes.CDLL(tpdir)

def getSeed():
    pattern = random.randint(0, 3)
    seed = random.randint(0, 2**32 - 1)

    return pattern, seed


def getPrice(pattern, seed):
    tplib.initTpPrices(pattern, seed)
    tmp = []

    for i in range(13):
        tmp.append(tplib.getTpPrice(i))

    return tmp


def getCurPrice(pattern, seed):
    priceTable = getPrice(pattern, seed)
    days = int(time.strftime("%w"))
    isAm = 0
    if time.strftime("%p") == 'AM':
        isAm = 1
    hour = int(time.strftime("%H"))
    type = days * 2 - isAm
    # if hour < 5:
    #     type -= 1
    if str(type) == '-1':
        type = 0
    isBuy = type == 0 and hour > 4
    price = priceTable[type]
    isDisable = isBuy and not isAm
    isShopClose = hour > 21 or hour < 8
    # realPrice = price
    if isDisable:
        # price = realPrice = 0
        isBuy = False
    # if isShopClose:
    #     realPrice = int(0.8 * int(price))

    return price, isBuy, isDisable, isShopClose


def getCurType():
    days = int(time.strftime("%w"))
    isAm = 0
    if time.strftime("%p") == 'AM':
        isAm = 1
    hour = int(time.strftime("%H"))
    type = days * 2 - isAm
    if hour < 5:
        type -= 1
    if str(type) == '-1':
        type = 0
    return type