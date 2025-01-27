
# Lexiclash Readme
This is the source code to the game [Lexiclash](https://lexiclash.longislandtedium.com) found on [lexiclash.longislandtedium.com](https://lexiclash.longislandtedium.com)
Please feel free to push edits and make forks, but do be mindful of licensing if you wish to use the code for your own project.
## The Game
The rules are similar to any other crossword board game you've played. Use your tiles to play words off of other words already on the board. Aim for special spaces to multiply the score of a tile or your entire word. You can be creative with your tile placement in this game. The engine allows you to play multiple lines at once to chase that perfect combo.

## Requirements
- Python 3
- Django
- Django Extensions
- SQLite3
- Patience

## How to get going
You should be able to simply extract the project to a directory, then use [manage.py](manage.py) to migrate, and then run the server. Ideally you would use this in conjunction with Gunicorn and Nginx, but you can use Django's built in runserver (or runsslserver if you uncomment the blocks in [settings.py](lexiclash/settings.py)) to run the game.

## Issues
The code is currently not the most well documented. Some functionality is not described correctly or clearly. There are some very sloppy portions of code that seem to work fine at a small scale but will likely cause issues at greater scales. There are also several stubs from planned functionality that may or may not be added in the future.

Overall, things work, but they don't necessarily work well. Large delays are quite common when playing across networks, and even LAN play can be disrupted by delays lasting a few seconds.
