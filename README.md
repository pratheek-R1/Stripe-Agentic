# Paygentic — AI Payment Orchestration Platform

-------------------------------------------------------------------------------------------------------------------------------------------------------------

Turn natural language into live Stripe payment links using AI-powered agent orchestration.

## Architecture Flow

![Architecture](https://github.com/user-attachments/assets/10574242-3260-4113-9b2a-9c7b314bb7c4)

## Demo Preview

### Main Interface

![Paygentic UI](https://github.com/user-attachments/assets/3e302325-6e7c-4117-8db9-a6e4a928e549)

### Generated Payment Flow

![Payment Flow](https://github.com/user-attachments/assets/26efa0c7-b63f-4d6b-a71a-83b511fa03c6)

### Stripe Checkout

![Stripe Checkout](https://github.com/user-attachments/assets/2dc8bc3f-fcdf-4fdd-ad67-d8afcda184a7)

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Overview

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Paygentic allows users to create Stripe payment links using natural language.

Example:

> "Send a $250 invoice for logo design to alice@company.com"

The system automatically:
- extracts payment details
- identifies customer information
- creates Stripe products/prices
- generates a Stripe checkout link instantly

The project combines:
- AI parsing
- autonomous agent workflows
- payment orchestration
- real-time frontend interactions

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Features

-------------------------------------------------------------------------------------------------------------------------------------------------------------

- Natural language payment generation
- AI-powered invoice parsing
- Stripe checkout automation
- Real-time payment link generation
- Agent-to-agent orchestration
- Responsive frontend UI
- Proxy-based backend communication

-------------------------------------------------------------------------------------------------------------------------------------------------------------

## Requirements

-------------------------------------------------------------------------------------------------------------------------------------------------------------

- Python 3.10+
- Stripe API Key
- Groq API Key

-------------------------------------------------------------------------------------------------------------------------------------------------------------

## Installation & Setup

-------------------------------------------------------------------------------------------------------------------------------------------------------------

```bash
# Clone the repository
git clone https://github.com/pratheek-R1/Stripe-Agentic

cd Stripe-Agentic

# Install dependencies
pip install -r requirements.txt

# OR install using Poetry
poetry install
```

Create a `.env` file in the root directory and add:

```env
STRIPE_SECRET_KEY=your_stripe_secret_key
GROQ_API_KEY=your_groq_api_key
```

Run the backend server:

```bash
python run_agents.py
```

Open a second terminal and run the frontend server:

```bash
python frontend/serve.py
```

Open the application in your browser:

```text
http://localhost:3000
```

Example payment prompt:

```text
Send a $250 invoice for logo design to alice@company.com
```

The AI agent extracts payment details automatically and instantly generates a Stripe checkout payment link.

-------------------------------------------------------------------------------------------------------------------------------------------------------------

## Usage

-------------------------------------------------------------------------------------------------------------------------------------------------------------

### Start the backend server

```bash
python run_agents.py
```

### Start the frontend server

Open a second terminal:

```bash
python frontend/serve.py
```

### Open the application

Visit:

```text
http://localhost:3000
```

### Example Prompt

```text
Send a $250 invoice for logo design to alice@company.com
```

The AI system extracts:
- payment amount
- customer email
- service/product name

and instantly generates a Stripe checkout payment link through natural language.


-------------------------------------------------------------------------------------------------------------------------------------------------------------

## Tech Stack

-------------------------------------------------------------------------------------------------------------------------------------------------------------

- Python
- JavaScript
- Stripe API
- Groq LLM API
- HTML/CSS
- Tailwind CSS
- uAgents
- CrewAI

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
