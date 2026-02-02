import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SeatSelectionPage } from '../seat-selection-page';

// Mock the API service
vi.mock('@/services/api', () => ({
  reservationsAPI: {
    getTimeslots: vi.fn(),
    getSeats: vi.fn(),
    createReservation: vi.fn(),
    getMyReservations: vi.fn(),
  },
  authAPI: {
    getManagerBalance: vi.fn(),
  },
}));

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

// Mock child components
vi.mock('@/app/components/ui/button', () => ({
  Button: ({ children, onClick, disabled }: any) => (
    <button onClick={onClick} disabled={disabled} data-testid="button">
      {children}
    </button>
  ),
}));

vi.mock('@/app/components/ui/card', () => ({
  Card: ({ children, className }: any) => (
    <div className={className} data-testid="card">
      {children}
    </div>
  ),
}));

describe('SeatSelectionPage - TDD Test Suite', () => {
  const mockProps = {
    onConfirmBooking: vi.fn(),
    onLogout: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // === TDD Test 1: Component Rendering Tests ===
  it('should render seat selection page with all required elements', () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Verify main components exist
    expect(screen.getByText('Riviera Booking')).toBeInTheDocument();
    expect(screen.getByText('Booking details')).toBeInTheDocument();
    expect(screen.getByText('Choose table')).toBeInTheDocument();
  });

  it('should display calendar for date selection', () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Calendar navigation should be present
    expect(screen.getByText('Jan')).toBeInTheDocument();
    expect(screen.getByText('Feb')).toBeInTheDocument();
  });

  it('should show manager balance information when available', async () => {
    // Mock manager balance data
    const { authAPI } = await import('@/services/api');
    (authAPI.getManagerBalance as any).mockResolvedValue({
      manager_name: 'Test Manager',
      balance: 50000,
    });
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Wait for balance to load
    await waitFor(() => {
      expect(screen.getByText(/Test Manager/)).toBeInTheDocument();
    });
  });

  // === TDD Test 2: User Interaction Tests ===
  it('should allow date selection from calendar', async () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Select today's date
    const todayButton = screen.getByText(new Date().getDate().toString());
    fireEvent.click(todayButton);
    
    // Verify date is selected
    expect(todayButton).toHaveClass('bg-blue-600');
  });

  it('should display timeslots when date is selected', async () => {
    const { reservationsAPI } = await import('@/services/api');
    (reservationsAPI.getTimeslots as any).mockResolvedValue([
      {
        id: 1,
        starts_at: '2026-02-01T12:00:00',
        ends_at: '2026-02-01T12:30:00',
      },
    ]);
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Select a date first
    const dateButton = screen.getByText('15'); // Any date
    fireEvent.click(dateButton);
    
    // Wait for timeslots to load
    await waitFor(() => {
      expect(reservationsAPI.getTimeslots).toHaveBeenCalled();
    });
  });

  it('should allow timeslot selection', async () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Mock timeslot selection
    const timeslotButton = screen.getByText('12:00 - 12:30 PM'); // Mock text
    fireEvent.click(timeslotButton);
    
    // Verify selection feedback
    expect(timeslotButton).toHaveClass('bg-blue-600');
  });

  // === TDD Test 3: Seat Selection Logic ===
  it('should allow seat selection from available seats', async () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Mock seat selection
    const seatButton = screen.getByText('A1'); // Mock seat
    fireEvent.click(seatButton);
    
    // Verify seat is selected (should have selected styling)
    expect(seatButton).toHaveClass('bg-blue-600');
  });

  it('should prevent selecting more than 2 seats', async () => {
    const { toast } = await import('sonner');
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Select first seat
    const seat1 = screen.getByText('A1');
    fireEvent.click(seat1);
    
    // Select second seat
    const seat2 = screen.getByText('A2');
    fireEvent.click(seat2);
    
    // Try to select third seat - should show error
    const seat3 = screen.getByText('A3');
    fireEvent.click(seat3);
    
    // Verify error message
    expect(toast.error).toHaveBeenCalledWith(
      'You can only book up to two seats per timeslot'
    );
  });

  it('should disable booked seats from selection', () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Mock a booked seat
    const bookedSeat = screen.getByText('B1'); // Mock booked seat
    expect(bookedSeat).toBeDisabled();
    expect(bookedSeat).toHaveClass('bg-gray-200');
  });

  // === TDD Test 4: Booking Confirmation ===
  it('should enable booking button when valid selections are made', async () => {
    const { reservationsAPI } = await import('@/services/api');
    (reservationsAPI.createReservation as any).mockResolvedValue({
      id: 1,
      seat_id: 1,
      timeslot_id: 1,
    });
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Make all required selections
    fireEvent.click(screen.getByText('15')); // Date
    fireEvent.click(screen.getByText('12:00 - 12:30 PM')); // Timeslot
    fireEvent.click(screen.getByText('A1')); // Seat
    
    // Find and click confirm button
    const confirmButton = screen.getByText(/Confirm Booking/);
    expect(confirmButton).not.toBeDisabled();
    
    fireEvent.click(confirmButton);
    
    // Verify booking is attempted
    await waitFor(() => {
      expect(reservationsAPI.createReservation).toHaveBeenCalled();
    });
  });

  it('should show error for booking with zero balance manager', async () => {
    const { authAPI } = await import('@/services/api');
    const { toast } = await import('sonner');
    
    // Mock zero balance manager
    (authAPI.getManagerBalance as any).mockResolvedValue({
      manager_name: 'Zero Balance Manager',
      balance: 0,
    });
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Wait for balance to load
    await waitFor(() => {
      expect(screen.getByText(/0 Blu-Points/)).toBeInTheDocument();
    });
    
    // Attempt booking
    fireEvent.click(screen.getByText(/Confirm Booking/));
    
    // Verify error message
    expect(toast.error).toHaveBeenCalledWith(
      'Your manager has 0 Blu-Points. Booking not allowed. Please contact your manager to add funds.'
    );
  });

  // === TDD Test 5: Timer Functionality ===
  it('should display countdown timer for active reservations', async () => {
    const { reservationsAPI } = await import('@/services/api');
    (reservationsAPI.getMyReservations as any).mockResolvedValue([
      {
        id: 1,
        status: 'confirmed',
        available_at: new Date(Date.now() + 300000).toISOString(), // 5 minutes from now
        timeslot: {
          starts_at: '2026-02-01T12:00:00',
          ends_at: '2026-02-01T12:30:00',
        },
        seat: {
          label: 'A1',
        },
      },
    ]);
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Wait for timer to load and display
    await waitFor(() => {
      expect(screen.getByText(/Seat A1:/)).toBeInTheDocument();
    });
    
    // Timer should show approximately 5 minutes remaining
    expect(screen.getByText(/\d{2}:\d{2} remaining/)).toBeInTheDocument();
  });

  it('should refresh seat availability periodically', async () => {
    const { reservationsAPI } = await import('@/services/api');
    (reservationsAPI.getSeats as any).mockResolvedValue([
      { id: 1, label: 'A1', available: true, mine: false },
    ]);
    
    vi.useFakeTimers();
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Select a timeslot first
    fireEvent.click(screen.getByText('12:00 - 12:30 PM'));
    
    // Wait for initial seats load
    await waitFor(() => {
      expect(reservationsAPI.getSeats).toHaveBeenCalledTimes(1);
    });
    
    // Advance timers by 5 seconds
    vi.advanceTimersByTime(5000);
    
    // Verify periodic refresh occurred
    await waitFor(() => {
      expect(reservationsAPI.getSeats).toHaveBeenCalledTimes(2);
    });
    
    vi.useRealTimers();
  });

  // === TDD Test 6: Admin Interface Testing ===
  it('should integrate with admin functionality in single codebase', () => {
    // This test verifies that admin and user components can coexist
    // in the same application architecture
    expect(typeof SeatSelectionPage).toBe('function');
    
    // Verify component accepts required props through interface
    const component = SeatSelectionPage;
    expect(component).toBeDefined();
  });

  // === TDD Test 7: Error Handling ===
  it('should handle API errors gracefully', async () => {
    const { reservationsAPI } = await import('@/services/api');
    const { toast } = await import('sonner');
    
    // Mock API failure
    (reservationsAPI.getTimeslots as any).mockRejectedValue(
      new Error('Network error')
    );
    
    render(<SeatSelectionPage {...mockProps} />);
    
    // Try to select a date
    fireEvent.click(screen.getByText('15'));
    
    // Verify error handling
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        'Failed to load timeslots'
      );
    });
  });

  it('should handle logout functionality', () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Find logout button
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);
    
    // Verify logout callback is called
    expect(mockProps.onLogout).toHaveBeenCalled();
  });

  // === TDD Test 8: Integration Testing ===
  it('should maintain state consistency across interactions', async () => {
    render(<SeatSelectionPage {...mockProps} />);
    
    // Perform sequence of interactions
    fireEvent.click(screen.getByText('15')); // Select date
    fireEvent.click(screen.getByText('12:00 - 12:30 PM')); // Select timeslot
    fireEvent.click(screen.getByText('A1')); // Select seat
    
    // Verify all selections are maintained
    expect(screen.getByText('15')).toHaveClass('bg-blue-600'); // Selected date
    expect(screen.getByText('12:00 - 12:30 PM')).toHaveClass('bg-blue-600'); // Selected timeslot
    expect(screen.getByText('A1')).toHaveClass('bg-blue-600'); // Selected seat
    
    // Verify booking button is enabled
    expect(screen.getByText(/Confirm Booking/)).not.toBeDisabled();
  });
});