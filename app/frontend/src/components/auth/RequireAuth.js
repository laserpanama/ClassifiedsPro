import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import authService from '../../services/authService';

// Gate for authenticated routes. The backend enforces the admin key on every
// /api route; this only controls whether the UI shell is shown at all.
const RequireAuth = () => {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
};

export default RequireAuth;
