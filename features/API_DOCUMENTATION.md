# API Documentation

Interactive docs: **http://localhost:8000/docs**

## Authentication

### Real W3ID
```
GET /auth/login
```
Redirects to IBM SSO. No query params.

### Dummy W3ID
```
GET /auth/login?mode=dummy&manager_name=Manager%201&employee_id=emp001
```

### Get Current User
```bash
curl -X GET "http://localhost:8000/auth/me" -b "session=YOUR_SESSION_COOKIE"
```

### Get Managers (for Dummy W3ID selection)
```bash
curl http://localhost:8000/auth/managers
```

### Get Manager Balance
```bash
curl -X GET "http://localhost:8000/auth/manager-balance" -b "session=YOUR_SESSION_COOKIE"
```

## Reservations

### Get Timeslots (full week)
```bash
curl "http://localhost:8000/reservations/timeslots?date=2026-02-05"
```

### Get Seats for Timeslot
```bash
curl "http://localhost:8000/reservations/seats?timeslot_id=1"
```

### Create Reservation (1 seat per user)
```bash
curl -X POST "http://localhost:8000/reservations" \
  -H "Content-Type: application/json" \
  -d '{"seat_id": 1, "timeslot_id": 1}' \
  -b "session=YOUR_SESSION_COOKIE"
```

### Get My Reservations
```bash
curl "http://localhost:8000/reservations/mine" -b "session=YOUR_SESSION_COOKIE"
```

### System Status
```bash
curl http://localhost:8000/reservations/verify
```

## Admin

### Dashboard
```bash
curl http://localhost:8000/admin/dashboard
```

### Weekly Bookings
```bash
curl http://localhost:8000/admin/bookings
```

### Reset (ACID: cancel bookings, restore balances)
```bash
curl -X POST http://localhost:8000/admin/reset
```

## Error Responses

| Code | Meaning |
|------|---------|
| 400 | Bad request (e.g. one-seat limit, invalid date) |
| 401 | Not authenticated |
| 402 | Insufficient manager balance |
| 404 | Resource not found |
| 409 | Conflict (seat/timeslot already booked) |
