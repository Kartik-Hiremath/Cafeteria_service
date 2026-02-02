// API Configuration
const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000';

export interface User {
  id: number;
  employee_uid: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  manager_name: string | null;
}

export interface Timeslot {
  id: number;
  starts_at: string;
  ends_at: string;
}

export interface Seat {
  id: number;
  label: string;
  available: boolean;
  mine: boolean;
}

export interface Reservation {
  id: number;
  user_id: number;
  seat_id: number;
  timeslot_id: number;
  status: string;
  created_at: string;
  available_at?: string;
  seat: Seat;
  timeslot: Timeslot;
}

export interface CreateReservationRequest {
  seat_id: number;
  timeslot_id: number;
}

// Helper function to make API calls with credentials
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    credentials: 'include', // Important for cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Manager interface
export interface Manager {
  name: string;
  balance: number;
}

// Auth API
export const authAPI = {
  // Redirect to login (this will redirect to OIDC)
  login: () => {
    window.location.href = `${API_BASE_URL}/auth/login`;
  },

  // Get list of managers
  getManagers: (): Promise<Manager[]> => {
    return apiCall<Manager[]>('/auth/managers');
  },

  // Get current user
  getMe: (): Promise<User> => {
    return apiCall<User>('/auth/me');
  },

  // Get manager balance
  getManagerBalance: (): Promise<{ manager_name: string; balance: number }> => {
    return apiCall<{ manager_name: string; balance: number }>('/auth/manager-balance');
  },

  // Logout
  logout: (): Promise<{ message: string }> => {
    return apiCall<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
  },
};

// Reservations API
export const reservationsAPI = {
  // Get timeslots for a date
  getTimeslots: (date: string): Promise<Timeslot[]> => {
    return apiCall<Timeslot[]>(`/reservations/timeslots?date=${date}`);
  },

  // Get seats for a timeslot
  getSeats: (timeslotId: number): Promise<Seat[]> => {
    return apiCall<Seat[]>(`/reservations/seats?timeslot_id=${timeslotId}`);
  },

  // Get my reservations
  getMyReservations: (): Promise<Reservation[]> => {
    return apiCall<Reservation[]>('/reservations/mine');
  },

  // Create reservation
  createReservation: (data: CreateReservationRequest): Promise<Reservation> => {
    return apiCall<Reservation>('/reservations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// Type declaration for import.meta.env
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
