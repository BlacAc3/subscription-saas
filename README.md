# Sub-SaaS API

A flexible, multi-tenant subscription management API built with FastAPI and MongoDB.

## Overview

Sub-SaaS API is an open-source platform designed to help developers quickly implement multi-tenant subscription functionality in their SaaS applications. It provides a complete backend solution for managing users, tenants, and subscription plans with features like:

- User authentication and authorization
- Tenant management
- Subscription plans and user allocation
- JWT-based authentication

## Features

- **User Management**: Create, update, and manage user accounts with role-based permissions
- **Tenant System**: Multi-tenant architecture to isolate organizations/customers
- **Subscription Plans**: Flexible subscription management with different tiers and user limits
- **RESTful API**: Clean API design following REST principles
- **Documentation**: Interactive API documentation with Swagger UI and ReDoc
- **Authentication**: Secure JWT token-based authentication

## Prerequisites

- Python 3.8+
- MongoDB database
- Docker (optional, for containerized deployment)

## Installation

### Option 1: Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/blacac3/subscription-saas.git
   cd sub-saas
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   MONGO_URI=mongodb://localhost:27017
   SECRET_KEY=your-secret-key-here
   PORT=8000
   ```

5. Run the application:
   ```bash
   cd app
   python main.py
   ```

### Option 2: Docker Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/blacac3/subscription-saas.git
   cd sub-saas
   ```

2. Build and run the Docker container:
   ```bash
   docker build -t sub-saas-api .
   docker run -p 8000:8000 -e MONGO_URI=mongodb://your-mongo-db-uri -e SECRET_KEY=your-secret-key sub-saas-api
   ```

## Configuration

The application can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | mongodb://localhost:27017 |
| `SECRET_KEY` | Secret key for JWT token generation | your-secret-key-here |
| `PORT` | Port for the API server | 8000 |

## Usage

Once the application is running, you can interact with it using HTTP requests or explore the API using the Swagger documentation at `http://localhost:8000/docs`.

### Quick Start

1. Create a user:
   ```bash
   curl -X POST http://localhost:8000/users/ \
     -H "Content-Type: application/json" \
     -d '{"name": "John Doe", "email": "john@example.com", "password": "securepassword"}'
   ```

2. Login to get an access token:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -d "username=john@example.com&password=securepassword"
   ```

3. Create a tenant:
   ```bash
   curl -X POST http://localhost:8000/tenants/ \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Company", "domain": "mycompany.com", "owner_id": "YOUR_USER_ID"}'
   ```

4. Create a subscription:
   ```bash
   curl -X POST http://localhost:8000/subscriptions/ \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"tenant_id": "YOUR_TENANT_ID", "plan": "basic", "max_users": 10}'
   ```

For more detailed API usage, please refer to the [API Documentation](API-DOCS.md) or the Swagger UI at `http://localhost:8000/docs`.

## Project Structure

```
sub-saas/
├── app/
│   ├── models/
│   │   ├── user.py
│   │   ├── tenant.py
│   │   └── subscription.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── tenant.py
│   │   └── subscription.py
│   ├── util/
│   │   └── auth.py
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── tests/
├── .env
├── Dockerfile
├── requirements.txt
└── README.md
```

## API Endpoints

The API is organized around the following resources:

- `/auth` - Authentication endpoints
- `/users` - User management
- `/tenants` - Tenant management
- `/subscriptions` - Subscription management

For detailed documentation of all endpoints, refer to the [API Documentation](API-DOCS.md) or visit the Swagger UI at `http://localhost:8000/docs`.

## Development

### Requirements

- Development requirements are listed in `requirements-dev.txt`

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI - https://fastapi.tiangolo.com/
- MongoDB - https://www.mongodb.com/
- Motor - https://motor.readthedocs.io/
