// src/App.tsx
import React, { useEffect, useState } from "react";
import { api } from "./api/client";

import StudentsPage from "./StudentsPage";
import TeachersPage from "./TeachersPage";
import CoursesPage from "./CoursesPage";
import EnrollmentsPage from "./EnrollmentsPage";
import AnalyticsPage from "./AnalyticsPage";
import VoiceConsolePage from "./VoiceConsolePage";

import LoginBox from "./LoginBox";
import StudentHome from "./StudentHome";
import TeacherHome from "./TeacherHome";

type Me = {
  id: number;
  name: string;
  email: string;
  role: "admin" | "student" | "teacher" | "hod";
  student_id?: number | null;
  teacher_id?: number | null;
};

type Tab =
  | "students"
  | "teachers"
  | "courses"
  | "enrollments"
  | "analytics"
  | "voice"
  | "student_home"
  | "teacher_home";

function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [meLoading, setMeLoading] = useState(true);

  const [tab, setTab] = useState<Tab>("voice");

  async function loadMe() {
    try {
      const res = await api.get("/auth/me");
      setMe(res.data);

      // default tab based on role
      const role = res.data?.role;
      if (role === "admin") setTab("students");
      else if (role === "student") setTab("student_home");
      else if (role === "teacher") setTab("teacher_home");
      else setTab("voice");
    } catch {
      setMe(null);
    } finally {
      setMeLoading(false);
    }
  }

  useEffect(() => {
    loadMe();

    // when LoginBox sets token it can dispatch this event
    const onAuthChanged = () => loadMe();
    window.addEventListener("acadexa-auth-changed", onAuthChanged);
    return () => window.removeEventListener("acadexa-auth-changed", onAuthChanged);
  }, []);

  if (meLoading) {
    return <div style={{ padding: 16 }}>Loading...</div>;
  }

  // not logged in
  if (!me) {
    return (
      <div className="app-shell">
        <header className="navbar">
          <div className="navbar-brand">ACADEXA</div>
          <div style={{ marginLeft: "auto", paddingRight: 12 }}>Not logged in</div>
        </header>

        <main style={{ padding: 16 }}>
          <LoginBox onLoggedIn={loadMe} />

        </main>
      </div>
    );
  }

  const role = me.role;

  // RBAC tab visibility
  const isAdmin = role === "admin";
  const isStudent = role === "student";
  const isTeacher = role === "teacher";

  return (
    <div className="app-shell">
      <header className="navbar">
        <div className="navbar-brand">ACADEXA</div>

        <nav className="navbar-tabs">
          {/* STUDENT */}
          {isStudent && (
            <button
              onClick={() => setTab("student_home")}
              className={"nav-button" + (tab === "student_home" ? " active" : "")}
            >
              My Dashboard
            </button>
          )}

          {/* TEACHER */}
          {isTeacher && (
            <button
              onClick={() => setTab("teacher_home")}
              className={"nav-button" + (tab === "teacher_home" ? " active" : "")}
            >
              My Dashboard
            </button>
          )}

          {/* ADMIN */}
          {isAdmin && (
            <>
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
                onClick={() => setTab("analytics")}
                className={"nav-button" + (tab === "analytics" ? " active" : "")}
              >
                Analytics
              </button>
            </>
          )}

          {/* Voice for everyone logged in */}
          <button
            onClick={() => setTab("voice")}
            className={"nav-button" + (tab === "voice" ? " active" : "")}
          >
            Voice
          </button>
        </nav>

        <div style={{ marginLeft: "auto", paddingRight: 12 }}>
          {me.email} ({role})
        </div>
      </header>

      <main>
        {/* STUDENT */}
        {tab === "student_home" && isStudent && <StudentHome />}

        {/* TEACHER */}
        {tab === "teacher_home" && isTeacher && <TeacherHome />}

        {/* ADMIN */}
        {tab === "students" && isAdmin && <StudentsPage />}
        {tab === "teachers" && isAdmin && <TeachersPage />}
        {tab === "courses" && isAdmin && <CoursesPage />}
        {tab === "enrollments" && isAdmin && <EnrollmentsPage />}
        {tab === "analytics" && isAdmin && <AnalyticsPage />}

        {/* Voice */}
        {tab === "voice" && <VoiceConsolePage />}
      </main>
    </div>
  );
}

export default App;
