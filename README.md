# Sentiment Analysis API

This is a FastAPI application that performs sentiment analysis on text inputs using NLTK's VADER sentiment analysis tool.

## Features

- Analyze the sentiment of a single text input.
- Analyze the sentiment of multiple text inputs.
- Retrieve sentiment classification categories.
- Get statistics on sentiment distribution for multiple texts.

## Requirements

- Python 3.7 or higher
- FastAPI
- Uvicorn
- NLTK

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ntsation/sentiment-analysis-api.git
   cd sentiment-analysis-api
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

   ```bash
   python src/main.py
   ```

   The API will start on `http://127.0.0.1:8000`.

2. Use an API client like Postman or curl to interact with the endpoints.

### API Endpoints

- **POST /analyze**
  - Analyze sentiment of a single text.
  - **Request Body:**
    ```json
    {
      "text": "Your text here"
    }
    ```
  - **Response:**
    ```json
    {
      "text": "Your text here",
      "sentiment": {
        "neg": 0.0,
        "neu": 0.4,
        "pos": 0.6,
        "compound": 0.5
      }
    }
    ```

- **POST /analyze_multiple**
  - Analyze sentiment of multiple texts.
  - **Request Body:**
    ```json
    {
      "texts": ["Text one", "Text two"]
    }
    ```
  - **Response:**
    ```json
    {
      "results": {
        "Text one": { ... },
        "Text two": { ... }
      }
    }
    ```

- **GET /sentiment_classes**
  - Retrieve sentiment classification categories.
  - **Response:**
    ```json
    {
      "classes": {
        "positive": "Scores greater than 0.05",
        "neutral": "Scores between -0.05 and 0.05",
        "negative": "Scores less than -0.05"
      }
    }
    ```

- **POST /analyze_statistics**
  - Get statistics on the sentiment distribution for multiple texts.
  - **Request Body:**
    ```json
    {
      "texts": ["Text one", "Text two"]
    }
    ```
  - **Response:**
    ```json
    {
      "statistics": {
        "positive": 1,
        "neutral": 1,
        "negative": 0
      }
    }
    ```