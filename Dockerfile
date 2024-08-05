FROM python:latest

# Copy application source
COPY ./source ./source

# Copy requirements.txt
COPY ./requirements.txt ./requirements.txt

# Copy the token.txt file
COPY ./token.txt ./token.txt

# Install python dependencies
RUN pip install -r ./requirements.txt

# run the python app
CMD ["python", "source/telegram_bot"]
