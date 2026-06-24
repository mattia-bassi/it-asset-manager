import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

const Login = lazy(() => import('./pages/Login'));
const MasterSetup = lazy(() => import('./pages/MasterSetup'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const People = lazy(() => import('./pages/People'));
const Sites = lazy(() => import('./pages/Sites'));
const Suppliers = lazy(() => import('./pages/Suppliers'));
const Assets = lazy(() => import('./pages/Assets'));
const Inventory = lazy(() => import('./pages/Inventory'));
const Assignments = lazy(() => import('./pages/Assignments'));
const Documents = lazy(() => import('./pages/Documents'));
const Reports = lazy(() => import('./pages/Reports'));
const Settings = lazy(() => import('./pages/Settings'));
const Sims = lazy(() => import('./pages/Sims'));
const Badges = lazy(() => import('./pages/Badges'));

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/master-setup" element={<MasterSetup />} />
          <Route
            path="/"
            element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/people"
            element={
            <ProtectedRoute>
              <Layout>
                <People />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/sites"
            element={
            <ProtectedRoute>
              <Layout>
                <Sites />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/suppliers"
            element={
            <ProtectedRoute>
              <Layout>
                <Suppliers />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/assets"
            element={
            <ProtectedRoute>
              <Layout>
                <Assets />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/inventory"
            element={
            <ProtectedRoute>
              <Layout>
                <Inventory />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/assignments"
            element={
            <ProtectedRoute>
              <Layout>
                <Assignments />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/documents"
            element={
            <ProtectedRoute>
              <Layout>
                <Documents />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/reports"
            element={
            <ProtectedRoute>
              <Layout>
                <Reports />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/settings"
            element={
            <ProtectedRoute>
              <Layout>
                <Settings />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/sims"
            element={
            <ProtectedRoute>
              <Layout>
                <Sims />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route
            path="/badges"
            element={
            <ProtectedRoute>
              <Layout>
                <Badges />
              </Layout>
            </ProtectedRoute>
          }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

