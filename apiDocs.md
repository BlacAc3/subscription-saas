
# API-DOCS.md

```markdown
# API Documentation

This document provides detailed information about the Sub-SaaS API endpoints, request/response formats, and authentication requirements.

## API Base URL

The base URL for all API endpoints is: `http://localhost:8000`

## Authentication

Most endpoints require authentication using a JWT token. To get a token:

1. Make a POST request to `/auth/login` with your email and password.
2. Include the token in subsequent requests in the Authorization header:
   ```
   Authorization: Bearer <your_token>
   ```

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Endpoints

### Authentication

#### Login
```
POST /auth/login
```

Request body:
```json
{
  "username": "user@example.com",
  "password": "userpassword"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "60a6c59e9f5e8c3e1234abcd",
  "name": "John Doe",
  "email": "user@example.com",
  "roles": ["user"]
}
```

#### Get Current User
```
GET /auth/me
```

Response:
```json
{
  "id": "60a6c59e9f5e8c3e1234abcd",
  "name": "John Doe",
  "email": "user@example.com",
  "roles": ["user"],
  "is_active": true
}
```

### Users

#### Create User
```
POST /users/
```

Request body:
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "password": "securePassword123",
  "roles": ["user"],
  "metadata": {
    "department": "Engineering",
    "location": "Remote"
  }
}
```

Response:
```json
{
  "id": "60a6c59e9f5e8c3e1234abcd",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "is_active": true,
  "roles": ["user"],
  "created_at": "2023-05-29T14:30:45.123Z"
}
```

#### Get Users
```
GET /users/
```

Query parameters:
- `is_active` (optional): Filter by active status

Response:
```json
[
  {
    "id": "60a6c59e9f5e8c3e1234abcd",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "is_active": true,
    "roles": ["user"],
    "created_at": "2023-05-29T14:30:45.123Z"
  }
]
```

#### Get User by ID
```
GET /users/{user_id}
```

Response:
```json
{
  "id": "60a6c59e9f5e8c3e1234abcd",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "is_active": true,
  "roles": ["user"],
  "created_at": "2023-05-29T14:30:45.123Z",
  "updated_at": "2023-05-29T14:30:45.123Z",
  "metadata": {
    "department": "Engineering",
    "location": "Remote"
  }
}
```

#### Update User
```
PUT /users/{user_id}
```

Request body:
```json
{
  "name": "John Updated",
  "email": "john.updated@example.com",
  "is_active": true,
  "roles": ["user", "admin"],
  "metadata": {
    "department": "Management",
    "location": "Office"
  }
}
```

Response:
```json
{
  "id": "60a6c59e9f5e8c3e1234abcd",
  "name": "John Updated",
  "email": "john.updated@example.com",
  "is_active": true,
  "roles": ["user", "admin"],
  "updated_at": "2023-05-30T09:15:32.456Z",
  "update_successful": true
}
```

#### Get User Tenants
```
GET /users/{user_id}/tenants
```

Response:
```json
[
  {
    "id": "60b7d69e9f5e8c3e4567defg",
    "name": "Example Company",
    "domain": "example.com",
    "is_active": true
  }
]
```

#### Get User Owned Tenants
```
GET /users/{user_id}/owned-tenants
```

Response:
```json
[
  {
    "id": "60b7d69e9f5e8c3e4567defg",
    "name": "Example Company",
    "domain": "example.com",
    "is_active": true,
    "created_at": "2023-05-28T10:15:30.123Z"
  }
]
```

#### Get User Subscriptions
```
GET /users/{user_id}/subscriptions
```

Response:
```json
[
  {
    "id": "60c8e79e9f5e8c3e7890hijk",
    "tenant_id": "60b7d69e9f5e8c3e4567defg",
    "plan": "premium",
    "is_active": true,
    "start_date": "2023-05-28T10:20:30.123Z",
    "end_date": "2024-05-28T10:20:30.123Z"
  }
]
```

### Tenants

#### Create Tenant
```
POST /tenants/
```

Request body:
```json
{
  "name": "Example Company",
  "domain": "example.com",
  "owner_id": "60a6c59e9f5e8c3e1234abcd",
  "contact_email": "contact@example.com",
  "billing_address": "123 Main St, City, Country",
  "metadata": {
    "industry": "Technology",
    "size": "Medium"
  }
}
```

Response:
```json
{
  "id": "60b7d69e9f5e8c3e4567defg",
  "name": "Example Company",
  "domain": "example.com",
  "owner_id": "60a6c59e9f5e8c3e1234abcd",
  "created_at": "2023-05-28T10:15:30.123Z"
}
```

#### Get Tenants
```
GET /tenants/
```

Query parameters:
- `owner_id` (optional): Filter by owner
- `is_active` (optional): Filter by active status

Response:
```json
[
  {
    "id": "60b7d69e9f5e8c3e4567defg",
    "name": "Example Company",
    "domain": "example.com",
    "owner_id": "60a6c59e9f5e8c3e1234abcd",
    "is_active": true,
    "created_at": "2023-05-28T10:15:30.123Z"
  }
]
```

#### Get Tenant by ID
```
GET /tenants/{tenant_id}
```

Response:
```json
{
  "id": "60b7d69e9f5e8c3e4567defg",
  "name": "Example Company",
  "domain": "example.com",
  "owner_id": "60a6c59e9f5e8c3e1234abcd",
  "is_active": true,
  "created_at": "2023-05-28T10:15:30.123Z",
  "updated_at": "2023-05-28T10:15:30.123Z",
  "billing_address": "123 Main St, City, Country",
  "contact_email": "contact@example.com",
  "metadata": {
    "industry": "Technology",
    "size": "Medium"
  },
  "subscription_count": 2
}
```

#### Update Tenant
```
PUT /tenants/{tenant_id}
```

Request body:
```json
{
  "name": "Example Company Updated",
  "domain": "example-updated.com",
  "is_active": true,
  "contact_email": "new-contact@example.com",
  "billing_address": "456 New St, City, Country",
  "metadata": {
    "industry": "Software",
    "size": "Large"
  }
}
```

Response:
```json
{
  "id": "60b7d69e9f5e8c3e4567defg",
  "name": "Example Company Updated",
  "domain": "example-updated.com",
  "is_active": true,
  "updated_at": "2023-05-30T11:20:35.789Z",
  "update_successful": true
}
```

#### Get Tenant Subscriptions
```
GET /tenants/{tenant_id}/subscriptions
```

Response:
```json
[
  {
    "id": "60c8e79e9f5e8c3e7890hijk",
    "plan": "premium",
    "is_active": true,
    "start_date": "2023-05-28T10:20:30.123Z",
    "end_date": "2024-05-28T10:20:30.123Z",
    "user_count": 5,
    "max_users": 10
  }
]
```

#### Get Tenant Users
```
GET /tenants/{tenant_id}/users
```

Response:
```json
[
  {
    "id": "60a6c59e9f5e8c3e1234abcd",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "is_active": true
  }
]
```

### Subscriptions

#### Create Subscription
```
POST /subscriptions/
```

Request body:
```json
{
  "tenant_id": "60b7d69e9f5e8c3e4567defg",
  "plan": "premium",
  "max_users": 10,
  "billing_cycle": "monthly",
  "payment_method_id": "pm_1234567890"
}
```

Response:
```json
{
  "id": "60c8e79e9f5e8c3e7890hijk",
  "tenant_id": "60b7d69e9f5e8c3e4567defg",
  "plan": "premium",
  "is_active": true,
  "start_date": "2023-05-28T10:20:30.123Z",
  "billing_cycle": "monthly",
  "max_users": 10
}
```

#### Get Subscriptions
```
GET /subscriptions/
```

Query parameters:
- `tenant_id` (optional): Filter by tenant
- `is_active` (optional): Filter by active status

Response:
```json
[
  {
    "id": "60c8e79e9f5e8c3e7890hijk",
    "tenant_id": "60b7d69e9f5e8c3e4567defg",
    "plan": "premium",
    "is_active": true,
    "user_count": 5,
    "max_users": 10,
    "start_date": "2023-05-28T10:20:30.123Z",
    "end_date": "2024-05-28T10:20:30.123Z",
    "renewal_date": "2024-05-28T10:20:30.123Z",
    "billing_cycle": "monthly"
  }
]
```

#### Get Subscription by ID
```
GET /subscriptions/{subscription_id}
```

Response:
```json
{
  "id": "60c8e79e9f5e8c3e7890hijk",
  "tenant_id": "60b7d69e9f5e8c3e4567defg",
  "plan": "premium",
  "is_active": true,
  "start_date": "2023-05-28T10:20:30.123Z",
  "end_date": "2024-05-28T10:20:30.123Z",
  "renewal_date": "2024-05-28T10:20:30.123Z",
  "billing_cycle": "monthly",
  "user_count": 5,
  "max_users": 10,
  "subscribed_user_ids": ["60a6c59e9f5e8c3e1234abcd"],
  "has_available_seats": true
}
```

#### Update Subscription
```
PUT /subscriptions/{subscription_id}
```

Request body:
```json
{
  "plan": "enterprise",
  "is_active": true,
  "end_date": "2025-05-28T10:20:30.123Z",
  "billing_cycle": "annually",
  "max_users": 25
}
```

Response:
```json
{
  "id": "60c8e79e9f5e8c3e7890hijk",
  "tenant_id": "60b7d69e9f5e8c3e4567defg",
  "plan": "enterprise",
  "is_active": true,
  "user_count": 5,
  "max_users": 25,
  "billing_cycle": "annually",
  "update_successful": true
}
```

#### Add User to Subscription
```
POST /subscriptions/{subscription_id}/users
```

Request body:
```json
{
  "user_id": "60a6c59e9f5e8c3e1234abcd"
}
```

Response:
```json
{
  "subscription_id": "60c8e79e9f5e8c3e7890hijk",
  "user_id": "60a6c59e9f5e8c3e1234abcd",
  "success": true,
  "user_count": 6,
  "max_users": 25
}
```

#### Remove User from Subscription
```
DELETE /subscriptions/{subscription_id}/users/{user_id}
```

Response:
```json
{
  "subscription_id": "60c8e79e9f5e8c3e7890hijk",
  "user_id": "60a6c59e9f5e8c3e1234abcd",
  "success": true,
  "user_count": 5
}
```

#### Get Subscription Users
```
GET /subscriptions/{subscription_id}/users
```

Response:
```json
[
  {
    "id": "60a6c59e9f5e8c3e1234abcd",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "is_active": true
  }
]
```

## Error Responses

The API returns standard HTTP status codes to indicate the success or failure of a request.

Common error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

Common error codes:
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Authenticated user doesn't have permission
- `404 Not Found`: Requested resource doesn't exist
- `422 Unprocessable Entity`: Request validation error
