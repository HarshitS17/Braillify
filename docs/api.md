# API Documentation

## Base URL and Versioning
All endpoints are prefixed with `/api/v1/`.

## Endpoints

### Health
`GET /health`

### Projects (CRUD)
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/{id}`

### Pages (Planned)
- `POST /api/projects/{id}/pages`
- `GET /api/projects/{id}/pages`

### Processing Pipeline (Planned)
- `POST /api/projects/{id}/process`

### Export (Planned)
- `GET /api/projects/{id}/export`

## Error Response Format
```json
{
  "error": "Not Found",
  "message": "Project ID not found",
  "status_code": 404
}
```
