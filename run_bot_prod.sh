

# .creds file should look like this 
# export CLIENT_TOKEN="LOTS OF NUMBERS THAT MAKE A TOKEN GO HERE"

git pull
source ~/.ssh/stellar-flux.prod.creds
pipenv run python3.7 -m bot --env prod "$@"