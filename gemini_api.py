import os
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()
import json
from tokencost import calculate_prompt_cost, calculate_completion_cost
import re
import colorama
from colorama import Fore, Back, Style
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model_name="gemini-1.5-pro"

# Create the model
generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"Retrying in {retry_state.next_action.sleep} seconds...")
)

def get_response(text):
    full_response = ""
    continue_token = "<CONTINUE>"
  
    system_prompt = f'''You are an AI assistant that explains your reasoning step by step, incorporating dynamic Chain of Thought (CoT), reflection, and verbal reinforcement learning. Follow these instructions:

1. Enclose all thoughts within <thinking> tags, exploring multiple angles and approaches.
2. Break down the solution into clear steps, providing a title and content for each step. Use a maximum of 20 steps.
3. After each step, decide if you need another step or if you're ready to give the final answer.
4. Continuously adjust your reasoning based on intermediate results and reflections, adapting your strategy as you progress.
5. Regularly evaluate your progress, being critical and honest about your reasoning process.
6. Assign a quality score between 0.0 and 1.0 to guide your approach:
- 0.8+: Continue current approach
- 0.5-0.7: Consider minor adjustments
- Below 0.5: Seriously consider backtracking and trying a different approach
7. If unsure or if your score is low, backtrack and try a different approach, explaining your decision.
8. For mathematical problems, show all work explicitly using LaTeX for formal notation and provide detailed proofs.
9. Explore multiple solutions individually if possible, comparing approaches in your reflections.
10. Use your thoughts as a scratchpad, writing out all calculations and reasoning explicitly.
11. Use at least 3 methods to derive the answer and consider alternative viewpoints.
12. Be aware of your limitations as an AI and what you can and cannot do.

After every 3 steps, perform a detailed self-reflection on your reasoning so far, considering potential biases and alternative viewpoints.

If your response is incomplete, end it with the token "{continue_token}" to indicate there's more to follow.
'''
    model = genai.GenerativeModel(
      model_name=model_name,
      generation_config=generation_config,
      system_instruction=system_prompt,
    )

    history = []
    while True:
        try:
            chat_session = model.start_chat(
                  history=history
            )
            response = chat_session.send_message(text)

            assistant_response = response.text
            full_response += assistant_response

            history.append({
                "role": "model",
                "parts": [assistant_response]
            })

            if assistant_response.strip().endswith(continue_token):
                full_response = full_response.rsplit(continue_token, 1)[0]
                history.append({
                    "role": "user",
                    "parts": [f"{continue_token}"]
                })
          
            else:
                break
            wait=30
            print(f'Need to continue: sleep for {wait} seconds')
            time.sleep(wait)

        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            print(f"Encountered error: {e}")
            raise
    
    return full_response




def analyze_price_action_gemini(data_history_short, data_history, data_history_long, technical_data_short, technical_data, technical_data_long):
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
    print(f"{Fore.YELLOW}Analyse Price Action - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    technical_analysis = get_response(message)
    
    print(f"{Fore.GREEN}Analyse Price Action - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{technical_analysis}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model_name)
    completion_cost = calculate_completion_cost(technical_analysis, model_name)
    print(f"{Fore.CYAN}Coûts - Prompt : {Fore.LIGHTCYAN_EX}{prompt_cost}{Style.RESET_ALL}, Completion : {Fore.LIGHTCYAN_EX}{completion_cost}{Style.RESET_ALL}\n")
    
    
    return technical_analysis, prompt_cost, completion_cost

def analys_past_data_gemini(past_data_short,past_data_medium="", past_data_long=""):
    message = f'''
You are an AI cryptocurrency market analyst specializing in order analysis. Your task is to analyze previous orders executed by other AI Agents in the Bitcoin market across three different time horizons. You will be provided with past order data for short-term, medium-term, and long-term strategies, and you need to give a precise analysis of the successes and failures for each horizon.

Here is the past order data you will analyze:
<past_data_short>
{past_data_short}
</past_data_short>

<past_data_medium>
{past_data_medium}
</past_data_medium>

<past_data_long>
{past_data_long}
</past_data_long>

To complete this task, follow these steps:

1. Carefully review the past order data provided for each time horizon (short, medium, long), paying attention to all fields including timestamp, type, order_type, side, quantity, pl, margin, leverage, price, stoploss, takeprofit, and reason.
2. For each time horizon, identify patterns of successful and unsuccessful orders, considering both created and closed orders.
3. Analyze the factors that contributed to the success or failure of orders in each time horizon, including the reasoning provided in the "reason" field.
4. Compare and contrast the strategies, performance, and risk management approaches across the three time horizons.
5. Consider market conditions, timing, order size, leverage used, and the relationship between entry price, stoploss, and takeprofit levels for each horizon.
6. Evaluate the overall performance of the AI Agents based on their orders in each time horizon, considering both long (buy) and short (sell) positions.

In your analysis for each time horizon, make sure to:

- Provide specific examples from the data to support your observations, using order IDs when relevant.
- Highlight any recurring strategies or mistakes specific to each time horizon.
- Offer insights into what made certain orders successful and others unsuccessful within each timeframe.
- Consider the broader market context and how it affects strategies in different time horizons.
- Analyze the use of different order types (market vs limit) and their effectiveness in each horizon.
- Evaluate the risk management strategies employed, including the use of leverage and the setting of stoploss and takeprofit levels, and how they differ across time horizons.

Present your analysis in a clear, structured format. Begin with an overview of your findings, followed by detailed sections for each time horizon:

1. Short-term strategy analysis
2. Medium-term strategy analysis
3. Long-term strategy analysis

For each time horizon, include subsections on:
- Entry strategies
- Exit strategies
- Risk management
- Market timing
- Use of leverage
- Performance trends

Additionally, include a comparative analysis section:
- Compare and contrast the effectiveness of strategies across different time horizons
- Discuss how market conditions impact each time horizon differently
- Analyze the risk-reward balance for each time horizon

Conclude with:
- Overall patterns or trends you've identified across all time horizons
- Potential recommendations for improving the trading strategy for each time horizon
- Suggestions on how to balance and integrate strategies from different time horizons for a more robust overall approach

Your entire response MUST be enclosed within <past_data_analys></past_data_analys> tags. Do not include the opening and closing tags in your response; they will be added automatically.

Remember, your goal is to provide a precise and insightful analysis of the successes and failures in the past Bitcoin trading data across short, medium, and long-term strategies. Focus on delivering actionable insights that could be used to improve future trading strategies in the cryptocurrency market, taking into account the unique characteristics and challenges of each time horizon.

    '''
    print(f"{Fore.YELLOW}Analyse des données passées - Prompt :{Style.RESET_ALL}\n{Fore.LIGHTYELLOW_EX}{message}{Style.RESET_ALL}\n")
    past_data_analys = get_response(message)
    print(f"{Fore.GREEN}Analyse des données passées - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{past_data_analys}{Style.RESET_ALL}\n")
    
    prompt_cost = calculate_prompt_cost(message, model_name)
    completion_cost = calculate_completion_cost(past_data_analys, model_name)
    print(f"{Fore.CYAN}Coûts - Prompt : {prompt_cost}, Completion : {completion_cost}{Style.RESET_ALL}\n")
    return past_data_analys, prompt_cost, completion_cost


def analys_gemini(data, user_balance, whitelist, technical_data,past_data, active_positions, open_positions):
    prompt_template = read_template_from_file("./prompt_template.txt")
    
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
    data = get_response(message)
    print(f"{Fore.GREEN}Analyse finale - Réponse :{Style.RESET_ALL}\n{Fore.LIGHTGREEN_EX}{data}{Style.RESET_ALL}\n")
    prompt_cost = calculate_prompt_cost(message, model_name)
    completion_cost = calculate_completion_cost(data, model_name)
    return data, prompt_cost, completion_cost
