# LnmGpt

LnmGpt is an automated trading bot for the LNMarkets platform, utilizing AI-powered analysis for Bitcoin trading decisions.

It uses the power of Claude 3.5 Sonnet and GPT-4o to execute orders on the LNMarkets platform. 
Bitcoin data is retrieved from YahooFinance.
A mini memory system allows the bot to take into account past orders.



# Requirements

A lnmarkets accounts ([https://lnmarkets.com/](https://lnmarkets.com/)) and an API key

An Anthopic API key and/or an OpenAPIKey

## Installation

1. Clone the repository:


2. Create a virtual environment:

```
conda create -n lnmGpt 
conda activate lnmGpt
```

3. Install the required packages

> pip install -r requirements.txt


4. Set up environment variables:
Create a `.env` file in the project root and add the following:
Anthropic API is used by default but OpenAi can be used too
```
LNM_KEY=your_lnmarkets_key LNM_SECRET=your_lnmarkets_secret LNM_PASS=your_lnmarkets_passphrase ANTRHOPIC_API_KEY=your_anthropic_api_key OPENAI_API_KEY=your_openai_api_key
```



## Usage

1. To run the main script:

> python script-lnmAuto.py

This script checks Bitcoin price movements and executes the main trading logic when significant changes are detected.


2. To run the main trading script directly:

> python run.py

run.py check bitcoin price variation before running the main script.

User is prompted to confirm order proposition.

Use the `oai` argument to use OpenAI instead of Claude model:

```
python script-lnmAuto.py oai
python run.py oai
```

4. Use the `--auto-validate` option to automatically execute all recommended actions without prompting:

```
python script-lnmAuto.py --auto-valide
python run.py --auto-validate
```

5. You can combine options:

```
python script-lnmAuto.py oai --auto-valide
python run.py oai --auto-validate
```

## Configuration

- Adjust the `THRESHOLD_PERCENT` in `run.py` to change the price movement threshold that triggers the main script execution.
- Modify the `whitelist.txt` file to add order IDs that should not be touched by the script

## Note

Ensure you have sufficient balance and have set up your LNMarkets account correctly before running the automated trading system.





