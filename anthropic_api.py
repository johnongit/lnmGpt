import anthropic
from dotenv import load_dotenv
import os
load_dotenv()
import json
from tokencost import calculate_prompt_cost, calculate_completion_cost
import re
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

model = "claude-3-5-sonnet-20240620"

api_key = os.getenv("ANTRHOPIC_API_KEY")

client = anthropic.Anthropic(
    api_key=api_key
)

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
    print(f"{Fore.YELLOW}Prompt envoyé :{Style.RESET_ALL}\n{text}\n")
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
    )
    print(f"{Fore.GREEN}Réponse reçue :{Style.RESET_ALL}\n{message.content[0].text}\n")
    return message


def analys_past_data(past_data):
    message = f'''
You are an AI cryptocurrency market analyst specializing in order analysis. Your task is to analyze previous orders executed by other AI Agents in the Bitcoin market. You will be provided with past order data, and you need to give a precise analysis of the successes and failures.

Here is the past order data you will analyze:
<past_order>
{past_data}
</past_order>

To complete this task, follow these steps:

    Carefully review the past order data provided, paying attention to all fields including timestamp, type, order_type, side, quantity, pl, margin, leverage, price, stoploss, takeprofit, and reason.
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
    print(f"{Fore.YELLOW}Analyse des données passées - Prompt :{Style.RESET_ALL}\n{message}\n")
    past_data_analys = get_response(message).content[0].text
    print(f"{Fore.GREEN}Analyse des données passées - Réponse :{Style.RESET_ALL}\n{past_data_analys}\n")
    
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(past_data_analys, model)
    print(f"{Fore.CYAN}Coûts - Prompt : {prompt_cost}, Completion : {completion_cost}{Style.RESET_ALL}\n")
    return past_data_analys, prompt_cost, completion_cost

def analysClaudeV4(data, user_balance, whitelist, technical_data,past_data, active_positions, open_positions, prompt_template):
    print("analysClaudeV4")
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
    
    print(f"{Fore.YELLOW}Analyse finale - Prompt :{Style.RESET_ALL}\n{message}\n")
    data = get_response(message).content[0].text
    print(f"{Fore.GREEN}Analyse finale - Réponse :{Style.RESET_ALL}\n{data}\n")
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(data, model)
    return data, prompt_cost, completion_cost


def analysClaudeV3(data, user_balance, whitelist, technical_data,past_data, active_positions, open_positions):

    message = f'''
    You are an AI trading system for the lnmarkets platform, composed of multiple expert agents collaborating to analyze market data and create trading recommendations. Your experts include:

    1. Technical Analyst
    2. Order Analyst
    3. Risk Manager
    4. Portfolio Manager

    Each expert will analyze the data from their perspective and contribute to the final recommendations. The Portfolio Manager will oversee the process and ensure a balanced approach to risk management across short, medium, and long-term orders.

    Input data:
    User usable balance
    <user_balance>
    {user_balance}
    </user_balance>

    Current Running (and filled) orders (that can be closed)
    <running_orders>
    {active_positions}
    </running_orders>

    Current opened and not running (currently waited to be filled) orders (that can be canceled)
    <open_orders>
    {open_positions}
    </open_orders>

    Orders of running and opened orders performed by agents (contains reason)
    <active_orders_list>
    {data}
    </active_orders_list>

    Orders not to be touched
    <whitelist>
    {whitelist}
    </whitelist>

    Technical analysis
    <technical_data>
    {technical_data}
    </technical_data>

    Previous actions analysis
    <past_data>
    {past_data}
    </past_data>

    Imagine that four Bitcoin market analysis experts are answering this question. Each expert represents a specific role:

    1- Technical Analyst:
        Analyze price trends, support/resistance levels, and technical indicators (RSI, MACD)
        Identify potential entry and exit points
        When defining take profit and stop loss, consider potential fakeouts, which can be significant for Bitcoin (1000-2000 dollars)
        Add reason, especially for resistance, take profit, stop loss, and target prices
        Analyze current market volatility

    2- Order Analyst:
        Review past order analysis data
        Review each running and open order, take into account reason and "time_horizon"
        For open orders, if "time_horizon" was not provided, check target price against resistance and support to determine time horizon
        Time horizon must be taken into account before suggesting cancellation
        Ensures that past successes and failures are taken into account
        Clearly distinguish between open orders and running orders
        When discussing orders, always specify whether they are open or running, and explain the implications for execution and risk management
        Check reason and time horizon before update, cancel and close
        Add term (short, middle, long)

    3- Risk Manager:
        Determine appropriate leverage (ranging from 2 to 10) and position sizes. This leverage range remains low risk profile
        For order creation and update, suggest stop-loss levels that account for potential Bitcoin fakeouts (1000-2000 dollars)
        Evaluate overall portfolio risk
        Balance risk across short, medium, and long-term positions
        Ensure compliance with risk-reward ratio (> 1.7)

    4- Portfolio Manager:
        Review existing orders and positions
        Suggest order modifications or closures based on current market conditions
        Ensure compliance with risk-reward ratio (> 1.7)
        Optimize the use of leverage (2 to 10) across different positions. This range remains low risk profile

    Process:

        Each expert will write a step of their thought process, then share it with the group.
        After each share, all experts will move on to the next step.
        If an expert realizes they are going down the wrong path at any point, they will withdraw from the process.
        The process will continue until all experts have completed their analysis or withdrawn.

    Final objective:
    Based on the collaborative analysis, provide recommendations for:

        Orders to close (for running orders)
        Orders to cancel (for open orders)
        New orders to create
        Existing orders to update
        Existing orders to cancel

    Begin with the first step of thinking for each expert, focusing on their specific area of expertise.

    Your recommendations should be provided in JSON format, with separate arrays for each action type. Use the following structure for your output:

    <order_to_close>
    [
    {{
        "id": "string",
        "entry_price": float,
        "margin": integer,
        "side": "string",
        "reason": "string"
    }},
    ...
    ]
    </order_to_close>

    <order_to_cancel>
    [
    {{
        "id": "string",
        "entry_price": float,
        "side": "string",
        "margin": integer,
        "reason": "string"
    }},
    ...
    ]
    </order_to_cancel>

    <order_to_create>
    [
    {{
        "type": "l" or "m",
        "side": "b" or "s",
        "margin": integer,
        "leverage": integer, (2 to 10)
        "takeprofit": integer (optional),
        "stoploss": integer (optional),
        "price": integer (required for type "l", use "N/A" for type "m"),
        "reason": "Explanation",
        "time_horizon": "short", "medium", or "long"
    }},
    ...
    ]
    </order_to_create>

    <order_to_update>
    [
    {{
        "id": "string",
        "type": "takeprofit" or "stoploss",
        "value": float,
        "side": "string",
        "margin": integer,
        "entry_price": float,
        "reason": "Explanation"
    }},
    ...
    ]
    </order_to_update>

    Follow these guidelines when creating your recommendations:

    1. Incorporate insights from all expert analyses. Insert all analyses between <expert></expert>
    2. Ensure a balanced risk profile across short, medium, and long-term positions.
    3. Consider the user's available balance and existing orders.
    4. For order creation:
    - Use 'm' for market orders (set price to "N/A") and 'l' for limit orders.
    - Use 'b' for buy orders and 's' for sell orders.
    - Provide only the margin, not the quantity.
    - Include a reason for each order.
    - Specify the time horizon for each order (short, medium, or long).
    - Set leverage between 2 and 10, optimizing based on risk and market conditions.
    5. For order updates:
    - Specify whether you're updating the takeprofit or stoploss.
    - Include a reason for each update.
    - If the value is a round number (i.e., has no decimal places), represent it as an integer without a decimal point. If it has decimal places, use a float.
    6. For order closure: reserved for running_orders order
    7. For order cancellation: reserved for open_orders
    8. Ensure that your recommendations do not include any orders from the <whitelist></whitelist>.
    9. Consider past order performance (success and failures) when making new recommendations.
    10. Maintain a risk-reward ratio of more than 1.7 for all positions.
    11. Place stop losses at a safe distance from support/resistance levels to avoid false triggers due to Bitcoin fakeouts (1000-2000 dollars), while still protecting the position.
    12. Balance the portfolio risk by adjusting position sizes and leverages (2 to 10) across different time horizons.

    Analyze the provided data using the tree of thought approach with multiple experts, and create your recommendations following the guidelines and format described above. Ensure that your output is properly formatted JSON within the specified XML tags.
'''
    print(f"{Fore.YELLOW}Analyse finale - Prompt :{Style.RESET_ALL}\n{message}\n")
    data = get_response(message).content[0].text
    print(f"{Fore.GREEN}Analyse finale - Réponse :{Style.RESET_ALL}\n{data}\n")
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(data, model)
    return data, prompt_cost, completion_cost


def customize_final_prompt(past_data):
    print("===================================")
    print("in customize_final_prompt")
    prompt_template = read_template_from_file("./prompt_template.txt")
    message = f'''
Based on the data inside <past_data>, adapt the template prompt inside <template>.
the new prompt MUST BE complete and very explicit. Never refers to the "original template"
The new prompt should remain in English and be placed inside <new_prompt_template>.

<past_data>
{past_data}
</past_data>

<template>
{prompt_template}
</template
'''
    print(f"{Fore.YELLOW}Personnalisation du prompt final - Prompt :{Style.RESET_ALL}\n{message}\n")
    data = get_response(message).content[0].text
    print(f"{Fore.GREEN}Nouveau prompt :{Style.RESET_ALL}\n{data}\n")
    
    prompt_cost = calculate_prompt_cost(message, model)

    completion_cost = calculate_completion_cost(data, model)
    print("===================================")
    return data, prompt_cost, completion_cost

def analyze_price_action(data_history_short, data_history, data_history_long, technical_data_short, technical_data, technical_data_long):
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
    
    technical_analysis = get_response(message).content[0].text
    
    technical_data = get_response(message).content[0].text
    prompt_cost = calculate_prompt_cost(message, model)
    completion_cost = calculate_completion_cost(technical_data, model)

    
    
    return technical_analysis, prompt_cost, completion_cost