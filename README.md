# Chatbot-Engine

## Requirements
- Python 3.10.2
- PyCharm
- Ngrok

## Installation
- Add python path to environment variable
- Configure interpreter in PyCharm
- Run `pip install rasa`
- Run `pip install rasa-sdk`

## Getting Started
- Open two terminals
- Run rasa server using `rasa run --enable-api --cors="*"` on one terminal
- Run rasa action server using `rasa run actions` on the other terminal

## Deployment Using Ngrok
- Open a third terminal and run `ngrok http 5005`
