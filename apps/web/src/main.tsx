import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App";
import PatientDetail from "./PatientDetail";
import { DoctorProvider } from "./context/DoctorContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <DoctorProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/patients/:id" element={<PatientDetail />} />
        </Routes>
      </BrowserRouter>
    </DoctorProvider>
  </React.StrictMode>
);
