from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
import json
import re
from tokencost import calculate_prompt_cost, calculate_completion_cost
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)
model='llama3-gradient'


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
    print(f"{Fore.YELLOW}Prompt envoyé :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{text}{Style.RESET_ALL}\n")
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
    print(f"{Fore.GREEN}Réponse reçue :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{response.choices[0].message.content}{Style.RESET_ALL}\n")
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
    print(f"{Fore.YELLOW}Analyse des données passées - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    past_data_analys = get_response(message).choices[0].message.content
    print(f"{Fore.GREEN}Analyse des données passées - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{past_data_analys}{Style.RESET_ALL}\n")
    prompt_cost = 0
    completion_cost = 0
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
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
    print(f"{Fore.YELLOW}Personnalisation du prompt final - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    data = get_response(message).choices[0].message.content
    print(f"{Fore.GREEN}Nouveau prompt :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{data}{Style.RESET_ALL}\n")
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
    
    print(f"{Fore.YELLOW}Analyse finale - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    data = get_response(message).choices[0].message.content
    print(f"{Fore.GREEN}Analyse finale - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{data}{Style.RESET_ALL}\n")
    prompt_cost = 0
    completion_cost = 0
    return data, prompt_cost, completion_cost


def analyze_price_action_ollama(data_history_short, data_history, data_history_long, technical_data_short, technical_data, technical_data_long):
    message = f'''
    You are a professional stock market analyst specializing in bitcoin and price action analysis. Your task is to thoroughly analyze bitcoin price data, as well as the RSI and MACD technical indicators, to provide a detailed analysis for short, medium, and long term.

Input data for your analysis:

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

For each time horizon (short, medium, and long term), analyze and provide the following information:

    Key resistance and support levels
    Current trend and trend strength
    Market configuration (range, bullish trend, bearish trend, etc.)
    Significant Japanese candlestick patterns
    Potential divergences between price and technical indicators (RSI, MACD)
    Volumes and their interpretation, including identification of low volume cycles
    Market momentum
    Relevant Fibonacci levels
    Anticipation of potential future movements

Analysis procedure for each time horizon:

    Carefully examine historical and technical data.
    Identify key support and resistance levels by observing important turning points.
    Determine the current trend and its strength by analyzing price direction and technical indicators.
    Assess the market configuration considering the trend and recent price movements.
    Spot significant Japanese candlestick patterns and their implications.
    Look for divergences between price and technical indicators.
    Analyze volumes and their impact on price movements, paying special attention to identifying low volume cycles and their significance.
    Evaluate market momentum using indicators and price movements.
    Identify relevant Fibonacci levels for retracements and extensions.
    Formulate anticipations of potential future movements based on the overall analysis.

Present your complete technical analysis between the tags <technical_analysis> and </technical_analysis>. Structure your analysis into three distinct sections: short term, medium term, and long term. For each section, provide the requested information in a clear, concise, and reasoned manner.

Conclude your analysis with an overall summary and strategic recommendations for traders and investors.

Added directive to reduce hallucinations:
To reduce hallucinations, do not invent or provide any metrics or specific numerical values if you are not certain you can determine them with certainty based on the given data. If you are unsure about a specific metric or value, state that it cannot be determined with the available information.
    '''
    
    technical_analysis = get_response(message).choices[0].message.content
    
    prompt_cost = 0
    completion_cost = 0
    
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    return technical_analysis, prompt_cost, completion_cost
