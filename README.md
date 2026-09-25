# REST API & Automation Projects

A hands-on backend and API integration project built with Python and Flask. The project demonstrates REST API development, PostgreSQL database integration, authentication, webhooks, OAuth 2.0, external API integration, API testing, and workflow automation with n8n.

## Technologies

* Python
* Flask
* PostgreSQL
* SQL
* REST APIs
* OAuth 2.0
* Webhooks
* n8n
* Postman
* `requests`
* Psycopg
* python-dotenv

## What I Built

### REST API

Built a Flask REST API for managing job application records with PostgreSQL.

Implemented:

* GET, POST, PUT, PATCH, and DELETE endpoints
* JSON request and response handling
* Request validation
* HTTP status code handling
* Parameterized SQL queries
* PostgreSQL transactions
* Resource lookup and error handling

### API Authentication

Implemented API-key authentication for protected endpoints.

Also implemented webhook-secret authentication for webhook-related operations.

### Webhooks

Built webhook endpoints that accept application events and validate incoming data.

Implemented duplicate event protection using a database uniqueness constraint and handled duplicate events with appropriate HTTP responses.

### External API Integration

Used Python `requests` to communicate with external REST APIs.

Implemented:

* JSON response parsing
* Query parameters
* Request headers
* Timeouts
* Network error handling
* Upstream API error handling

Integrated with the openFDA API and stored selected results in PostgreSQL.

### OAuth 2.0

Implemented the GitHub OAuth 2.0 Authorization Code flow.

The implementation includes:

* Authorization redirect
* OAuth state generation and validation
* Authorization code handling
* Access-token exchange
* Bearer-token authentication
* GitHub API requests

### n8n Automation

Built an n8n workflow that receives an application through a webhook and applies a salary-based workflow condition.

For applications meeting the configured salary threshold, the workflow:

1. Creates the application through `POST /applications`.
2. Uses the returned application ID dynamically.
3. Updates the application's status through `PATCH /applications/{id}/status`.

The workflow was tested with both qualifying and non-qualifying applications.

## API Examples

### Create an application

```http
POST /applications
```

Example request:

```json
{
  "company": "Example Company",
  "position": "Python Developer",
  "salary": 60000
}
```

### Get applications

```http
GET /applications
```

### Update application status

```http
PATCH /applications/{id}/status
```

Example request:

```json
{
  "status": "qualified"
}
```

## Testing

Postman was used to test the API endpoints, authentication, request validation, error cases, external API integrations, OAuth flow, and the n8n workflow.

The n8n workflow was tested through its webhook using both qualifying and non-qualifying application data.

## Project Scope

This is a hands-on learning and portfolio project developed locally to demonstrate practical backend, API integration, authentication, and automation skills.

It is not presented as a production deployment.
