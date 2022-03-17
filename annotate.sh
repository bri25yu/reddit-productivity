pip install -q -q -r requirements.txt

python manage.py migrate

python -c "import webbrowser;webbrowser.open('http://localhost:8000/')"

python manage.py runserver
