

# .creds file should look like this 
# export CLIENT_TOKEN="LOTS OF NUMBERS THAT MAKE A TOKEN GO HERE"

git checkout master
git pull
source ~/.ssh/poebot-prod.creds
pipenv install
pipenv run python3.7 -m bot --env prod "$@"