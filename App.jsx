import { Routes, Route, Navigate, NavLink, useNavigate } from "react-router-dom";
import { api, getToken, clearSession } from "./api";
import Auth from "./pages/Auth.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Profile from "./pages/Profile.jsx";
import Advisor from "./pages/Advisor.jsx";

function Protected({ children }) {
  const nav = useNavigate();
  if (!getToken()) return <Navigate to="/login" replace />;
  const logout = async () => {
    try { await api("/auth/logout", { method: "POST" }); } catch {}
    clearSession(); nav("/login");
  };
  return (
    <>
      <nav className="nav">
        <strong>Credit Assistant</strong>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/profile">Profile</NavLink>
        <NavLink to="/advisor">AI Advisor</NavLink>
        <button className="link" onClick={logout}>Logout</button>
      </nav>
      <main className="container">{children}</main>
    </>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth mode="login" />} />
      <Route path="/register" element={<Auth mode="register" />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/profile" element={<Protected><Profile /></Protected>} />
      <Route path="/advisor" element={<Protected><Advisor /></Protected>} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
