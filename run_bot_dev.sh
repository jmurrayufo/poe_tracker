
# .creds file should look like this 
# export CLIENT_TOKEN="LOTS OF NUMBERS THAT MAKE A TOKEN GO HERE"

source ~/.ssh/poebot-dev.creds
pipenv install --dev
pipenv run python3.7 -m poe_tracker --env dev "$@"
