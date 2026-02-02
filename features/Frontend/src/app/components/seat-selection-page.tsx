import { useState, useEffect } from "react";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { ChevronLeft, ChevronRight, User, Loader2, Clock, DollarSign } from "lucide-react";
import { reservationsAPI, Timeslot, Seat, Reservation, authAPI } from "@/services/api";
import { toast } from "sonner";

interface SeatSelectionPageProps {
  onConfirmBooking: (bookingDetails: BookingDetails) => void;
  onLogout: () => void;
}

export interface BookingDetails {
  seats: number[];
  timeSlot: string;
  quantity: number;
  totalCost: number;
  date: string;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// Table configuration: 20 tables with varying seats (total 100 seats)
const TABLE_CONFIG: Record<number, number> = {
  1: 2, 2: 4, 3: 6, 4: 4, 5: 2,
  6: 6, 7: 4, 8: 2, 9: 4, 10: 6,
  11: 2, 12: 4, 13: 6, 14: 4, 15: 2,
  16: 6, 17: 4, 18: 2, 19: 4, 20: 6,
};

// Map backend seats (A1-J10) to table structure
function mapSeatsToTables(backendSeats: Seat[]): Map<number, Seat[]> {
  const tableMap = new Map<number, Seat[]>();
  let seatIndex = 0;
  
  for (let tableNum = 1; tableNum <= 20; tableNum++) {
    const seatCount = TABLE_CONFIG[tableNum];
    const tableSeats: Seat[] = [];
    
    for (let i = 0; i < seatCount && seatIndex < backendSeats.length; i++) {
      tableSeats.push(backendSeats[seatIndex]);
      seatIndex++;
    }
    
    if (tableSeats.length > 0) {
      tableMap.set(tableNum, tableSeats);
    }
  }
  
  return tableMap;
}

export function SeatSelectionPage({ onConfirmBooking, onLogout }: SeatSelectionPageProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
  const [selectedTimeslot, setSelectedTimeslot] = useState<number | null>(null);
  const [backendSeats, setBackendSeats] = useState<Seat[]>([]);
  const [selectedSeatIds, setSelectedSeatIds] = useState<Set<number>>(new Set());
  const [loadingTimeslots, setLoadingTimeslots] = useState(false);
  const [loadingSeats, setLoadingSeats] = useState(false);
  const [booking, setBooking] = useState(false);
  const [managerBalance, setManagerBalance] = useState<{ manager_name: string; balance: number } | null>(null);
  const [activeReservations, setActiveReservations] = useState<Reservation[]>([]);
  const [timeRemaining, setTimeRemaining] = useState<{ minutes: number; seconds: number; seatLabel: string; timeslot: string } | null>(null);

  // Fetch timeslots when date is selected
  useEffect(() => {
    if (selectedDate) {
      setLoadingTimeslots(true);
      const dateStr = selectedDate.toISOString().split('T')[0];
      reservationsAPI.getTimeslots(dateStr)
        .then(setTimeslots)
        .catch((error) => {
          toast.error(error.message || 'Failed to load timeslots');
          setTimeslots([]);
        })
        .finally(() => setLoadingTimeslots(false));
    } else {
      setTimeslots([]);
      setSelectedTimeslot(null);
    }
  }, [selectedDate]);

  // Fetch seats when timeslot is selected
  useEffect(() => {
    if (selectedTimeslot) {
      setLoadingSeats(true);
      setSelectedSeatIds(new Set());
      reservationsAPI.getSeats(selectedTimeslot)
        .then(setBackendSeats)
        .catch((error) => {
          toast.error(error.message || 'Failed to load seats');
          setBackendSeats([]);
        })
        .finally(() => setLoadingSeats(false));
    } else {
      setBackendSeats([]);
    }
  }, [selectedTimeslot]);

  // Fetch manager balance on mount
  useEffect(() => {
    authAPI.getManagerBalance()
      .then(setManagerBalance)
      .catch((error) => {
        console.error('Failed to fetch manager balance:', error);
      });
  }, []);

  // Fetch active reservations for timer
  useEffect(() => {
    const fetchReservations = () => {
      reservationsAPI.getMyReservations()
        .then(setActiveReservations)
        .catch((error) => {
          console.error('Failed to fetch reservations:', error);
        });
    };
    
    fetchReservations();
    const interval = setInterval(fetchReservations, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Calculate time remaining for active reservations based on the 5-minute timer
  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const activeRes = activeReservations
        .filter(r => r.status === 'confirmed')
        .find(r => {
          // Check if reservation has available_at set (5-minute timer)
          if (r.available_at) {
            const availableAt = new Date(r.available_at);
            return availableAt > now;
          }
          return false;
        });

      if (activeRes) {
        const availableAt = new Date(activeRes.available_at);
        const diff = availableAt.getTime() - now.getTime();
        
        if (diff > 0) {
          const minutes = Math.floor(diff / 60000);
          const seconds = Math.floor((diff % 60000) / 1000);
          const startTime = new Date(activeRes.timeslot.starts_at);
          const endTime = new Date(activeRes.timeslot.ends_at);
          const timeslotStr = `${startTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} - ${endTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
          
          setTimeRemaining({
            minutes,
            seconds,
            seatLabel: activeRes.seat.label,
            timeslot: timeslotStr
          });
        } else {
          setTimeRemaining(null);
        }
      } else {
        setTimeRemaining(null);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000); // Update every second
    return () => clearInterval(interval);
  }, [activeReservations]);

  // Auto-refresh seats every 5 seconds to show real-time updates
  useEffect(() => {
    if (!selectedTimeslot) return;
    
    const interval = setInterval(() => {
      reservationsAPI.getSeats(selectedTimeslot)
        .then(setBackendSeats)
        .catch((error) => {
          console.error('Failed to refresh seats:', error);
        });
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [selectedTimeslot]);

  const getDaysInMonth = (date: Date) => ({
    daysInMonth: new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate(),
    startingDayOfWeek: new Date(date.getFullYear(), date.getMonth(), 1).getDay(),
  });

  const { daysInMonth, startingDayOfWeek } = getDaysInMonth(currentDate);

  const formatTimeslot = (timeslot: Timeslot) => {
    const start = new Date(timeslot.starts_at);
    const end = new Date(timeslot.ends_at);
    return `${start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} - ${end.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
  };

  const handleSeatClick = (seatId: number) => {
    // One seat per user: check active reservations
    const userActiveReservationsCount = activeReservations.filter(
      (r) => r.status === "confirmed" && new Date(r.timeslot.ends_at) > new Date()
    ).length;

    if (userActiveReservationsCount >= 1 && !selectedSeatIds.has(seatId)) {
      toast.error("You can only book one seat. Cancel your existing reservation first.");
      return;
    }

    // Max 1 seat selection
    if (selectedSeatIds.size >= 1 && !selectedSeatIds.has(seatId)) {
      toast.error("You can only select one seat.");
      return;
    }

    setSelectedSeatIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(seatId)) {
        newSet.delete(seatId);
      } else {
        newSet.clear();
        newSet.add(seatId);
      }
      return newSet;
    });
  };

  const handleConfirm = async () => {
    if (!selectedDate || !selectedTimeslot || selectedSeatIds.size === 0) {
      toast.error('Please select date, timeslot, and at least one seat');
      return;
    }

    if (selectedSeatIds.size > 1) {
      toast.error("You can only book one seat.");
      return;
    }
    
    // Check if manager has zero balance
    if (managerBalance && managerBalance.balance === 0) {
      toast.error('Your manager has 0 Blu-Points. Booking not allowed. Please contact your manager to add funds.');
      return;
    }

    const seatId = Array.from(selectedSeatIds)[0];
    setBooking(true);
    
    try {
      const reservation = await reservationsAPI.createReservation({
        seat_id: seatId,
        timeslot_id: selectedTimeslot,
      });

      const selectedTimeslotData = timeslots.find(t => t.id === selectedTimeslot);
      const selectedSeat = backendSeats.find(s => s.id === seatId);

      // Refresh seats to show updated availability
      await reservationsAPI.getSeats(selectedTimeslot).then(setBackendSeats);
      
      // Refresh manager balance and reservations
      authAPI.getManagerBalance().then(setManagerBalance);
      reservationsAPI.getMyReservations().then(setActiveReservations);

      onConfirmBooking({
        seats: [seatId],
        timeSlot: selectedTimeslotData ? formatTimeslot(selectedTimeslotData) : '',
        quantity: 1,
        totalCost: 10.00,
        date: selectedDate.toDateString(),
      });

      toast.success('Booking confirmed! 10 Blu-Dollars charged to manager account.');
    } catch (error: any) {
      console.error('Booking error:', error);
      if (error.message.includes('409') || error.message.includes('conflict')) {
        toast.error('Seat or timeslot already reserved. Please select another.');
        // Refresh seats to show current availability
        reservationsAPI.getSeats(selectedTimeslot).then(setBackendSeats);
      } else if (error.message.includes("402")) {
        toast.error("Insufficient manager balance. Please contact your manager to add funds.");
      } else if (error.message.includes("400") || error.message.includes("one seat")) {
        toast.error("You can only book one seat. Cancel your existing reservation first.");
        reservationsAPI.getMyReservations().then(setActiveReservations);
      } else {
        toast.error(error.message || "Booking failed. Please try again.");
      }
    } finally {
      setBooking(false);
    }
  };

  // Map backend seats to tables
  const tableMap = mapSeatsToTables(backendSeats);
  const allTables = Array.from({ length: 20 }, (_, i) => {
    const tableNum = i + 1;
    return tableMap.get(tableNum) || [];
  });
  const groundFloorTables = allTables.slice(0, 10);
  const firstFloorTables = allTables.slice(10);

  const renderFloor = (title: string, tables: Seat[][]) => (
    <div className="mb-6 sm:mb-10">
      <h3 className="text-sm sm:text-base font-semibold text-gray-700 mb-3 sm:mb-4">{title}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        {tables.map((tableSeats, idx) => {
          const tableNo = idx + (title === "Ground Floor" ? 1 : 11);
          const hasSelected = tableSeats.some(s => selectedSeatIds.has(s.id));
          const hasMine = tableSeats.some(s => s.mine);

          if (tableSeats.length === 0) return null;

          return (
            <div
              key={tableNo}
              className={`p-4 rounded-2xl border-2 ${
                hasSelected || hasMine
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 bg-white"
              }`}
            >
              <p className="text-xs text-gray-500 text-center mb-2">
                Table {tableNo} · {tableSeats.length} seats
              </p>
              <div
                className={`grid gap-2 ${
                  tableSeats.length <= 2
                    ? "grid-cols-2"
                    : tableSeats.length <= 4
                      ? "grid-cols-2"
                      : "grid-cols-3"
                }`}
              >
                {tableSeats.map((seat) => {
                  const isSelected = selectedSeatIds.has(seat.id);
                  const isMine = seat.mine;
                  const isAvailable = seat.available;

                  return (
                  <button
                    key={seat.id}
                    onClick={() => handleSeatClick(seat.id)}
                      disabled={!isAvailable && !isMine}
                      className={`h-10 rounded-lg text-xs font-medium transition-all ${
                        isSelected
                          ? "bg-blue-600 text-white scale-105 shadow-md"
                          : isMine
                          ? "bg-green-600 text-white"
                          : isAvailable
                          ? "bg-blue-100 text-blue-700 hover:bg-blue-200"
                          : "bg-gray-200 text-gray-500 cursor-not-allowed"
                      }`}
                    >
                      {seat.label}
                  </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b px-4 sm:px-6 py-3 sm:py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
          <h1 className="text-xl font-medium">Riviera Booking</h1>
          <div className="flex items-center gap-4">
            {/* Manager Balance */}
            {managerBalance && (
              <div className="flex items-center gap-2 text-sm bg-blue-50 px-3 py-1.5 rounded-lg">
                <DollarSign className="h-4 w-4 text-blue-600" />
                <span className="text-gray-700">
                  <span className="font-medium">{managerBalance.manager_name}</span>
                  {' '}| Balance: <span className="font-semibold text-blue-600">{managerBalance.balance.toLocaleString()}</span> Blu-Points
                </span>
              </div>
            )}
            
            {/* Timeslot Timer */}
            {timeRemaining && (
              <div className={`flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg ${
                timeRemaining.minutes < 1 
                  ? timeRemaining.seconds < 30 
                    ? 'bg-red-50 text-red-700' 
                    : 'bg-yellow-50 text-yellow-700'
                  : 'bg-green-50 text-green-700'
              }`}>
                <Clock className="h-4 w-4" />
                <span className="font-medium">
                  Seat {timeRemaining.seatLabel}: {String(timeRemaining.minutes).padStart(2, '0')}:{String(timeRemaining.seconds).padStart(2, '0')} remaining
                </span>
              </div>
            )}
            
          <Button variant="ghost" onClick={onLogout}>
            <User className="mr-2 h-4 w-4" /> Logout
          </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8 grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-8">
        <Card className="p-6 rounded-3xl">
          <h2 className="mb-6 text-lg font-medium">Booking details</h2>

          <div className="mb-6">
            <div className="flex justify-between mb-3">
              <ChevronLeft
                className="cursor-pointer"
                onClick={() =>
                  setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))
                }
              />
              <span>
                {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
              </span>
              <ChevronRight
                className="cursor-pointer"
                onClick={() =>
                  setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))
                }
              />
            </div>

            <div className="grid grid-cols-7 gap-2">
              {DAYS.map((d) => (
                <div key={d} className="text-xs text-center text-gray-500">
                  {d}
                </div>
              ))}
              {Array.from({ length: startingDayOfWeek }).map((_, i) => (
                  <div key={i} />
              ))}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                  const day = i + 1;
                const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
                  const active =
                    selectedDate?.getDate() === day &&
                  selectedDate?.getMonth() === currentDate.getMonth();
                
                // Today and tomorrow only
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const tomorrow = new Date(today);
                tomorrow.setDate(tomorrow.getDate() + 1);
                const dateToCheck = new Date(date);
                dateToCheck.setHours(0, 0, 0, 0);
                const isToday =
                  dateToCheck.getTime() === today.getTime();
                const isTomorrow =
                  dateToCheck.getTime() === tomorrow.getTime();
                const isSelectable = isToday || isTomorrow;

                  return (
                    <button
                      key={day}
                    onClick={() => isSelectable && setSelectedDate(date)}
                    disabled={!isSelectable}
                    className={`aspect-square rounded-xl text-sm ${
                      !isSelectable
                        ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                        : active
                          ? "bg-blue-600 text-white"
                        : "hover:bg-gray-100 text-gray-700"
                      }`}
                    >
                      {day}
                    </button>
                  );
              })}
            </div>
          </div>

          {selectedDate && (
            <div className="mb-6">
              <label className="block mb-2 text-sm font-medium">Select time slot</label>
              {loadingTimeslots ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          </div>
              ) : timeslots.length === 0 ? (
                <p className="text-sm text-gray-500 py-4">No timeslots available for this date</p>
              ) : (
                <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto">
                  {timeslots.map((timeslot) => (
                    <button
                      key={timeslot.id}
                      onClick={() => setSelectedTimeslot(timeslot.id)}
                      className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                        selectedTimeslot === timeslot.id
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                      }`}
                    >
                      {formatTimeslot(timeslot)}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <Button
            onClick={handleConfirm}
            disabled={!selectedDate || !selectedTimeslot || selectedSeatIds.size === 0 || booking}
            className="w-full"
          >
            {booking ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Booking...
              </>
            ) : (
              `Confirm Booking (${selectedSeatIds.size} seat${selectedSeatIds.size !== 1 ? 's' : ''})`
            )}
          </Button>
        </Card>

        <Card className="p-4 sm:p-6 rounded-3xl overflow-y-auto max-h-[600px] sm:max-h-[750px]">
          <h2 className="text-lg font-medium mb-2">Choose table</h2>
          <p className="text-sm text-gray-600 mb-4">Two-storey cafeteria layout</p>

          <div className="flex items-center gap-4 mb-4 pb-4 border-b">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-blue-100 border border-blue-200"></div>
              <span className="text-xs text-gray-600">Available</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gray-200"></div>
              <span className="text-xs text-gray-600">Booked</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-green-600"></div>
              <span className="text-xs text-gray-600">Mine</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-blue-600"></div>
              <span className="text-xs text-gray-600">Selected</span>
            </div>
          </div>

          {!selectedTimeslot ? (
            <div className="text-center py-12 text-gray-500">
              Select a date and timeslot to view seats
            </div>
          ) : loadingSeats ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : (
            <>
          {renderFloor("Ground Floor", groundFloorTables)}
          {renderFloor("First Floor", firstFloorTables)}
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
