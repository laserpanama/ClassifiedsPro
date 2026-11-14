import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import "./App.css";
import { ToastProvider } from "./components/ui/toast";
import DashboardLayout from "./components/dashboard/DashboardLayout";
import RequireAuth from "./components/auth/RequireAuth";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AccountsPage from "./pages/AccountsPage";
import AdsPage from "./pages/AdsPage";
import SchedulesPage from "./pages/SchedulesPage";

const NotFoundPage = () => <h2 className="text-2xl font-bold">404: Page Not Found</h2>;

// Layout route element: authenticated shell + the current page.
const AppShell = () => (
  <DashboardLayout>
    <Outlet />
  </DashboardLayout>
);

const App = () => (
  <ToastProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/accounts" element={<AccountsPage />} />
            <Route path="/ads" element={<AdsPage />} />
            <Route path="/schedules" element={<SchedulesPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </ToastProvider>
);

export default App;
