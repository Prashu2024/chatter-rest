# Chatter (REST API Version)

## Overview

This project is a REST API-based chat application built on top of [rishabh10gpt/chatter](https://github.com/rishabh10gpt/chatter), which originally used WebSockets for real-time communication. The original WebSocket implementation was adapted to a RESTful architecture to ensure compatibility with serverless platforms like Netlify and Vercel, which do not natively support persistent WebSocket connections. This version retains the core functionality—pairing users based on tags and enabling chat—while using HTTP polling instead of WebSockets.

## Features

- **User Pairing**: Matches users based on common tags (e.g., interests).
- **Chat Functionality**: Users can send and receive messages with their paired partner.
- **Online Status**: Displays the number of currently connected users.
- **Geo-Location**: Fetches user location based on IP using the `ipinfo.io` API.
- **Auto-Reconnect**: Automatically attempts to reconnect users if disconnected (optional).
- **Serverless-Friendly**: Designed to deploy on platforms like Netlify or Vercel.

## Differences from the Original

The original `rishabh10gpt/chatter` used WebSockets for real-time, bidirectional communication. This version:
- Replaces WebSockets with REST API endpoints (`/connect`, `/message`, `/poll`, `/disconnect`).
- Uses HTTP polling (every 1 second) to fetch messages and status updates instead of server-pushed events.
- Removes WebSocket-specific dependencies and logic, making it compatible with serverless environments.

## Tech Stack

- **Backend**: FastAPI (Python), Pydantic for request validation
- **Frontend**: HTML, JavaScript, Bootstrap, custom CSS
- **Deployment**: Compatible with Netlify, Vercel, or traditional servers
- **Dependencies**: `requests` for geolocation, `jinja2` for templating

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Prash2024/chatter-rest.git
   cd chatter-rest
  
2. **Install Dependencies**: Ensure you have Python 3.8+ installed, then:
	```bash
	pip install -r requirements.txt

Create a requirements.txt with:
	```text
	fastapi
	uvicorn
	jinja2
	requests
	pydantic

3. **Run Locally**:
	```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    
Open http://localhost:8000 in your browser.

## Usage

    Connect: Enter optional tags (comma-separated) and click "Connect" to find a partner.
    Chat: Once paired, type messages and press "Send". Messages appear via polling.
    Disconnect: Click "Disconnect" to end the session. Auto-reconnect is enabled by default.
    
## Credits

    Built upon rishabh10gpt/chatter.
    Adapted to REST API by Prashant Gupta
