FROM python:3.10-slim
WORKDIR /app

COPY . /app/


RUN pip install --upgrade pip
RUN pip install -r requirement.txt

EXPOSE 8020

CMD ["python", "manage.py", "runserver", "0.0.0.0:8020"]
