#!/usr/bin/python3

"""
This script scans for all optionable symbols on Ameritrade to identify the highest premium for committed capital on short cash-covered puts. 

I noticed new IPOs tend to show higher put premiums, so I automatically update the symbols list from NASDAQ FTP server. 
"""

import os
import json
import time
import datetime 

api_key = ""

def updateSymbols():
    
    # get new symbols from FTP server
    cmd = 'curl -s ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt | grep -v "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares" | grep -v "File Creation Time: " | cut -d "|" -f 1'
    new_symbols = os.popen(cmd).read().split('\n')

    cmd = 'curl -s ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt | grep -v "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol" | grep -v "File Creation Time: " | cut -d "|" -f 1'
    new_symbols += os.popen(cmd).read().split('\n')

    # get known symbols from file
    symbols_file = open('symbols', 'w+')
    known_symbols = list(symbols_file.readlines())
    
    # merge lists
    symbols = set(new_symbols).union(set(known_symbols))
    symbols = sorted(list(symbols))

    for line in symbols: 
        symbols_file.write(line + '\n')
    
    symbols_file.close()

    return 0

def getReturn(ticker): 

    # find next Friday
    today = datetime.date.today()
    friday = str(today + datetime.timedelta( (4-today.weekday()) % 7 ))

    # request option chain
    cmd = 'curl -s -X GET --header "Authorization: " "https://api.tdameritrade.com/v1/marketdata/chains?apikey={}&symbol={}&contractType=PUT&strikeCount=2&includeQuotes=FALSE&strategy=ANALYTICAL&range=OTM&toDate={}"'.format(api_key, ticker, friday)
    options = json.loads(os.popen(cmd).read())

    print(options)

    if list(options.keys())[0] == "error": return 2
    if options['status'] == 'FAILED': return 1

    # print("Symbol: {} | Status: {} |".format(ticker, options['status']))

    # extract mark, strike, bid for each option
    market = options['underlyingPrice']
    expires = str(list(options['putExpDateMap'].keys())[0])
    strike = list(options['putExpDateMap'][expires].keys())[0]
    bid = options['putExpDateMap'][expires][str(strike)][0]['bid']

    # get rid of iliquid and OTM
    if bid == 0.0: return 1 
    if float(strike) > float(market): return 1

    # compute return
    margin = (float(strike)* 100)
    profit = (float(bid)* 100)
    
    gain = margin / profit
    gain = 1/ gain
    gain = gain*100

    # write to file
    out_file = open("output.log", 'a+')
    out = "{},{},{}\n".format(ticker, str(gain), str(margin))
    out_file.write(out)
    out_file.close()

    return 0


updateSymbols()

# open symbols / read into list
symbols = open('symbols', 'r').readlines()

# for each symbol, place result of getReturn into list
for symbol in symbols:
    if getReturn(symbol.strip()) == 2:
        time.sleep(31)
        getReturn(symbol.strip())

