import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { CheckCircle2, Home, LogOut, Calendar, Clock, Users, DollarSign } from "lucide-react";
import { BookingDetails } from "./seat-selection-page";

interface BookingSuccessPageProps {
  bookingDetails: BookingDetails;
  onBackToDashboard: () => void;
  onLogout: () => void;
}

export function BookingSuccessPage({
  bookingDetails,
  onBackToDashboard,
  onLogout,
}: BookingSuccessPageProps) {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg"></div>
            <h1 className="text-xl font-medium text-gray-900">Riviera Booking</h1>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-6 py-12">
        <Card className="p-8 rounded-3xl shadow-sm border-gray-100">
          {/* Success Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle2 className="w-12 h-12 text-green-600" />
            </div>
          </div>

          {/* Success Message */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-medium text-gray-900 mb-2">
              Booking Confirmed!
            </h1>
            <p className="text-base text-gray-600">
              Your reservation has been successfully confirmed
            </p>
          </div>

          {/* Booking Details Cards */}
          <div className="space-y-3 mb-8">
            {/* Date & Time */}
            <div className="p-4 rounded-2xl bg-blue-50 border border-blue-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Calendar className="h-5 w-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-600 mb-0.5">Date & Time</p>
                  <p className="text-sm font-medium text-gray-900">
                    {bookingDetails.date} at {bookingDetails.timeSlot}
                  </p>
                </div>
              </div>
            </div>

            {/* Seats */}
            <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                  <Users className="h-5 w-5 text-gray-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-600 mb-0.5">Reserved Seats</p>
                  <p className="text-sm font-medium text-gray-900">
                    {bookingDetails.quantity} {bookingDetails.quantity === 1 ? 'seat' : 'seats'} (#{bookingDetails.seats.join(", #")})
                  </p>
                </div>
              </div>
            </div>

            {/* Cost */}
            <div className="p-4 rounded-2xl bg-green-50 border border-green-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-600 mb-0.5">Total Amount</p>
                  <p className="text-sm font-medium text-gray-900">
                    ${bookingDetails.totalCost.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="space-y-3 mb-8">
            <div className="p-4 rounded-xl bg-blue-50 border border-blue-100 text-center">
              <p className="text-sm text-gray-700">
                ✉️ Confirmation email sent to your inbox
              </p>
            </div>
            <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 text-center">
              <p className="text-sm text-gray-700">
                💳 Charged to manager's budget
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={onBackToDashboard}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-sm text-base font-medium transition-all"
            >
              <Home className="mr-2 h-5 w-5" />
              Make Another Booking
            </Button>

            <Button
              onClick={onLogout}
              variant="outline"
              className="w-full h-12 border-gray-300 text-gray-700 hover:bg-gray-50 rounded-xl text-base font-medium transition-all"
            >
              <LogOut className="mr-2 h-5 w-5" />
              Logout
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
