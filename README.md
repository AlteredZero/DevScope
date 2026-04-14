# DevScope

DevScope is an ai powered coding assistant that understands entire project folders and helps debug, explain, and improve code.

## Features
- Project-wide code understanding
- Run using free models through OpenRouter (meaning it will always be free!)
- Multi-language support

## INSTRUCTRIONS
Prorgram will fail if an OpenRouter API key is missing. Go to https://openrouter.ai/ and create an API key, it is free. After that, 
create a file called 'config.py' and inside it add 'OPENROUTER_API_KEY = "[YOUR API KEY HERE]"', replace the 
[YOUR API KEY HERE] with your OpenRouter API key.

## Run
python main.py