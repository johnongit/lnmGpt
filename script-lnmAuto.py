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
from anthropic_api import analyze_price_action, analys_past_data, analysClaudeV4
from openai_api import analyze_price_action_oai, analys_past_data_oai, analysGptV2, analys_o1
from ollama_api import analys_past_data_ollama, analysOllamaV2, analyze_price_action_ollama
from gemini_api import analyze_price_action_gemini, analys_past_data_gemini, analys_gemini
from yahoo_finance_api import YahooFinanceTool
from history import update_history, find_not_closed_orders, read_order_history, find_closed_orders, update_pl_from_active_positions
from structured_logger import StructuredLogger
import pandas as pd

import logging
print("test")

# Add this near the top of the file
auto_validate = "--auto-validate" in sys.argv
use_oai = "oai" in sys.argv
use_o1 = "o1" in sys.argv
use_claude = "claude" in sys.argv
use_ollama = "ollama" in sys.argv
use_gemini = 'gemini' in sys.argv
print("test")
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
logger = StructuredLogger()


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

def log_info(message):
    logging.info(message)

def main():
    logger.log("execution_start", {"message": "Début de l'exécution de script-lnmAuto.py"})
    print("Utilisation de OpenAI" if use_oai else "Utilisation de Ollama" if use_ollama else "Utilisation de Claude" if use_claude else "Utilise de Gemini" if use_gemini else "Utilisation O1" )
    
    

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
        pd.set_option('display.max_rows', None)

        data_history_short = tickeryf.history(interval="1h", period="10d")
        data_history = tickeryf.history(interval="1d", period="1mo")
        data_history_long = tickeryf.history(interval="1d", period="6mo")

        technical_data_short = yahoofi.get_rsi_macd(interval="1h", period="10d")
        technical_data = yahoofi.get_rsi_macd(interval="1d", period="1mo")
        technical_data_long = yahoofi.get_rsi_macd(interval="1d", period="6mo")
        #print(data_history_long)

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
        print(formatted_output["active_positions"]["positions"])
        
        # Update history
        update_history(formatted_output=formatted_output, history_filename="order_history.txt")
        
        history = read_order_history()
        history = filter_order_history(history, selected_types=["closed", "created"])
        orders_not_closed = find_not_closed_orders(history)
        orders_not_closed = update_pl_from_active_positions(orders_not_closed, active_positions)
        orders_closed_short = find_closed_orders(history, "short")
        orders_closed_medium = find_closed_orders(history, "medium")
        orders_closed_long = find_closed_orders(history, "long")

        
        

        

       
        if use_o1:
            analysis_func = analys_o1
            analysis_result, p_cost, c_cost = analysis_func(
                user_balance=user_balance,
                history_data_short=data_history_short,
                history_data_medium=data_history,
                history_data_long=data_history_long,
                technical_data_short=technical_data_short,
                technical_data_medium=technical_data,
                technical_data_long=technical_data_long,
                active_positions=active_positions_ids,
                open_positions=open_positions_ids,
                past_data_short=orders_closed_short,
            )
            print(f'Coût du prompt : {p_cost}')
            print(f'Coût de complétion : {c_cost}')
            prompt_cost += p_cost
            completion_cost += c_cost
        else:
            analyze_price_action_func = analyze_price_action_oai if use_oai else analyze_price_action_ollama if use_ollama else analyze_price_action_gemini if use_gemini else analyze_price_action

            

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
            
            price_data = parse_technical_analys(price_data)
            
        
            # Analyze past data
            history_data, p_cost, c_cost = (
                analys_past_data_oai(orders_closed_short, orders_closed_medium, orders_closed_long, data_history_short,data_history,data_history_long  ) if use_oai
                else analys_past_data_ollama(orders_closed_short, orders_closed_medium, orders_closed_long )  if use_ollama
                else analys_past_data_gemini(orders_closed_short, orders_closed_medium, orders_closed_long ) if use_gemini
                else analys_past_data(orders_closed_short, orders_closed_medium, orders_closed_long, data_history_short,data_history,data_history_long ) 
            )
            prompt_cost += p_cost
            completion_cost += c_cost
            history_data = parse_past_data_analys(history_data)



            '''
            customize_prompt_func = (
                customize_final_prompt_gpt if use_oai
                else customize_final_prompt_ollama if use_ollama
                else customize_final_prompt
            )
            
            new_prompt_template, p_cost, c_cost = customize_prompt_func(
                past_data=history_data
            )
            new_prompt_template = parse_new_prompt_template(
                prompt_template=new_prompt_template
            )
            '''            

            # Perform analysis
            logger.log_prompt("final_analysis", {
                "data": orders_not_closed,
                "user_balance": user_balance,
                "whitelist": whitelist,
                "technical_data": price_data,
                "past_data": history_data,
                "active_positions": active_positions,
                "open_positions": open_positions_ids
            })
            analysis_func = analysGptV2 if use_oai else analysOllamaV2 if use_ollama else analys_gemini if use_gemini  else analysClaudeV4

            analysis_result, p_cost, c_cost = analysis_func(
                data=orders_not_closed,
                user_balance=user_balance,
                whitelist=whitelist,
                technical_data=price_data,
                past_data=history_data,
                active_positions=active_positions_ids,
                open_positions=open_positions_ids
            )
            print(f'Coût du prompt : {p_cost}')
            print(f'Coût de complétion : {c_cost}')
            '''
            logger.log_response("final_analysis", {
                "analysis_result": analysis_result,
                "prompt_cost": p_cost,
                "completion_cost": c_cost
            })
            '''
            prompt_cost += p_cost
            completion_cost += c_cost
        
        close_orders, update_orders, create_orders, cancel_orders = parse_analysis_result(analysis_result)

        print(f'Coût total du prompt : {prompt_cost}')
        print(f'Coût total de complétion : {completion_cost}')
        log_info(f"Coût total du prompt : {prompt_cost}")
        log_info(f"Coût total de complétion : {completion_cost}")
        user_interaction(close_orders, update_orders, create_orders, active_positions_ids, open_positions_ids, cancel_orders, auto_validate)

    except Exception as e:
        logger.log_error(e, {"traceback": traceback.format_exc()})
        error_message = f"Une erreur s'est produite pendant l'exécution: {str(e)}"
        print(error_message)
        log_info(error_message)
        traceback.print_exc()

    logger.log("execution_end", {"message": "Fin de l'exécution de script-lnmAuto.py"})

if __name__ == "__main__":
    main()
