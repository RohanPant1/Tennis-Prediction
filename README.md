# Tennis Prediction App

This project is a full-stack application designed to predict the outcome of ATP tennis matches using machine learning. It leverages historical match data to train an XGBoost model, which is then served via a FastAPI backend to a React frontend.

## Project Structure

- **`backend/`**: Contains the FastAPI application, the trained machine learning model (`tennis_prediction_pipeline.joblib`), data processing scripts, and Jupyter notebooks used for data cleaning, feature engineering, and model training.
- **`frontend/`**: A React application built with Vite that provides a user interface for selecting players and match conditions to get predictions.
- **`data/`**: Stores raw and processed CSV/Excel files containing ATP match statistics and rankings.
- **`atp_scraper/`**: Utilities for scraping latest ATP match data (if applicable).

## Prerequisites

- **Python 3.8+**
- **Node.js 16+** & **npm**

## Installation & Setup

### 1. Backend Setup

The backend handles the prediction logic and serves the API.

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```

2.  (Optional but recommended) Create and activate a virtual environment:
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  Start the FastAPI server:
    ```bash
    uvicorn main:app --reload
    ```
    The backend API will be available at `http://localhost:8000`.

### 2. Frontend Setup

The frontend provides the interactive UI for the application.

1.  Open a new terminal and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  Install the dependencies:
    ```bash
    npm install
    ```

3.  Start the development server:
    ```bash
    npm run dev
    ```
    The application should now be running at `http://localhost:5173` (or the port specified in your terminal).

## Usage

1.  Ensure both the backend and frontend servers are running.
2.  Open your browser and go to `http://localhost:5173`.
3.  Enter the names of the two players (Player 1 and Player 2).
4.  Select the match conditions:
    -   **Target Date**: Date of the match.
    -   **Surface**: Hard, Clay, Grass, etc.
    -   **Draw Size**: Size of the tournament draw.
    -   **Best Of**: 3 or 5 sets.
    -   **Tournament Level**: Grand Slam, Masters, etc.
    -   **Round Index**: The round of the tournament.
5.  Click **Predict** to see the predicted winner and the probability of winning.

## Data Pipeline

The project includes several Jupyter notebooks in the `backend/` directory that document the data science workflow:

-   `data_clean.ipynb`: Cleaning raw ATP match data.
-   `feature_add.ipynb` & `feature_engineer.ipynb`: creating features for the model.
-   `model.ipynb`: Training and evaluating the XGBoost model.

## Technologies Used

-   **Frontend:** React, Vite, Axios
-   **Backend:** Python, FastAPI, Pandas, XGBoost, Scikit-learn (Joblib)
-   **Data:** Historical ATP Match Data
