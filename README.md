A telegram bot to scrape kleinanzeigen.de and send messages upon the discovery of new entries written in python.

# Setup

## API key

To use this bot you need to create a telegram bot and get the API token. Find out how to do this here: https://core.telegram.org/bots#how-do-i-create-a-bot

Save this token in a new file in the root directory of this repo called `token.txt`

## run using Docker

To run the application in a docker container, build and run the image using the `Dockerfile`:

```
cd [install directory]
docker build -t python-kleinanzeigen .
docker run -d python-kleinanzeigen
```

## run using pyton virtual environment

Create a python virtual environment, install required packages and run the project

```
cd [install directory]
py -m venv .
pip install -r requirements.txt
python source/telegram_bot.py
```

## Controlling the Bot

The Bot offers the following commands:

- `/start` -- Show all availabel commands
- `/add_bot` <name> <link> -- add a bot that scans the specified link
- `/start_bots`  -- start fetching with registered bots
- `/stop` -- stop fetching
- `/remove_bot` <name> -- stop and remove a bot
- `/clear_bots` -- stop and clear all registered bots
- `/status` -- get status information
- `/add_filter` -- add a filter to filter out unwanted messages
- `/show_filters` -- show active filters
- `/clear_filters` -- clear all filters
