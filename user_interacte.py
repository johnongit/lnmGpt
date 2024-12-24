from datetime import datetime, timedelta
import json
from lnmarkets import rest
from history import save_order_history
from parse import parse_analysis_result
from dotenv import load_dotenv
import os
# Configurez vos informations d'authentification

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

lnm = rest.LNMarketsRest(**LNM_OPTIONS)


def user_interaction(close_orders, update_orders, create_orders, active_positions, open_positions, cancel_orders, auto_validate=False, next_trigger=None):
    print("\nRecommandations d'actions :")

    # Fermeture d'ordres
    if cancel_orders:
        print("\nOrdres à annuler :")
        for order in cancel_orders:
            print(order)
            position = order
            if position:
                print(f"ID: {order['id']}")
                print(f"Raison: {order['reason']}")
                print(f"Marge: {order['margin']}")
                print(f"Sens: {order['side']}")
                print(f"Prix d'achat: {order['entry_price']}")
                if auto_validate or input("Voulez-vous annuler cet ordre ? [o/n]: ").lower() == 'o':
                    result = cancel_order(order_id=order['id'],reason=order['reason'])
                    print(result)
                    if 'id' not in result:
                        result = close_order(order_id=order['id'],reason=order['reason'])
                        if result:
                            save_order_history("closed", result)
                            print(f"Ordre {order['id']} fermé et sauvegardé dans l'historique.")
                    elif result:
                        save_order_history("closed", result)
                        print(f"Ordre {order['id']} annulé et sauvegardé dans l'historique.")
                    else:
                        print(f"Erreur lors de la fermeture de l'ordre {order['id']}.")
            else:
                print(f"Erreur : Position {order['id']} non trouvée dans les positions actives.")

    # Fermeture d'ordres
    if close_orders:
        print("\nOrdres à fermer :")
        for order in close_orders:
            print(order)
            position = order
            if position:
                print(f"ID: {order['id']}")
                print(f"Raison: {order['reason']}")
                print(f"Marge: {order['margin']}")
                print(f"Sens: {order['side']}")
                print(f"Prix d'achat: {order['entry_price']}")
                if auto_validate or input("Voulez-vous fermer cet ordre ? [o/n]: ").lower() == 'o':
                    result = close_order(order_id=order['id'],reason=order['reason'])
                    print(f'debug close order: {result}')
                    if 'id' not in result:
                        result = cancel_order(order_id=order['id'],reason=order['reason'])
                        if result:
                            save_order_history("closed", result)
                            print(f"Ordre {order['id']} annulé et sauvegardé dans l'historique.")
                    elif result:
                        save_order_history("closed", result)
                        print(f"Ordre {order['id']} fermé et sauvegardé dans l'historique.")
                    else:
                        print(f"Erreur lors de la fermeture de l'ordre {order['id']}.")
            else:
                print(f"Erreur : Position {order['id']} non trouvée dans les positions actives.")
    # Création de nouveaux ordres
    if create_orders:
        print("\nNouveaux ordres à créer :")
        for order in create_orders:
            print(order)
            if(order['type'] == 'm') :
                order['price'] = "N/A"
            print(f"Type: {order['type']}")
            print(f"Side: {order['side']}")
            print(f"Marge: {order['margin']}")
            print(f"Levier: {order['leverage']}")
            print(f"Prix: {order['price']}")
            print(f"Take Profit: {order['takeprofit']}")
            print(f"Time Horizon': {order['time_horizon']}")
            print(f"Stop Loss: {order['stoploss']}")
            print(f"Raison: {order['reason']}")
            if auto_validate or input("Voulez-vous créer cet ordre ? [o/n]: ").lower() == 'o':
                result = create_order(
                    type=order['type'],
                    side=order['side'],
                    margin=order['margin'],
                    leverage=order['leverage'],
                    price=order['price'],
                    takeprofit=order['takeprofit'],
                    stoploss=order['stoploss'],
                    reason=order['reason'],
                    time_horizon=order['time_horizon']
                )
                if result:
                    print("Nouvel ordre créé et sauvegardé dans l'historique.")
                else:
                    print("Erreur lors de la création du nouvel ordre.")


    # Mise à jour d'ordres
    if update_orders:
        print("\nOrdres à mettre à jour :")
        for order in update_orders:
            print(f"ID: {order['id']}")
            print(f"Type de mise à jour: {order['type']}")
            print(f"Sens: {order['side']}")
            print(f"Nouvelle valeur: {order['value']}")
            print(f"Prix d'achat: {order['entry_price']}")
            print(f"Raison: {order['reason']}")
            if auto_validate or input("Voulez-vous mettre à jour cet ordre ? [o/n]: ").lower() == 'o':
                result = update_order(order_id=order['id'], order_type=order['type'], value=order['value'],reason=order['reason'])
                if result:
                    print(f"Ordre {order['id']} mis à jour et sauvegardé dans l'historique.")
                else:
                    print(f"Erreur lors de la mise à jour de l'ordre {order['id']}.")

    # Add next trigger display at the end
    if next_trigger:
        print("\n===============================")
        print("\nRecommandation pour la prochaine exécution:")
        print(f"Type de déclenchement: {next_trigger['type']}")
        
        if "date" in next_trigger:
            next_date = datetime.strptime(next_trigger['date'], '%Y-%m-%d %H:%M:%S')
            current_date = datetime.now()
            min_next_date = current_date + timedelta(days=1)
            
            if next_date < min_next_date:
                next_date = min_next_date
                print(f"Date ajustée pour respecter l'intervalle minimum de 24h: {next_date.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"Date: {next_trigger['date']}")
                
        if "price_target" in next_trigger:
            print(f"Cible de prix: {next_trigger['price_target']['price']} ({next_trigger['price_target']['direction']})")
            print(f"Raison du prix cible: {next_trigger['price_target']['reason']}")
            
        print(f"Raison générale: {next_trigger['reason']}")

# Fonctions pour interagir avec l'API LN Markets
def close_order(order_id, reason):
    print(order_id, reason)
    try:
        result = lnm.futures_close({'id': order_id})
        result = json.loads(result)
        if result:  # Vérifiez si l'opération a réussi
            # Ajout de la raison au résultat avant de le sauvegarder
            result['reason'] = reason
        else:
            print(f'Can\'t close order, lnmarkets returns {result}')
    except ValueError as e:
        print(f'error: {e}')
    return result

def cancel_order(order_id, reason):
    print(order_id, reason)
    try:
        result = lnm.futures_cancel({'id': order_id})
        result = json.loads(result)
        if result:  # Vérifiez si l'opération a réussi
            # Ajout de la raison au résultat avant de le sauvegarder
            result['reason'] = reason
        else:
            print(f'Can\'t cancel order, lnmarkets returns {result}')
    except ValueError as e:
        print(f'error: {e}')
    return result

def update_order(order_id, order_type, value, reason):
    update_data = {
        'id': order_id,
        'type': order_type,
        'value': value
    }
    print(update_data)
    result = lnm.futures_update_trade(update_data)
    result = json.loads(result)
    if 'id' in result: # Vérifiez si l'opération a réussi
        # Ajout de la raison au résultat avant de le sauvegarder
        result['reason'] = reason
        save_order_history("updated", result)
    else: 
        print(f'Can\'t update order, lnmarkets returns {result}')
    return result

def create_order(type,side,margin,leverage,takeprofit,stoploss,price,reason,time_horizon):
    
    if(type == 'l'):
        print("create limit")
        order_data = {
            'type': type,
            'side': side,
            'margin': margin,
            'leverage': leverage,
            'takeprofit': takeprofit,
            'stoploss': stoploss,
            'price': price
        }
    else:
        print("create market")
        order_data = {
            'type': type,
            'side': side,
            'margin': margin,
            'leverage': leverage,
            'takeprofit': takeprofit,
            'stoploss': stoploss,
        }
    result = lnm.futures_new_trade(order_data)
    result = json.loads(result)
    if 'id' in result:  # Vérifiez si l'opération a réussi
        # Ajout de la raison au résultat avant de le sauvegarder
        result['reason'] = reason
        result['time_horizon'] = time_horizon
        save_order_history("created", result)
    else: 
        print(f'Can\'t create order, lnmarkets returns {result}')
    return result
#create_order('l', 'b', 50000, 2, 66000, 72000, 63000, "Profiter d'une potentielle correction à court terme pour entrer dans la tendance haussière à long terme")
#create_order('m','b',3000,1.5,72000,64000,price=5000,reason="lalala")

#user_interaction(close_orders=order,update_orders=[], create_orders=order, active_positions=[])

data = '''<order_to_cancel>
[
  {
    "id": "770b221f-ba7b-4a93-8ce0-9708c7f54275",
    "entry_price": 61000,
    "reason": "Ordre de vente limite trop proche du prix actuel, risque de rebond technique"
  },
  {
    "id": "1f1600dc-4d06-4af2-bc26-9834ae81975f",
    "entry_price": 61500,
    "reason": "Ordre de vente limite trop proche du prix actuel, risque de rebond technique"
  }
]
</order_to_cancel>
'''
#close_orders, update_orders, create_orders, cancel_orders = parse_analysis_result(data)
#user_interaction(close_orders=close_orders,update_orders=update_orders,create_orders=[],active_positions=[],cancel_orders=cancel_orders,open_positions=[])
