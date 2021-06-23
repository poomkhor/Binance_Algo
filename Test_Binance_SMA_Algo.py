import os
import time
import datetime as dt
import pandas as pd
from binance.client import Client
from binance import ThreadedWebsocketManager, BinanceSocketManager
from binance.enums import *
from twisted.internet import reactor

'''for threaded websocket manager the connection requires api_key and api_secret instead of client arg*
declare self.con init as a threadedWebsocketMaager directly, do not have to declare client first
ThreadedWebsocketManager is an asynchronous. Once connection start can directly callback function which 
is SMA_trade receiving msg and directly append to dataframe then process the strategy before firing the order
'''    
api_key = 'UeRMEYWx3LWuWFFt47Y5jd94j9w2qCQtWqSJfSySz4PLjbH7gkzwPZX7Nh9mxEnl'
api_secret = '9oCJjPb9Hxb9czkTnjXRXRTWGkUh2RbVbaLyFW3uz3lAv3uZBSvs9MhshttEDSLW'

class SMATrading:
    
    def __init__(self, symbol, units):
#         initializing the trading class
        self.con = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret, testnet=True)
        self.client = Client(api_key, api_secret, testnet = True)
        self.symbol = str(symbol)
        self.units = int(units)
        self.data = pd.DataFrame()
        self.ticks = 0
        self.position = 0
        self.timestamp = dt.datetime.now()
    
    def streaming(self):
        self.con.start()
        connection = self.con.start_kline_socket(callback=self.SMA_Trade, symbol = self.symbol)
    
    def SMA_Trade(self, msg):
        if msg['e'] != 'error':
            kline = msg['k']
            Close = kline['c']
            self.ticks += 1
            self.data = self.data.append(pd.DataFrame({'Close': kline['c']}, index = [self.timestamp]), sort = True)
            
        self.data['SMA1'] = self.data['Close'].rolling(5).mean().round(2)
        self.data['SMA2'] = self.data['Close'].rolling(10).mean().round(2)
        
        SMA1 = self.data['SMA1'][-1]
        SMA2 = self.data['SMA2'][-1]
        print(f'{self.ticks} | {self.timestamp} | {Close} | SMA1 {SMA1} | SMA2 {SMA2}')
        
        '''
        still missing data resampling in this code, need to adjust after connection testing complete
                
        '''
        
        if (self.data['SMA1'].iloc[-1] > self.data['SMA2'].iloc[-1]) and (self.position == 0):
            self.data['Signal'] = 1
            print('Create | BUY ORDER')
            Symbol = self.symbol
            self.order = self.client.create_test_order(
            symbol = 'BTCUSDT',
            side = SIDE_BUY,
            type = ORDER_TYPE_LIMIT,
            timeInForce = TIME_IN_FORCE_GTC,
            quantity = self.units,
            price = self.data['Close'][-1]
            )
            self.position = 1
        
        elif (self.data['SMA1'].iloc[-1] < self.data['SMA2'].iloc[-1]) and (self.position == 1):
            self.data['Signal'] = -1
            print('Create | SELL ORDER')
            Symbol = self.symbol
            self.order = self.client.create_test_order(
            symbol = 'BTCUSDT',
            side = SIDE_SELL,
            type = ORDER_TYPE_LIMIT,
            timeInForce = TIME_IN_FORCE_GTC,
            quantity = self.units,
            price = self.data['Close'][-1]
            )
            self.position = 0
    
    def stop_strategy(self):
        self.con.stop()
    
if __name__ == '__main__':
    sma = SMATrading('BTCUSDT', 2000)
    time.sleep(7)
    sma.streaming()
        

# adjust to include Trading ID and filled price
# adjust to include method to easily request historical trade
# adjust create_test_order to be able to take self.symbol, self.units
# adjust class SMATrading to be able to input SMA1, SMA2 args plus condition to check SMA1 to be less than SMA2
# prevent order from firing after the first SMA has been calculated

# backtesting class to find the best optimal SMA combinations.
# check timestamp since it remains the same throughout the connection
