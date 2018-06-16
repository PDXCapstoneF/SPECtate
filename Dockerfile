FROM kennethreitz/pipenv

COPY . /app

CMD python3 mainCLI.py
