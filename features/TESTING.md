# Testing Guide - TDD Approach

This project follows Test-Driven Development (TDD) with comprehensive test coverage.

## Quick Start

```bash
# 1. Install dependencies (includes pytest)
cd features
pip install -r requirements.txt

# 2. Run tests (use python -m pytest if pytest command not found)
python -m pytest

# Or if pytest is in PATH:
pytest

# With verbose output
python -m pytest -v

# With coverage report (requires pytest-cov: pip install pytest-cov)
python -m pytest --cov=app --cov-report=html
```

## Test Structure

| File | Focus |
|------|-------|
| `tests/test_auth.py` | Authentication: Real W3ID, Dummy W3ID, managers, session |
| `tests/test_reservations.py` | Reservations, timeslots, seats, admin, race conditions |
| `tests/test_basic.py` | Basic health checks |

## Key Test Scenarios

### Authentication
- **Real W3ID**: Login redirects to IBM SSO when configured
- **Dummy W3ID**: Invalid manager returns 400
- **Managers**: List returned for Dummy W3ID selection
- **Session**: `/auth/me` returns 401 when not authenticated

### Reservations
- **Single seat**: User can only have 1 active reservation
- **Double booking**: Unique constraint prevents same seat/timeslot
- **Full week**: Timeslots available for today through today+6
- **Zero balance**: Manager with 0 points cannot book

### Admin
- **Reset (ACID)**: Cancels reservations, restores balances in one transaction
- **Dashboard**: Returns all required data

### Race Conditions
- **Concurrent booking**: `uq_seat_timeslot` prevents two users booking same seat

## Example: Running a Specific Test

```bash
pytest tests/test_reservations.py::test_one_seat_booking_limit -v
```

## Example: Test Output

```
tests/test_reservations.py::test_one_seat_booking_limit PASSED
tests/test_reservations.py::test_unique_constraint_prevents_double_booking PASSED
```

## Prerequisites

- Database must be initialized (tables created). Run the app once or rely on `conftest.py` autouse fixture.
- No mock auth or special setup needed for most tests.
