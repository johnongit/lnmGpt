import os
import sys
import json
import time
import traceback
from dotenv import load_dotenv
import yfinance as yf
from lnmarkets import rest

from parse import parse_analysis_result, filter_order_history, parse_technical_analys, parse_past_data_analys, parse_new_prompt_template
from user_interacte import user_interaction
from anthropic_api import analyze_price_action, analys_past_data, analysClaudeV3, analysClaudeV4, customize_final_prompt
from openai_api import analyze_price_action_oai, analys_past_data_aoi, analysGpt, analysGptV2, customize_final_prompt_gpt
from ollama_api import analys_past_data_ollama, analysOllamaV2, analyze_price_action_ollama, customize_final_prompt_ollama
from yahoo_finance_api import YahooFinanceTool
from history import update_history, find_not_closed_orders, read_order_history, find_closed_orders

# Add this near the top of the file
auto_validate = "--auto-validate" in sys.argv
use_oai = "oai" in sys.argv
use_ollama = "ollama" in sys.argv

# Load environment variables
load_dotenv()

# LNMarkets configuration
LNM_KEY = os.getenv("LNM_KEY")
LNM_SECRET = os.getenv("LNM_SECRET")
LNM_PASSPHRASE = os.getenv("LNM_PASS")

LNM_OPTIONS = {
    'key': LNM_KEY,
    'secret': LNM_SECRET,
    'passphrase': LNM_PASSPHRASE
}

# Initialize clients
lnm = rest.LNMarketsRest(**LNM_OPTIONS)
yahoofi = YahooFinanceTool()

def read_whitelist(filename='whitelist.txt'):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def format_position(position):
    return {
        "id": position.get('id', 'N/A'),
        "type": "Market" if position.get('type') == 'm' else "Limit",
        "side": "Buy" if position.get('side') == 'b' else "Sell",
        "quantity": position.get('quantity', 'N/A'),
        "entry_price": position.get('price', 'N/A'),
        "leverage": position.get('leverage', 'N/A'),
        "profit_loss": position.get('pl', 'N/A'),
        "liquidation_price": position.get('liquidation', 'N/A')
    }

def main():
    # Check if OpenAI should be used
    
    print("Using OpenAI" if use_oai else "Using Ollama" if use_ollama else "Using Claude")

    try:
        # Test connection
        completion_cost = 0
        prompt_cost = 0
        ticker = lnm.futures_get_ticker()
        print("Connection successful!")
        print("Ticker data:", ticker)

        # Fetch user balance and market data
        user_balance = json.loads(lnm.get_user())['balance']
        print(f'Balance: {user_balance}')

        tickeryf = yf.Ticker("BTC-USD")
        data_history_short = tickeryf.history(interval="1h", period="10d")
        data_history = tickeryf.history(interval="1d", period="1mo")
        data_history_long = tickeryf.history(interval="1d", period="6mo")

        technical_data_short = yahoofi.get_rsi_macd(interval="1h", period="10d")
        technical_data = yahoofi.get_rsi_macd(interval="1d", period="1mo")
        technical_data_long = yahoofi.get_rsi_macd(interval="1d", period="6mo")

        # Fetch positions
        active_positions_raw = lnm.futures_get_trades({'type': 'running'})
        closed_positions_raw = lnm.futures_get_trades({'type': 'closed', 'limit': 1000})
        open_positions_raw = lnm.futures_get_trades({'type': 'open'})

        whitelist = read_whitelist()
        history = read_order_history()

        active_positions = json.loads(active_positions_raw)
        active_positions = [position for position in active_positions if position['id'] not in whitelist]
        
        closed_positions = json.loads(closed_positions_raw)
        open_positions = json.loads(open_positions_raw)
        open_positions = [position for position in open_positions if position['id'] not in whitelist]

        # Format positions
        formatted_output = {
            "active_positions": {"total": len(active_positions), "positions": []},
            "closed_positions": {"total": len(closed_positions), "positions": []},
            "open_positions": {"total": len(open_positions), "positions": []}
        }

        for key in formatted_output:
            formatted_output[key]["positions"] = [format_position(p) for p in locals()[key]]

        active_positions_ids = "\n".join([p['id'] for p in formatted_output["active_positions"]["positions"]])
        open_positions_ids = "\n".join([p['id'] for p in formatted_output["open_positions"]["positions"]])

        # Update history
        update_history(formatted_output=formatted_output, history_filename="order_history.txt")
        
        history = read_order_history()
        history = filter_order_history(history, selected_types=["closed", "created"])
        orders_not_closed = find_not_closed_orders(history)
        orders_closed = find_closed_orders(history)

        # Analyze price action
        analyze_price_action_func = analyze_price_action_oai if use_oai else analyze_price_action_ollama if use_ollama else analyze_price_action

        price_data, p_cost, c_cost = analyze_price_action_func(
            data_history_short=data_history_short,
            data_history=data_history,
            data_history_long=data_history_long,
            technical_data_short=technical_data_short,
            technical_data=technical_data,
            technical_data_long=technical_data_long
        )
        prompt_cost += p_cost
        completion_cost += c_cost
        print(price_data)
        price_data = parse_technical_analys(price_data)
        
        # Analyze past data
        history_data, p_cost, c_cost= analys_past_data_aoi(orders_closed) if use_oai else analys_past_data_ollama(orders_closed) if use_ollama else analys_past_data(orders_closed)
        prompt_cost += p_cost
        completion_cost += c_cost
        history_data = parse_past_data_analys(history_data)

        # Customize prompt
        customize_prompt_func = customize_final_prompt_gpt if use_oai else customize_final_prompt_ollama if use_ollama else customize_final_prompt
        
        new_prompt_template, p_cost, c_cost = customize_prompt_func(
            past_data=history_data
        )
        new_prompt_template = parse_new_prompt_template(
            prompt_template=new_prompt_template
        )
        

        # Perform analysis
        analysis_func = analysGptV2 if use_oai else analysOllamaV2 if use_ollama else analysClaudeV4

        analysis_result, p_cost, c_cost = analysis_func(
            data=orders_not_closed,
            user_balance=user_balance,
            whitelist=whitelist,
            technical_data=price_data,
            past_data=history_data,
            active_positions=active_positions_ids,
            open_positions=open_positions_ids,
            prompt_template=new_prompt_template
        )
        
        prompt_cost += p_cost
        completion_cost += c_cost
        close_orders, update_orders, create_orders, cancel_orders = parse_analysis_result(analysis_result)
        print(f'Total prompt cost: {prompt_cost}')
        print(f'Total completion cost: {completion_cost}')
        user_interaction(close_orders, update_orders, create_orders, active_positions_ids, open_positions_ids, cancel_orders, auto_validate)

    except Exception as e:
        print("Error occurred during execution:", str(e))
        traceback.print_exc()

if __name__ == "__main__":
    main()