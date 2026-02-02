import { useState, useEffect } from "react";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import {
  ShieldCheck,
  KeyRound,
  ArrowRight,
  X,
  UserCircle,
} from "lucide-react";
import { ImageWithFallback } from "@/app/components/figma/ImageWithFallback";
import rivieraImage from "@/assets/riviera-preview.png";
import { authAPI } from "@/services/api";

interface LoginPageProps {
  onLogin: () => void;
}

interface Manager {
  name: string;
  balance: number;
}

const EMPLOYEES = [
  "emp001", "emp002", "emp003", "emp004", "emp005",
  "emp006", "emp007", "emp008", "emp009", "emp010",
];

export function LoginPage({ onLogin }: LoginPageProps) {
  const [showDummyModal, setShowDummyModal] = useState(false);
  const [managers, setManagers] = useState<Manager[]>([]);
  const [selectedManager, setSelectedManager] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState("");

  useEffect(() => {
    if (showDummyModal) {
      authAPI.getManagers()
        .then(setManagers)
        .catch((error) => {
          console.error("Failed to fetch managers:", error);
        });
    }
  }, [showDummyModal]);

  // Real W3ID: redirect to backend, which redirects to IBM SSO
  const handleRealW3IDLogin = () => {
    const loginUrl = `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/auth/login`;
    window.location.href = loginUrl;
  };

  // Dummy W3ID: open modal to select manager + employee
  const handleDummyW3IDClick = () => {
    setShowDummyModal(true);
  };

  const handleDummyLogin = () => {
    if (!selectedManager) {
      alert("Please select a manager");
      return;
    }
    if (!selectedEmployee) {
      alert("Please select an employee");
      return;
    }
    const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const loginUrl = `${baseUrl}/auth/login?mode=dummy&manager_name=${encodeURIComponent(selectedManager)}&employee_id=${encodeURIComponent(selectedEmployee)}`;
    window.location.href = loginUrl;
  };

  return (
    <div className="min-h-screen bg-white flex flex-col lg:flex-row">
      {/* Left Side - Preview Image */}
      <div className="hidden lg:block lg:w-1/2 relative bg-white">
        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="w-full max-w-[90%] lg:min-h-[720px] flex items-center">
            <ImageWithFallback
              src={rivieraImage}
              alt="Riviera IBM Cafeteria"
              className="w-full h-full object-cover object-center filter brightness-95 rounded-lg shadow-lg"
            />
          </div>
        </div>
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-white/90 pointer-events-none" />
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8">
        <div className="w-full max-w-md lg:ml-8">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-600 rounded-xl"></div>
              <h1 className="text-2xl font-medium text-gray-900">Riviera Booking</h1>
            </div>
            <h2 className="text-3xl font-medium text-gray-900 mb-2">Welcome back</h2>
            <p className="text-base text-gray-600">Sign in to reserve your cafeteria seat</p>
          </div>

          <Card className="p-6 rounded-3xl shadow-sm border-gray-100 mb-6 bg-white/95 backdrop-blur-sm">
            <h3 className="text-sm font-medium text-gray-700 mb-4">Sign in with W3ID</h3>
            <div className="space-y-3">
              {/* Real W3ID - IBM SSO */}
              <Button
                onClick={handleRealW3IDLogin}
                className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-sm text-base font-medium"
              >
                <ShieldCheck className="mr-2 h-5 w-5" />
                Sign in with Real W3ID
              </Button>

              {/* Dummy W3ID - Demo with managers/employees */}
              <Button
                onClick={handleDummyW3IDClick}
                variant="outline"
                className="w-full h-12 border-gray-300 text-gray-700 hover:bg-gray-50 rounded-xl text-base font-medium"
              >
                <UserCircle className="mr-2 h-5 w-5" />
                Sign in with Dummy W3ID
              </Button>
            </div>
          </Card>

          <div className="flex gap-4 mb-6">
            <div className="flex-1 h-px bg-gray-200"></div>
            <span className="text-sm text-gray-500">Or</span>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>

          <div className="space-y-3">
            <Button
              onClick={onLogin}
              variant="outline"
              className="w-full h-12 border-gray-300 text-gray-700 hover:bg-gray-50 rounded-xl text-base font-medium"
            >
              <KeyRound className="mr-2 h-5 w-5" />
              Sign in with Passkey
            </Button>
          </div>

          <p className="text-center text-sm text-gray-500 mt-8">
            Don&apos;t have an account?{" "}
            <button className="text-blue-600 hover:text-blue-700 font-medium">
              Contact IT Support
            </button>
          </p>
        </div>
      </div>

      {/* Dummy W3ID Modal - Managers, Admin, 10 Employees */}
      {showDummyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="p-6 rounded-3xl shadow-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-medium text-gray-900">Dummy W3ID - Select Manager & Employee</h2>
              <button
                onClick={() => setShowDummyModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-700 mb-2 block">Select Manager</label>
                <select
                  value={selectedManager}
                  onChange={(e) => {
                    setSelectedManager(e.target.value);
                    if (e.target.value === "Admin") {
                      setSelectedEmployee("admin001");
                    } else {
                      setSelectedEmployee("");
                    }
                  }}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                >
                  <option value="">-- Select Manager --</option>
                  {managers.map((m) => (
                    <option key={m.name} value={m.name}>
                      {m.name} ({m.balance.toLocaleString()} Blu-Points)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm text-gray-700 mb-2 block">Select Employee</label>
                {selectedManager === "Admin" ? (
                  <input
                    type="text"
                    value="admin001"
                    readOnly
                    className="w-full px-4 py-3 bg-gray-100 border border-gray-200 rounded-xl text-gray-500 outline-none"
                  />
                ) : (
                  <select
                    value={selectedEmployee}
                    onChange={(e) => setSelectedEmployee(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                  >
                    <option value="">-- Select Employee --</option>
                    {EMPLOYEES.map((emp) => (
                      <option key={emp} value={emp}>
                        {emp}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <Button
                onClick={handleDummyLogin}
                className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-xl"
              >
                Login
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
