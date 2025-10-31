# Classifieds Pro

Classifieds Pro is a full-stack application designed to automate the management and posting of classified ads to wanuncios.com. It provides a user-friendly web dashboard to manage accounts, generate ad content with AI, and schedule automatic ad posting and republishing.

## Key Features

- **Account Management:** Securely store and manage multiple `wanuncios.com` user accounts.
- **Ad Management:** A full CRUD interface for creating, editing, and managing ad templates.
- **AI-Powered Text Generation:** Uses an integrated LLM to automatically generate compelling ad descriptions based on a title.
- **Scheduling System:** A robust scheduling system to automatically republish ads at user-defined intervals, ensuring they stay at the top of the listings.
- **Web Automation:** A Playwright-based service that automates the entire process of logging in and posting ads.
- **Modern UI:** A clean and responsive user interface built with React and shadcn/ui.

## Tech Stack

### Backend

- **Framework:** FastAPI
- **Database:** MongoDB (via `motor`)
- **Web Automation:** Playwright
- **Scheduling:** APScheduler
- **AI Integration:** `emergentintegrations`
- **Dependency Management:** `pip` with `requirements.txt`

### Frontend

- **Framework:** React (via `create-react-app`)
- **UI Library:** `shadcn/ui`
- **Styling:** Tailwind CSS
- **API Communication:** Axios
- **Testing:** Jest with React Testing Library
- **Dependency Management:** `npm`

## Project Structure

The project is a monorepo located in the `/app` directory, with two main sub-directories:

- `/app/backend`: The FastAPI application.
  - `/api`: Contains the API endpoint routers.
  - `/models`: Contains the Pydantic data models.
  - `/services`: Contains the business logic for services like AI, automation, and scheduling.
  - `/tests`: Contains pytest test suite for backend components.
  - `requirements.txt`: All backend dependencies for easy installation.
  - `main.py`: Entry point for the FastAPI application.

- `/app/frontend`: The React application.
  - `/src`: Contains React components, pages, and services.
  - `/public`: Contains static assets.
  - `jest.config.js`: Jest configuration for testing.
  - `package.json`: Frontend dependencies and scripts.
  - `tailwind.config.js`: Tailwind CSS configuration.

## Setup and Installation

### Backend

1. **Navigate to the backend directory:**
   ```bash
   cd app/backend
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the `app/backend` directory with the required variables:
   ```
   MONGODB_URI=mongodb://localhost:27017
   DATABASE_NAME=classifieds_pro
   UNIVERSAL_KEY=your_key_here
   TWOCAPTCHA_API_KEY=your_api_key_here
   ```

### Frontend

1. **Navigate to the frontend directory:**
   ```bash
   cd app/frontend
   ```

2. **Install NPM dependencies:**
   ```bash
   npm install
   ```

## How to Run

### Backend

From the `app/backend` directory, run the following command to start the FastAPI server:

```bash
uvicorn main:app --reload
```

The server will be available at `http://localhost:8001`.

### Frontend

From the `app/frontend` directory, run the following command to start the React development server:

```bash
npm start
```

The application will be available at `http://localhost:3000`.

## Testing

### Backend Testing

The backend includes a suite of integration tests. To run them:

1. **Navigate to the backend directory:**
   ```bash
   cd app/backend
   ```

2. **Run pytest:**
   ```bash
   pytest
   ```

**Note:** During development, an intractable `TimeoutError` was encountered with the test runner (`asgi-lifespan`) in some environments. The tests are written to be correct and use best practices (mocking, dependency injection), but they may require environment-specific debugging.

### Frontend Testing

The frontend now includes Jest configuration and example tests. To run frontend tests:

1. **Navigate to the frontend directory:**
   ```bash
   cd app/frontend
   ```

2. **Run Jest tests:**
   ```bash
   npm test
   ```

Test files should follow the naming convention: `*.test.js` or `*.spec.js`

**Configuration:** Jest is configured in `jest.config.js` to work with React and supports path aliases like `@/` for the src directory.

## Known Limitations

- **CAPTCHA:** The target website, `wanuncios.com`, uses CAPTCHA on both its login and ad posting pages. The current automation service has support for flexible CAPTCHA solving methods (API-based via 2Captcha, local scripts, or manual solving), but these require configuration.

- **Frontend Tests:** While Jest is now configured, comprehensive test coverage for React components is still in progress. A basic example test (`App.test.js`) has been added as a starting point.

- **No CI/CD:** There is no continuous integration or deployment pipeline set up. This should be implemented for production use.

## Next Steps

- Expand frontend test coverage with more comprehensive component tests
- Implement CI/CD pipeline using GitHub Actions
- Add end-to-end (E2E) tests with tools like Cypress or Playwright
- Optimize MongoDB queries and add proper indexing
- Implement user authentication and authorization
- Add proper error handling and logging throughout the application
- Create API documentation (Swagger/OpenAPI)
- Deploy to production environment
