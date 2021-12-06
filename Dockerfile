FROM python:3.9

WORKDIR /python-code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python","./solution/solution.py"]


