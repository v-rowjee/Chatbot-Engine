# Chatbot-Engine

## Requirements
- Python 3.10.2
- PyCharm
- Ngrok

## Installation
- Add python path to environment variable
- Configure interpreter in PyCharm
- Run `pip install rasa==3.5.6`
- Run `pip install rasa-sdk==3.5.1`

## Getting Started
- Open two terminals
- Run rasa server using `rasa run --enable-api --cors="*"` on one terminal
- Run rasa action server using `rasa run actions` on the other terminal

## Deploy Using Ngrok
- Open a third terminal and run `ngrok http --domain=9c13e46fcc38-15980982744599944965.ngrok-free.app 5005`
