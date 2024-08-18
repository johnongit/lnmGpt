import json
from lnmarkets import rest
from history import read_order_history, update_history
import os
from dotenv import load_dotenv
load_dotenv()

lnm_key = os.getenv("LNM_KEY")
lnm_secret = os.getenv("LNM_SECRET")
lnm_passphrase = os.getenv("LNM_PASS")

# Configurez vos informations d'authentification
options = {
    'key': lnm_key,
    'secret': lnm_secret,
    'passphrase': lnm_passphrase
}
lnm = rest.LNMarketsRest(**options)

def calculate_performance(buy_price, sell_price):
    return (sell_price - buy_price) / buy_price * 100

def process_trade_data(info, data):
    if isinstance(data, str):
        data = json.loads(data)
    
    if data['type'] == 'm' and data['closed']:
        buy_price = data['price']
        sell_price = data['exit_price']
        performance = calculate_performance(buy_price, sell_price)
        
        print(f"Trade fermé:")
        print(f"Prix d'achat: {buy_price}")
        print(f"Prix de vente: {sell_price}")
        print(f"Performance: {performance:.2f}%")
        print(f"Profit/Perte: {data['pl']}")
        
        return performance, float(data['pl'])
    
    elif data['type'] == 'm' and data['running']:
        buy_price = data['price']
        current_price = data['price']  # Nous n'avons pas le prix actuel, donc nous utilisons le prix d'achat
        performance = calculate_performance(buy_price, current_price)
        
        print(f"Trade en cours:")
        print(f"Prix d'achat: {buy_price}")
        print(f"Prix actuel: {current_price}")
        print(f"Performance actuelle: {performance:.2f}%")
        print(f"Profit/Perte actuel: {data['pl']}")
        
        return performance, float(data['pl'])
    
    else:
        print("Type de trade non reconnu ou trade non en cours.")
        return 0, 0

closed_positions_raw = lnm.futures_get_trades({'type': 'closed'})
closed_positions = json.loads(closed_positions_raw)  
    # Formatage des données pour un LLM
formatted_output = {

    "closed_positions": {
        "total": len(closed_positions),
        "positions": []
    }
}
history = read_order_history()
update_history(formatted_output=formatted_output,history_filename="order_history.txt")
# Initialiser les variables pour le calcul total
total_performance = 0
total_pl = 0
trade_count = 0

# Charger les données depuis le fichier
with open('order_history.txt', 'r') as file:
    for line in file:
        trade_info = json.loads(line)
        print(f"\nTrade (timestamp: {trade_info['data']['id']} {trade_info['timestamp']}):")
        perf, pl = process_trade_data(trade_info, trade_info['data'])
        
        total_performance += perf
        total_pl += pl
        trade_count += 1

# Calculer et afficher la performance totale
if trade_count > 0:
    average_performance = total_performance / trade_count
    print(f"\nRésumé total:")
    print(f"Nombre total de trades: {trade_count}")
    print(f"Performance moyenne: {average_performance:.2f}%")
    print(f"Profit/Perte total: {total_pl:.2f}")
else:
    print("\nAucun trade n'a été traité.")