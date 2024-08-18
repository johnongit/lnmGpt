import yfinance as yf
import pandas as pd


class YahooFinanceTool:


    def __init__(self):
        pass

    def get_data(self, ticker,interval, period):
        # Download and return stock data
        datas = yf.download(ticker, period=period, interval=interval)["Close"]
        return datas # Return data as JSON

    def get_sma(self, ticker="BTC-USD", period="1y"):
        asset = yf.Ticker(ticker)
        history = asset.history(period=period)
        sma_50 = history["Close"].rolling(window=50).mean()
        sma_200 = history["Close"].rolling(window=200).mean()
        current_price = history["Close"].iloc[-1]
        
        trend_sma50 = "Bullish" if current_price > sma_50.iloc[-1]  else "Bearish"
        trend_sma200 = "Bullish" if current_price > sma_200.iloc[-1]  else "Bearish"

        output = f'''
Trend sma50: {trend_sma50}
Trend sma 200: {trend_sma200}
        \n
        '''
        return output

    def get_rsi_macd(self, ticker="BTC-USD", period="1y", interval="1d"):
        
        
        asset = yf.Ticker(ticker)
        data = asset.history(period=period, interval=interval)
        close_prices = data["Close"]


        # Calculate RSI
        delta = close_prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Calculate MACD
        ema_12 = close_prices.ewm(span=12, adjust=False).mean()
        ema_26 = close_prices.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line

        # Format output
        output = f"Results for {ticker} over period {period} with interval {interval}:\n\n"
        output += f"Latest RSI: {rsi.iloc[-1]:.2f}\n"
        output += f"Latest MACD: {macd_line.iloc[-1]:.2f}\n"
        output += f"Latest MACD Signal: {signal_line.iloc[-1]:.2f}\n"
        output += f"Latest MACD Histogram: {macd_hist.iloc[-1]:.2f}\n\n"
        output += "RSI Evolution:\n"
        output += f"{rsi.tail(10).to_string(header=False)}\n\n"
        output += "MACD Evolution:\n"  
        output += self.get_sma(ticker=ticker, period="1y") if period == "6mo" else "\n"
        output_df = pd.DataFrame({"MACD": macd_line, "Signal": signal_line, "Histogram": macd_hist}, index=macd_line.index)
        output += f"{output_df.tail(10).to_string(index=True)}"
        
        return output
