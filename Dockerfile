ARG ENV=dev
# Use official base image
FROM python:3.10-slim

ENV ENVIRONMENT=$ENV



# Set working directory inside container
WORKDIR /app

# Copy app code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8443

# Start the app
CMD ["python3 -m", "polybot.app"]
