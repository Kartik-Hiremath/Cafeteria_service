# Test Cases for Cafeteria Service - Blu-Reserve

Comprehensive test scenarios and verification procedures for the cafeteria seat booking system.

## Authentication Tests

### 1. Successful Login
**Scenario**: User logs in successfully with mock authentication
- **Precondition**: Backend is running on http://localhost:8000
- **Steps**:
  1. Open http://localhost:3000
  2. Click "Continue with W3ID" button
  3. Verify auto-login (mock auth enabled)
- **Expected Result**: User is logged in and redirected to seat selection page
- **Post-condition**: Session cookie is created

### 2. Manager Selection
**Scenario**: User selects a manager during login
- **Precondition**: User is on login page
- **Steps**:
  1. Select a manager from dropdown
  2. Enter employee ID
  3. Click login
- **Expected Result**: User is authenticated with selected manager assignment
- **Verification**: Manager name appears in header

## Booking Functionality Tests

### 3. Single Seat Booking
**Scenario**: User books a single seat for a timeslot
- **Precondition**: User is logged in and on seat selection page
- **Steps**:
  1. Select a date (today or tomorrow)
  2. Select a timeslot
  3. Click an available seat (blue button)
  4. Click "Confirm Booking"
- **Expected Result**: Booking confirmation page appears with success message
- **Verification**: 
  - Seat turns gray (booked)
  - Manager balance decreases by 10 Blu-Dollars
  - Toast shows "Booking confirmed! 10 Blu-Dollars charged"

### 4. Two Seat Booking Limit
**Scenario**: User attempts to book 2 seats (maximum allowed)
- **Precondition**: User is on seat selection page
- **Steps**:
  1. Select a timeslot
  2. Click first available seat
  3. Click second available seat
  4. Verify only 2 seats can be selected
  5. Click "Confirm Booking"
- **Expected Result**: Only first selected seat is booked
- **Verification**: 
  - System enforces 2-seat limit
  - Error shown if trying to select more than 2

### 5. Three Seat Attempt (Should Fail)
**Scenario**: User attempts to select 3 seats (above limit)
- **Precondition**: User has selected 2 seats
- **Steps**:
  1. Try to select a third seat
- **Expected Result**: Error message "You can only select up to two seats per booking"
- **Verification**: Third seat cannot be selected

### 6. Zero Balance Booking (Should Fail)
**Scenario**: User with zero balance manager tries to book
- **Precondition**: User assigned to "Manager with 0 points"
- **Steps**:
  1. Select a timeslot
  2. Click an available seat
  3. Click "Confirm Booking"
- **Expected Result**: Error message "Your manager has 0 Blu-Points. Booking not allowed."
- **Verification**: No booking is created, no charges made

### 7. Seat Availability After 5 Minutes
**Scenario**: Seat becomes available after 5-minute timer
- **Precondition**: Seat is booked by user
- **Steps**:
  1. Wait for 5 minutes after booking
  2. Refresh seat list
- **Expected Result**: Previously booked seat becomes available again
- **Verification**: Seat shows as blue (available) instead of gray (booked)

## Admin Functionality Tests

### 8. Admin Dashboard Access
**Scenario**: Admin accesses comprehensive dashboard
- **Precondition**: User is logged in as admin
- **Steps**:
  1. Navigate to http://localhost:3000/admin
  2. Verify dashboard loads
- **Expected Result**: Admin dashboard with statistics and booking views
- **Verification**: All dashboard sections load without errors

### 9. View Today/Tomorrow Bookings
**Scenario**: Admin views bookings for today and tomorrow
- **Precondition**: Admin is on dashboard
- **Steps**:
  1. Scroll to "Today & Tomorrow Bookings" section
  2. Verify bookings organized by date and timeslot
- **Expected Result**: Clear view of all bookings grouped by date
- **Verification**: Each timeslot shows count and details of reservations

### 10. System Reset Functionality
**Scenario**: Admin resets entire system
- **Precondition**: There are active bookings in the system
- **Steps**:
  1. Click "Reset System" button
  2. Confirm reset in popup
  3. Wait for operation to complete
- **Expected Result**: Success message with cancellation counts
- **Verification**:
  - All reservations cancelled
  - All manager balances restored to 50,000
  - Seats become available immediately

## Edge Case Tests

### 11. Concurrent Booking Attempt
**Scenario**: Multiple users try to book same seat simultaneously
- **Precondition**: Two users viewing same seat
- **Steps**:
  1. User A clicks seat first
  2. User B clicks same seat (slightly delayed)
- **Expected Result**: User A gets booking, User B gets conflict error
- **Verification**: Only one booking is created for the seat

### 12. Session Timeout Handling
**Scenario**: User session expires during booking
- **Precondition**: User has been inactive for extended period
- **Steps**:
  1. Attempt to book a seat after session timeout
- **Expected Result**: Redirect to login page
- **Verification**: User must re-authenticate

### 13. Timeslot Boundary Conditions
**Scenario**: Booking near timeslot boundaries
- **Precondition**: Current time is near timeslot end
- **Steps**:
  1. Book seat close to timeslot end
  2. Wait until timeslot ends
- **Expected Result**: Seat becomes available at timeslot end
- **Verification**: Seat availability updates correctly

## Database Verification Tests

### 14. Data Integrity Checks
```bash
# Count total seats (should be 100)
sqlite3 cafeteria.db "SELECT COUNT(*) FROM seats;"

# Count total managers (should be 12)
sqlite3 cafeteria.db "SELECT COUNT(*) FROM managers;"

# Count total timeslots (should be 12 for 2 days with 6 slots each)
sqlite3 cafeteria.db "SELECT COUNT(*) FROM timeslots;"

# Check for orphaned records
sqlite3 cafeteria.db "SELECT COUNT(*) FROM reservations WHERE user_id NOT IN (SELECT id FROM users);"
```

### 15. How Data is Handled
1. **Reservation Creation**: When booking occurs, a reservation is created in the DB with available_at set to 5 minutes from booking time
2. **Balance Deduction**: 10 Blu-Dollars are immediately deducted from manager balance
3. **Availability Logic**: Seats are considered booked until either the timeslot ends OR the 5-minute timer expires (whichever comes first)
4. **Cleanup**: Old reservations are kept in DB for historical purposes, only status changes from 'confirmed' to 'cancelled'

## API Testing Examples

### 16. Manual API Tests
```bash
# Get all managers
curl -s http://localhost:8000/auth/managers | jq

# Get admin dashboard data
curl -s http://localhost:8000/admin/dashboard | jq

# Get today and tomorrow bookings
curl -s http://localhost:8000/admin/bookings | jq

# Get timeslots for today
curl -s "http://localhost:8000/reservations/timeslots?date=$(date +%Y-%m-%d)" | jq

# Get seats for a timeslot (replace TIMESLOT_ID)
curl -s "http://localhost:8000/reservations/seats?timeslot_id=TIMESLOT_ID" | jq

# Reset system (admin function)
curl -s -X POST http://localhost:8000/admin/reset | jq
```

## Frontend Testing

### 17. UI Interaction Tests
- Navigate to http://localhost:3000
- Use the login modal to select a manager and employee ID
- Select a date and timeslot
- Choose a seat and confirm booking
- Verify success message and seat status change
- Check that manager balance updates appropriately
- Verify 5-minute timer display updates correctly

### 18. Admin Interface Tests
- Access http://localhost:3000/admin
- Verify all dashboard statistics are displayed
- Check that today/tomorrow bookings are shown correctly
- Test refresh buttons work
- Verify reset functionality works as expected

## Performance Tests

### 19. Real-time Updates
- **Scenario**: Multiple users viewing same seat availability
- **Steps**: 
  1. User A books a seat
  2. User B (on different machine) should see seat turn gray within 5 seconds
- **Expected**: Real-time synchronization of seat availability
- **Verification**: Auto-refresh every 5 seconds works correctly

## Error Handling Tests

### 20. Network Error Recovery
- **Scenario**: Network interruption during booking
- **Steps**:
  1. Attempt to book while simulating network issues
  2. Restore network connectivity
  3. Retry booking
- **Expected**: Clear error messages and retry capability
- **Verification**: System handles network failures gracefully

### 21. Invalid Input Handling
- **Scenario**: Malformed API requests
- **Steps**:
  1. Send invalid data to booking endpoint
  2. Verify appropriate error responses
- **Expected**: 400 Bad Request or 422 Validation Error
- **Verification**: System validates all inputs properly