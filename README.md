
Development
```
# start virtual env
python -m venv .venv
source .venv/bin/activate

# download packages
pip install -r requirements.txt

# start server
python -m src.app

# end
deactivate
```

Production
```
pip install -r requirements.txt

gunicorn --bind 0.0.0.0:3000 src.app:app
```