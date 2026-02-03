// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import SurveyPage from './pages/SurveyPage'; // rename your survey file to SurveyPage.tsx if needed
import DashboardPage from './pages/DashboardPage';
import AuthCallbackPage from "./pages/AuthCallbackPage";
import TermsOfUsePage from "./pages/TermsOfUsePage";
const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default route shows the Login page */}
        <Route path="/" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        {/* After login success → navigate('/survey') shows this */}
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="/dashboard" element={<DashboardPage/>} />
        <Route path="/terms" element={<TermsOfUsePage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
