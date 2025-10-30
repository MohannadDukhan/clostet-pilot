CLOSET PILOT

Closet Pilot is an AI-powered wardrobe management web application built with a FastAPI backend and a React + Vite frontend.
It allows users to upload images of their clothing items, which are automatically analyzed and classified by an integrated GPT-4o-mini vision model.
The system predicts attributes such as category, color, season, and formality for each item. Users can view and manage their wardrobe through a modern dark-themed interface.

The project is designed as a prototype for future AI outfit generation, with a clean structure ready for expansion into authentication, outfit recommendations, and deployment.

OVERVIEW

Backend (FastAPI)

- Handles user creation, clothing uploads, and database storage.
- integrates with OpenAI GPT-4o-mini for automatic classification.
- Stores all data locally using SQLite.
- Uses an environment file (.env) for API keys and configuration.

Frontend (React + Vite + Tailwind)

- Provides a responsive dark-themed
- Supports navigation between pages such as Home, About, Create User, Dashboard, Upload, and Generate Outfit.
- Uses TailwindCSS v4 for styling and Framer Motion for animations (planned).

RUNNING THE PROJECT LOCALLY:

To run Closet Pilot on your machine, you need to set up both the backend and the frontend. The backend runs the FastAPI server, while the frontend runs a Vite development server that connects to it.

Prerequisites: Python 3.10+, Node.js 16+ and npm, and an OpenAI API key (create one at https://platform.openai.com)

Steps:

1. Navigate to your project folder -> backend
2. Create and activate virtual environment: 
    python -m venv venv
    venv\Scripts\activate 
3. install dependencies:
    pip install -r requirements.txt
4. Create a file named .env inside backend/
    Paste this content:
    OPENAI_API_KEY=your_openai_api_key_here
    AUTO_CLASSIFY_ON_UPLOAD=true
5. Run the backend server:
    uvicorn main:app --reload
6. Leave the backend open and open a new terminal window and navigate to your frontend
7. Install dependencies listed in package.json
    npm install
8. Start the development server:
    npm run dev
9. You’ll see a local address (usually http://localhost:5173). Open it in your browser.

USING THE APPLICATION:

1. With both servers running, open http://localhost:5173.
2. Create a new user on the main page.
3. Upload clothing images — the backend will automatically classify them.
4. Each item will show its predicted category, color, season, and formality.
5. You can edit or delete items directly from the interface.
6. The “Generate Outfit” page currently exists as a placeholder for future AI-based outfit suggestions.

All data (user info, image paths, and predictions) are stored locally in backend/database.db. If you delete that file, your wardrobe resets.

NEXT STEPS (for future development):

- Add user accounts with email + password login.
- Implement the actual outfit generator page once Model B is ready.
- Deploy both backend and frontend using Heroku, Railway, or Render.