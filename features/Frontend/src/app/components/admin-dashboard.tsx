import { useState, useEffect } from "react";
import { Card } from "@/app/components/ui/card";
import { Button } from "@/app/components/ui/button";
import { RefreshCw, TrendingUp, Users, DollarSign, Calendar, RotateCcw } from "lucide-react";
import { toast } from "sonner";

interface DashboardData {
  active_reservations: Array<{
    id: number;
    user_email: string;
    user_name: string;
    seat_label: string;
    timeslot_start: string;
    timeslot_end: string;
    created_at: string;
    available_at?: string;
    manager_name: string;
  }>;
  managers: Array<{
    id: number;
    name: string;
    balance: number;
  }>;
  recent_charges: Array<{
    id: number;
    manager_name: string;
    amount: number;
    created_at: string;
    reservation_id: number;
  }>;
  seat_occupancy: Array<{
    id: number;
    label: string;
    active_reservations: number;
    is_occupied: boolean;
  }>;
  statistics: {
    total_active_reservations: number;
    bookings_today: number;
    total_revenue: number;
    most_booked_seats: Array<{
      seat: string;
      bookings: number;
    }>;
  };
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [bookingsByDate, setBookingsByDate] = useState<any>(null);
  const [bookingsLoading, setBookingsLoading] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
        credentials: 'include',
      });
      if (response.ok) {
        const dashboardData = await response.json();
        setData(dashboardData);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBookingsData = async () => {
    setBookingsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/bookings`, {
        credentials: 'include',
      });
      if (response.ok) {
        const bookingsData = await response.json();
        setBookingsByDate(bookingsData);
      }
    } catch (error) {
      console.error('Failed to fetch bookings data:', error);
    } finally {
      setBookingsLoading(false);
    }
  };

  const resetSystem = async () => {
    if (window.confirm('Are you sure you want to reset the entire system? This will cancel all bookings and restore all manager balances.')) {
      try {
        const response = await fetch(`${API_BASE_URL}/admin/reset`, {
          method: 'POST',
          credentials: 'include',
        });
        if (response.ok) {
          const result = await response.json();
          toast.success(`System reset: ${result.cancelled_reservations} reservations cancelled, ${result.restored_managers} managers restored.`);
          // Refresh all data
          fetchDashboardData();
          fetchBookingsData();
        } else {
          toast.error('Failed to reset system');
        }
      } catch (error) {
        console.error('Reset error:', error);
        toast.error('Failed to reset system');
      }
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchBookingsData();
    // Auto-refresh every 3 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchBookingsData();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load dashboard data</p>
          <Button onClick={fetchDashboardData}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-600 mt-1">
              Real-time booking visualization and analytics
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
            <Button onClick={fetchDashboardData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
          <Card className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Active Reservations</p>
                <p className="text-3xl font-bold mt-1">{data.statistics.total_active_reservations}</p>
              </div>
              <Users className="h-8 w-8 text-blue-200" />
            </div>
          </Card>

          <Card className="p-4 bg-gradient-to-br from-green-500 to-green-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Bookings Today</p>
                <p className="text-3xl font-bold mt-1">{data.statistics.bookings_today}</p>
              </div>
              <Calendar className="h-8 w-8 text-green-200" />
            </div>
          </Card>

          <Card className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Total Revenue</p>
                <p className="text-3xl font-bold mt-1">{data.statistics.total_revenue.toFixed(2)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-purple-200" />
            </div>
          </Card>

          <Card className="p-4 bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100 text-sm">Managers</p>
                <p className="text-3xl font-bold mt-1">{data.managers.length}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-200" />
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Seat Grid Visualization */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Seat Occupancy (100 Seats)</h2>
            <div className="grid grid-cols-5 sm:grid-cols-10 gap-1 sm:gap-2 max-h-64 sm:max-h-96 overflow-y-auto">
              {data.seat_occupancy.map((seat) => (
                <div
                  key={seat.id}
                  className={`aspect-square rounded-lg flex items-center justify-center text-xs font-medium transition-all ${
                    seat.is_occupied
                      ? "bg-red-500 text-white"
                      : "bg-green-200 text-green-800"
                  }`}
                  title={`${seat.label}: ${seat.is_occupied ? "Occupied" : "Available"}`}
                >
                  {seat.label}
                </div>
              ))}
            </div>
            <div className="mt-4 flex gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-green-200"></div>
                <span>Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-red-500"></div>
                <span>Occupied</span>
              </div>
            </div>
          </Card>

          {/* Manager Balances */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Manager Balances</h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {data.managers.map((manager) => {
                const maxBalance = Math.max(...data.managers.map(m => m.balance));
                const percentage = (manager.balance / maxBalance) * 100;
                return (
                  <div key={manager.id} className="border rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-gray-900">{manager.name}</span>
                      <span className="text-sm font-semibold text-blue-600">
                        {manager.balance.toLocaleString()} Blu-Points
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          manager.balance > 50000
                            ? "bg-green-500"
                            : manager.balance > 10000
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Reservations */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Active Reservations</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {data.active_reservations.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No active reservations</p>
              ) : (
                data.active_reservations.map((res) => (
                  <div
                    key={res.id}
                    className="border rounded-lg p-3 bg-blue-50 hover:bg-blue-100 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-medium text-gray-900">{res.user_name}</p>
                        <p className="text-sm text-gray-600">{res.user_email}</p>
                      </div>
                      <span className="px-2 py-1 bg-blue-600 text-white text-xs font-medium rounded">
                        {res.seat_label}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 space-y-1">
                      <p>
                        Time: {new Date(res.timeslot_start).toLocaleTimeString()} -{" "}
                        {new Date(res.timeslot_end).toLocaleTimeString()}
                      </p>
                      <p>Manager: {res.manager_name}</p>
                      {res.available_at && (
                        <p className="text-xs text-gray-500">Available: {new Date(res.available_at).toLocaleTimeString()}</p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Recent Charges */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Charges</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {data.recent_charges.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No recent charges</p>
              ) : (
                data.recent_charges.map((charge) => (
                  <div
                    key={charge.id}
                    className="border rounded-lg p-3 bg-green-50 hover:bg-green-100 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900">{charge.manager_name}</p>
                        <p className="text-xs text-gray-600">
                          {new Date(charge.created_at).toLocaleString()}
                        </p>
                      </div>
                      <span className="text-lg font-bold text-green-600">
                        -{charge.amount.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Most Booked Seats */}
        {data.statistics.most_booked_seats.length > 0 && (
          <Card className="p-6 mt-6">
            <h2 className="text-xl font-semibold mb-4">Most Booked Seats</h2>
            <div className="grid grid-cols-5 gap-4">
              {data.statistics.most_booked_seats.map((item, index) => (
                <div
                  key={item.seat}
                  className="border rounded-lg p-3 text-center bg-gradient-to-br from-purple-50 to-purple-100"
                >
                  <div className="text-2xl font-bold text-purple-600 mb-1">
                    #{index + 1}
                  </div>
                  <div className="text-lg font-semibold text-gray-900">{item.seat}</div>
                  <div className="text-sm text-gray-600">{item.bookings} bookings</div>
                </div>
              ))}
            </div>
          </Card>
        )}
        
        {/* Today & Tomorrow Bookings */}
        <Card className="p-6 mt-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Today & Tomorrow Bookings</h2>
            {bookingsLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            ) : (
              <Button onClick={() => fetchBookingsData()} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            )}
          </div>
          
          {bookingsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p>Loading bookings...</p>
            </div>
          ) : bookingsByDate ? (
            <div className="space-y-6">
              {bookingsByDate.dates.map((date: string) => (
                <div key={date}>
                  <h3 className="text-lg font-medium mb-3 text-gray-700">{new Date(date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {bookingsByDate.bookings_by_date[date]?.map((timeslot: any) => (
                      <div key={timeslot.id} className="border rounded-lg p-4 bg-white">
                        <div className="font-medium">{timeslot.time_range}</div>
                        <div className="text-sm text-gray-600 mt-1">{timeslot.reservations_count} reservation{timeslot.reservations_count !== 1 ? 's' : ''}</div>
                        <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                          {timeslot.reservations?.slice(0, 5).map((res: any) => (
                            <div key={res.id} className="text-xs bg-gray-50 p-1 rounded">
                              <span className="font-medium">{res.seat_label}</span> - {res.user_name} ({res.manager_name})
                            </div>
                          ))}
                          {timeslot.reservations && timeslot.reservations.length > 5 && (
                            <div className="text-xs text-gray-500">+{timeslot.reservations.length - 5} more</div>
                          )}
                        </div>
                      </div>
                    )) || <p className="text-gray-500 col-span-3 text-center py-4">No bookings for this date</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No booking data available</p>
          )}
        </Card>
        
        {/* Reset System Button */}
        <div className="mt-6 flex justify-center">
          <Button onClick={resetSystem} variant="destructive" className="bg-red-600 hover:bg-red-700">
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset System (Cancel All Bookings & Restore Balances)
          </Button>
        </div>
      </div>
    </div>
  );
}
