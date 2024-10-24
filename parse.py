import re
import json
import time

def filter_order_history(orders, selected_types=["closed", "created"]):
    filtered_orders = []

    for order in orders:
        if order['type'] in selected_types:
            # Si 'data' est une chaîne JSON, on la parse
            if isinstance(order['data'], str):
                try:
                    order['data'] = json.loads(order['data'])
                except json.JSONDecodeError as e:
                    print(f"Erreur lors du décodage de data pour l'ordre: {order['id']}")
                    print(f"Erreur: {e}")
                    continue  # Passe à l'ordre suivant en cas d'erreur
            
            filtered_orders.append(order)

    return filtered_orders


def parse_past_data_analys(past_data_analys):
    # Extraire les sections pertinentes
    
    past_data_analys = re.findall(r'<past_data_analys>(.*?)</past_data_analys>', past_data_analys, re.DOTALL)
    

    return past_data_analys[0]


def parse_technical_analys(technical_data):
    # Extraire les sections pertinentes
    technical_data_parsed = re.findall(r'<technical_analysis>(.*?)</technical_analysis>', technical_data, re.DOTALL)


    return technical_data_parsed[0]

def parse_new_prompt_template(prompt_template):
    # Extraire les sections pertinentes
    new_prompt_template = re.findall(r'<new_prompt_template>(.*?)</new_prompt_template>', prompt_template, re.DOTALL)


    return new_prompt_template[0]

def parse_analysis_result(analysis_result):
    # Extraire les sections pertinentes
    order_to_close = re.findall(r'<order_to_close>(.*?)</order_to_close>', analysis_result, re.DOTALL)
    order_to_update = re.findall(r'<order_to_update>(.*?)</order_to_update>', analysis_result, re.DOTALL)
    order_to_create = re.findall(r'<order_to_create>(.*?)</order_to_create>', analysis_result, re.DOTALL)
    order_to_cancel = re.findall(r'<order_to_cancel>(.*?)</order_to_cancel>', analysis_result, re.DOTALL)
        

    # Fonction pour parser le JSON dans chaque section
    def parse_json(section):
        return json.loads(section[0]) if section else []

    # Parser les sections JSON
    close_orders = parse_json(order_to_close)
    update_orders = parse_json(order_to_update)
    create_orders = parse_json(order_to_create)
    cancel_orders = parse_json(order_to_cancel)

    return close_orders, update_orders, create_orders, cancel_orders

