from __future__ import annotations

import datetime
import time
from collections import deque
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

from Chapter7_02.LiquidityProvider import LiquidityProvider
from Chapter7_02.MarketSimulator import MarketSimulator
from Chapter7_02.OrderBook import OrderBook
from Chapter7_02.OrderManager import OrderManager
from Chapter9.TradingStrategyDualMA import TradingStrategyDualMA


def call_if_not_empty(deq: deque, fun: callable):
    while len(deq) > 0:
        fun()


class EventBasedBackTester:
    lp_2_gateway: deque[Any]
    ob_2_ts: deque[Any]
    ts_2_om: deque[Any]
    ms_2_om: deque[Any]
    om_2_ts: deque[Any]
    gw_2_om: deque[Any]
    om_2_gw: deque[Any]

    lp: LiquidityProvider
    ob: OrderBook
    ts: TradingStrategyDualMA
    ms: MarketSimulator
    om: OrderManager

    def __init__(self):
        self.lp_2_gateway = deque()
        self.ob_2_ts = deque()
        self.ts_2_om = deque()
        self.ms_2_om = deque()
        self.om_2_ts = deque()
        self.gw_2_om = deque()
        self.om_2_gw = deque()

        self.lp = LiquidityProvider(self.lp_2_gateway)
        self.ob = OrderBook(self.lp_2_gateway, self.ob_2_ts)
        self.ts = TradingStrategyDualMA(self.ob_2_ts, self.ts_2_om, self.om_2_ts)
        self.ms = MarketSimulator(self.om_2_gw, self.gw_2_om)
        self.om = OrderManager(self.ts_2_om, self.om_2_ts, self.om_2_gw, self.gw_2_om)

    def process_data_from_yahoo(self, price):
        order_bid: dict[str, str | int] = {
            "id": 1,
            "price": price,
            "quantity": 1000,
            "side": "bid",
            "action": "new",
        }
        order_ask: dict[str, str | int] = {
            "id": 1,
            "price": price,
            "quantity": 1000,
            "side": "ask",
            "action": "new",
        }
        self.lp_2_gateway.append(order_ask)
        self.lp_2_gateway.append(order_bid)
        self.process_events()
        order_ask["action"] = "delete"
        order_bid["action"] = "delete"
        self.lp_2_gateway.append(order_ask)
        self.lp_2_gateway.append(order_bid)

    def process_events(self):
        while len(self.lp_2_gateway) > 0:
            call_if_not_empty(self.lp_2_gateway, self.ob.handle_order_from_gateway)
            call_if_not_empty(self.ob_2_ts, self.ts.handle_input_from_bb)
            call_if_not_empty(self.ts_2_om, self.om.handle_input_from_ts)
            call_if_not_empty(self.om_2_gw, self.ms.handle_order_from_gw)
            call_if_not_empty(self.gw_2_om, self.om.handle_input_from_market)
            call_if_not_empty(self.om_2_ts, self.ts.handle_response_from_om)


eb = EventBasedBackTester()


def load_financial_data(ticker: str, start_date: str, end_date: str, output_file: str):
    try:
        df: pd.DataFrame = pd.read_pickle(output_file)
        print(f"File data found...reading {ticker} data")
    except FileNotFoundError:
        print(f"No data file found for {ticker}, downloading {ticker} data...")

        # df = data.DataReader("GOOG", "yahoo", start_date, end_date)
        df = yf.download(ticker, start=start_date, end=end_date)
        df.to_pickle(output_file)
    return df


ticker = "NFLX"
start_date = "2001-01-01"
end_date = datetime.date.today().strftime("%Y-%m-%d")
output_file = f"data//{ticker}_data_{start_date}_{end_date}.pkl"
stock_data = load_financial_data(
    ticker=ticker,
    start_date=start_date,
    end_date=end_date,
    output_file=output_file,
)

time_start = time.time()
line: tuple[int | pd.Series]
for line in zip(stock_data.index, stock_data["Adj Close"]):
    date = line[0]
    price = line[1]
    price_information = {"date": date, "price": float(price)}
    eb.process_data_from_yahoo(price_information["price"])
    eb.process_events()
time_end = time.time()
print("Time spent: ", time_end - time_start)

plt.plot(
    stock_data.index,
    eb.ts.list_paper_total,
    label=(f"Trading Strategy Dual MA for {ticker}"),
)
plt.plot(
    stock_data.index, eb.ts.list_total, label=f"Trading Strategy Dual MA for {ticker}"
)
plt.plot(
    stock_data.index,
    (stock_data["Adj Close"] / stock_data["Adj Close"][0]) * eb.ts.list_paper_total[0],
    label=f"Buy and Hold {ticker}",
)
# show the x label on the graph
plt.xlabel("Days")
plt.legend()
plt.title(f"Trading Strategy Dual MA for {ticker}")
plt.show()
