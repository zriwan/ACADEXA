// src/App.tsx
import React, { useState } from "react";
import StudentsPage from "./StudentsPage";
import TeachersPage from "./TeachersPage";
import CoursesPage from "./CoursesPage";
import EnrollmentsPage from "./EnrollmentsPage";
import AnalyticsPage from "./AnalyticsPage";
import VoiceConsolePage from "./VoiceConsolePage";

function App() {
  const [tab, setTab] = useState<
    "students" | "teachers" | "courses" | "enrollments" | "voice" | "analytics"
  >("students");

  return (
    <div className="app-shell">
      <header className="navbar">
        <div className="navbar-brand">ACADEXA Admin</div>
        <nav className="navbar-tabs">
          <button
            onClick={() => setTab("students")}
            className={"nav-button" + (tab === "students" ? " active" : "")}
          >
            Students
          </button>
          <button
            onClick={() => setTab("teachers")}
            className={"nav-button" + (tab === "teachers" ? " active" : "")}
          >
            Teachers
          </button>
          <button
            onClick={() => setTab("courses")}
            className={"nav-button" + (tab === "courses" ? " active" : "")}
          >
            Courses
          </button>
          <button
            onClick={() => setTab("enrollments")}
            className={"nav-button" + (tab === "enrollments" ? " active" : "")}
          >
            Enrollments
          </button>
          <button
            onClick={() => setTab("voice")}
            className={"nav-button" + (tab === "voice" ? " active" : "")}
          >
            Command
          </button>
          <button
            onClick={() => setTab("analytics")}
            className={"nav-button" + (tab === "analytics" ? " active" : "")}
          >
            Analytics
          </button>
        </nav>
      </header>

      <main>
        {tab === "students" && <StudentsPage />}
        {tab === "teachers" && <TeachersPage />}
        {tab === "courses" && <CoursesPage />}
        {tab === "enrollments" && <EnrollmentsPage />}
        {tab === "voice" && <VoiceConsolePage />}
        {tab === "analytics" && <AnalyticsPage />}
      </main>
    </div>
  );
}

export default App;
