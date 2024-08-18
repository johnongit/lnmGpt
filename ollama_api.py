from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
import json
import re
from tokencost import calculate_prompt_cost, calculate_completion_cost





client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)
model='llama3:70b-instruct-q2_K'


def read_template_from_file(file_path):
    """Lit le contenu du fichier template."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()
    
def safe_format(template, **kwargs):
    def replace(match):
        key = match.group(1)
        return str(kwargs.get(key, match.group(0)))
    
    pattern = r'\{([^}]*)\}'
    return re.sub(pattern, replace, template)


def get_response(text):
    response = client.chat.completions.create(
    model=model,
    messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": text
        }
      ]
    }],
    temperature=0,
    max_tokens=10000,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    response_format={
        "type": "text"
    }
    )
    return response



def analys_past_data_ollama(past_data):
    message=f'''
You are an AI cryptocurrency market analyst specializing in order analysis. Your task is to analyze previous orders executed by other AI Agents in the Bitcoin market. You will be provided with past order data, and you need to give a precise analysis of the successes and failures.

Here is the past order data you will analyze:
<past_order>
{past_data}
</past_order>

To complete this task, follow these steps:

    Carefully review the past order data provided, paying attention to all fields including timestamp, type, order_type, side, pl, quantity, margin, leverage, price, stoploss, takeprofit, and reason.
    Identify patterns of successful and unsuccessful orders, considering both created and closed orders.
    Analyze the factors that contributed to the success or failure of each order, including the reasoning provided in the "reason" field.
    Consider market conditions, timing, order size, leverage used, and the relationship between entry price, stoploss, and takeprofit levels.
    Evaluate the overall performance of the AI Agents based on their orders, considering both long (buy) and short (sell) positions.

In your analysis, make sure to:

    Provide specific examples from the data to support your observations, using order IDs when relevant.
    Highlight any recurring strategies or mistakes, such as repeated entries at certain price levels or common reasons for closing positions.
    Offer insights into what made certain orders successful and others unsuccessful, considering the balance between risk (stoploss) and reward (takeprofit).
    Consider the broader market context if apparent from the data, including any trends in Bitcoin price movement that can be inferred from the orders.
    Analyze the use of different order types (market vs limit) and their effectiveness.
    Evaluate the risk management strategies employed, including the use of leverage and the setting of stoploss and takeprofit levels.

Present your analysis in a clear, structured format. Begin with an overview of your findings, followed by detailed observations on successes and failures. Include sections on:

    Entry strategies
    Exit strategies
    Risk management
    Market timing
    Use of leverage
    Overall performance trends

Conclude with any overall patterns or trends you've identified and potential recommendations for improving the trading strategy.

Your entire response should be enclosed within <past_data_analys> tags. Do not include the opening and closing tags in your response; they will be added automatically.

Remember, your goal is to provide a precise and insightful analysis of the successes and failures in the past Bitcoin trading data. Focus on delivering actionable insights that could be used to improve future trading strategies in the cryptocurrency market.

    '''
    past_data_analys = get_response(message).choices[0].message.content
    prompt_cost = 0
    completion_cost = 0
    print(prompt_cost, completion_cost)
    return past_data_analys, prompt_cost, completion_cost


def customize_final_prompt_ollama(past_data):
    prompt_template = read_template_from_file("./prompt_template.txt")
    message = f'''
Based on the data inside <past_data>, adapt the template prompt inside <template>. 
The new prompt should remain in English and be placed inside <new_prompt_template>.

<past_data>
{past_data}
</past_data>

<template>
{prompt_template}
</template
'''
    data = get_response(message).choices[0].message.content
    print(data)
    prompt_cost = 0
    completion_cost = 0
    return data, prompt_cost, completion_cost


def analysOllamaV2(data, user_balance, whitelist, technical_data,past_data, active_positions, open_positions, prompt_template):
    prompt_template = str(prompt_template)
    variables = {
        'data': data,
        'user_balance': user_balance,
        'whitelist': whitelist,
        'technical_data': technical_data,
        'past_data': past_data,
        'active_positions': active_positions,
        'open_positions': open_positions
    }
    message = safe_format(prompt_template, **variables)
    
    print(f'''prompt analyse finale: \n {message}''')
    print("==============================")
    data = get_response(message).choices[0].message.content
    print(f'''Analyse finale: {data}''' )
    prompt_cost = 0
    completion_cost = 0
    return data, prompt_cost, completion_cost


def analyze_price_action_ollama(data_history_short, data_history, data_history_long, technical_data_short, technical_data, technical_data_long):
    message = f'''
    Tu es un analyste boursier professionnel spécialisé dans le bitcoin et l'analyse de price action. Ta tâche est d'analyser en profondeur les données de prix du bitcoin, ainsi que les indicateurs techniques RSI et MACD, pour fournir une analyse détaillée à court, moyen et long terme.

Données d'entrée pour ton analyse :

<history_price_short>
{data_history_short}
</history_price_short>

<history_price>
{data_history}
</history_price>

<history_price_long>
{data_history_long}
</history_price_long>

<technical_price_short>
{technical_data_short}
</technical_price_short>

<technical_price>
{technical_data}
</technical_price>

<technical_data_long>
{technical_data_long}
</technical_data_long>

Pour chaque horizon temporel (court, moyen et long terme), analyse et fournis les informations suivantes :

1. Niveaux de résistance et de support clés
2. Tendance actuelle et force de la tendance
3. Configuration du marché (range, tendance haussière, tendance baissière, etc.)
4. Modèles de chandeliers japonais significatifs
5. Divergences potentielles entre le prix et les indicateurs techniques (RSI, MACD)
6. Volumes et leur interprétation
7. Momentum du marché
8. Niveaux de Fibonacci pertinents
9. Anticipation des mouvements futurs potentiels

Procédure d'analyse pour chaque horizon temporel :

1. Examine attentivement les données historiques et techniques.
2. Identifie les niveaux de support et de résistance clés en observant les points de retournement importants.
3. Détermine la tendance actuelle et sa force en analysant la direction des prix et les indicateurs techniques.
4. Évalue la configuration du marché en considérant la tendance et les mouvements de prix récents.
5. Repère les modèles de chandeliers japonais significatifs et leur implication.
6. Cherche des divergences entre le prix et les indicateurs techniques.
7. Analyse les volumes et leur impact sur les mouvements de prix.
8. Évalue le momentum du marché à l'aide des indicateurs et des mouvements de prix.
9. Identifie les niveaux de Fibonacci pertinents pour les retracements et les extensions.
10. Formule des anticipations sur les mouvements futurs potentiels basées sur l'ensemble de l'analyse.

Présente ton analyse technique complète entre les balises <technical_analysis> et </technical_analysis>. Structure ton analyse en trois sections distinctes : court terme, moyen terme et long terme. Pour chaque section, fournis les informations demandées de manière claire, concise et argumentée.

Conclus ton analyse par une synthèse globale et des recommandations stratégiques pour les traders et investisseurs.
    '''
    
    technical_analysis = get_response(message).choices[0].message.content
    
    prompt_cost = 0
    completion_cost = 0
    
    print(prompt_cost, completion_cost)
    return technical_analysis, prompt_cost, completion_cost