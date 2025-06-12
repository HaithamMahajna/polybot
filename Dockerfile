ARG ENV=dev
# Use official base image
FROM python:3.10-slim

ENV ENVIRONMENT=$ENV



# Set working directory inside container
WORKDIR /app

# Copy app code


# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install boto3
RUN pip install pydantic  
COPY . . 
# Expose port
EXPOSE 8443

# Start the app
CMD ["python3", "-m" ,"polybot.app"]
