# Artifex

Artifex is an AI image generator built with FastAPI and Next.js.  
It generates high-quality images from text prompts with style options and enhancement support.

## Features

- Text-to-image generation.
- Multiple art styles.
- Prompt enhancement.
- User-specific image history.
- Secure backend with token-based access.
- Rate limiting for API protection.

## Tech Stack

- Frontend: Next.js
- Backend: FastAPI
- Image generation API: Pollinations AI
- Deployment: Hugging Face Spaces

## Project Structure

```bash
Artifex/
├── backend/
│   └── main.py
├── public/
│   └── generated/
├── src/
├── Dockerfile
├── .env.example
├── package.json
└── README.md
```

## Environment Variables

Create a `.env` file from `.env.example`.

Example:

```env
BACKEND_SECRET_TOKEN=your_secret_token
HOST=0.0.0.0
PORT=7860
```

## Local Setup

1. Clone the repository.
2. Install frontend and backend dependencies.
3. Create your `.env` file.
4. Run the backend and frontend.

## Run Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 7860
```

## Deploy on Hugging Face

1. Create a new Hugging Face Space.
2. Select `Docker` as the SDK.
3. Upload the project files.
4. Add secrets in Hugging Face Space settings.
5. Commit and wait for build to finish.

## Notes

- Do not commit `.env` to GitHub.
- Keep `.env.example` updated with required variables.
- Public Spaces are easiest for free deployment.

## License

This project is for educational and personal use.
