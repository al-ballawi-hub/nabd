import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App";
import PatientDetail from "./PatientDetail";
import LoginScreen from "./components/LoginScreen";
import { useAuth } from "./context/auth";

export default function Root() {
  const { user } = useAuth();
  if (!user) {
    return <LoginScreen />;
  }
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/patients/:id" element={<PatientDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
