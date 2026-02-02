import { useState, useEffect } from "react";
import { LoginPage } from "@/app/components/login-page";
import { SeatSelectionPage, BookingDetails } from "@/app/components/seat-selection-page";
import { BookingSuccessPage } from "@/app/components/booking-success-page";
import { AdminDashboard } from "@/app/components/admin-dashboard";
import { authAPI } from "@/services/api";

type Screen = "login" | "seat-selection" | "success" | "loading" | "admin";

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>("loading");
  const [bookingDetails, setBookingDetails] = useState<BookingDetails | null>(null);
  const [user, setUser] = useState<any>(null);

  // Check if admin route first
  useEffect(() => {
    if (window.location.pathname === '/admin' || window.location.pathname === '/admin/dashboard') {
      setCurrentScreen('admin');
      return;
    }
    // Otherwise check authentication
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const userData = await authAPI.getMe();
      setUser(userData);
      setCurrentScreen("seat-selection");
    } catch (error) {
      // Not authenticated or API error - show login page
      console.log("Auth check failed, showing login:", error);
      setCurrentScreen("login");
    }
  };

  const handleLogin = () => {
    // This will be handled by OIDC redirect
    checkAuth();
  };

  const handleConfirmBooking = (details: BookingDetails) => {
    setBookingDetails(details);
    setCurrentScreen("success");
  };

  const handleBackToDashboard = () => {
    setCurrentScreen("seat-selection");
    setBookingDetails(null);
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error("Logout error:", error);
    }
    setUser(null);
    setCurrentScreen("login");
    setBookingDetails(null);
  };

  if (currentScreen === "loading") {
    return (
      <div className="w-full min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen">
      {currentScreen === "login" && <LoginPage onLogin={handleLogin} />}
      
      {currentScreen === "seat-selection" && (
        <SeatSelectionPage
          onConfirmBooking={handleConfirmBooking}
          onLogout={handleLogout}
        />
      )}
      
      {currentScreen === "success" && bookingDetails && (
        <BookingSuccessPage
          bookingDetails={bookingDetails}
          onBackToDashboard={handleBackToDashboard}
          onLogout={handleLogout}
        />
      )}
      
      {currentScreen === "admin" && <AdminDashboard />}
    </div>
  );
}
