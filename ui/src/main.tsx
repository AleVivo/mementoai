import React from "react";
import ReactDOM from "react-dom/client";
import "./App.css";
import App from "./App";

// Apply dark class before first paint to avoid flash
if (localStorage.getItem("theme") === "dark") {
  document.documentElement.classList.add("dark");
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
