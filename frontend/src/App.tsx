// src/App.tsx
import React, { useEffect, useState } from "react";
import { api, setAuthToken } from "./api/client";

import StudentsPage from "./StudentsPage";
import TeachersPage from "./TeachersPage";
import CoursesPage from "./CoursesPage";
import EnrollmentsPage from "./EnrollmentsPage";
import AnalyticsPage from "./AnalyticsPage";
import VoiceConsolePage from "./VoiceConsolePage";

import LoginBox from "./LoginBox";
import StudentHome from "./StudentHome";
import TeacherHome from "./TeacherHome";
import HODHome from "./HODHome";
import TeacherAttendancePage from "./TeacherAttendancePage";
import StudentAttendancePage from "./StudentAttendancePage";

import AdminFeesPage from "./AdminFeesPage";
import DarkModeToggle from "./DarkModeToggle";
import { useDarkMode } from "./DarkModeToggle";

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
  | "teacher_home"
  | "hod_home"
  | "fees"
  | "teacher_attendance"
  | "student_attendance";

// Icon Components
const IconHome = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </svg>
);

const IconUsers = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
);

const IconBook = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
  </svg>
);

const IconClipboard = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
  </svg>
);

const IconBarChart = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="20" x2="12" y2="10" />
    <line x1="18" y1="20" x2="18" y2="4" />
    <line x1="6" y1="20" x2="6" y2="16" />
  </svg>
);

const IconMic = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="23" />
    <line x1="8" y1="23" x2="16" y2="23" />
  </svg>
);

const IconDollar = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

const IconCalendar = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
);

const IconLogout = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [meLoading, setMeLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("voice");
  
  // Initialize dark mode
  useDarkMode();

  async function loadMe() {
    try {
      const res = await api.get("/auth/me");
      setMe(res.data);

      const role = res.data?.role as Me["role"] | undefined;

      if (role === "admin") setTab("students");
      else if (role === "student") setTab("student_home");
      else if (role === "teacher") setTab("teacher_home");
      else if (role === "hod") setTab("hod_home");
      else setTab("voice");
    } catch {
      setMe(null);
    } finally {
      setMeLoading(false);
    }
  }

  useEffect(() => {
    loadMe();

    const onAuthChanged = () => loadMe();
    window.addEventListener("acadexa-auth-changed", onAuthChanged);
    return () => window.removeEventListener("acadexa-auth-changed", onAuthChanged);
  }, []);

  if (meLoading) {
    return (
      <div className="login-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  if (!me) {
    return (
      <div className="login-container">
        <div style={{ position: "absolute", top: "1.5rem", right: "1.5rem" }}>
          <DarkModeToggle />
        </div>
        <LoginBox onLoggedIn={loadMe} />
      </div>
    );
  }

  const role = me.role;
  const isAdmin = role === "admin";
  const isStudent = role === "student";
  const isTeacher = role === "teacher";
  const isHod = role === "hod";
  const canManageDepartment = isAdmin || isHod;

  const handleLogout = () => {
    localStorage.removeItem("acadexa_token");
    setAuthToken(null);
    setMe(null);
    setTab("voice");
    window.dispatchEvent(new Event("acadexa-auth-changed"));
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getPageTitle = () => {
    const titles: Record<Tab, string> = {
      student_home: "Student Dashboard",
      teacher_home: "Teacher Dashboard",
      hod_home: "HOD Dashboard",
      students: "Students",
      teachers: "Teachers",
      courses: "Courses",
      enrollments: "Enrollments",
      analytics: "Analytics",
      fees: "Fees Management",
      voice: "Voice Console",
      teacher_attendance: "Attendance",
      student_attendance: "My Attendance",
    };
    return titles[tab] || "Dashboard";
  };

  const getPageSubtitle = () => {
    const subtitles: Record<Tab, string> = {
      student_home: "View your courses, grades, and academic progress",
      teacher_home: "Manage your courses, attendance, and student grades",
      hod_home: "Department overview and management",
      students: "Manage student records and information",
      teachers: "Manage teacher accounts and profiles",
      courses: "Create and manage course offerings",
      enrollments: "Handle student course enrollments",
      analytics: "View department statistics and insights",
      fees: "Manage student fees and payments",
      voice: "Voice-controlled interface",
      teacher_attendance: "Record and manage student attendance",
      student_attendance: "View your attendance records",
    };
    return subtitles[tab] || "";
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">A</div>
          <div className="sidebar-brand">ACADEXA</div>
        </div>

        <nav className="sidebar-nav">
          {/* Dashboard Section */}
          <div className="sidebar-section">
            <div className="sidebar-section-title">Dashboard</div>
            {isStudent && (
              <button
                onClick={() => setTab("student_home")}
                className={`sidebar-item ${tab === "student_home" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconHome />
                </span>
                <span>My Dashboard</span>
              </button>
            )}
            {isTeacher && (
              <button
                onClick={() => setTab("teacher_home")}
                className={`sidebar-item ${tab === "teacher_home" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconHome />
                </span>
                <span>My Dashboard</span>
              </button>
            )}
            {isHod && (
              <button
                onClick={() => setTab("hod_home")}
                className={`sidebar-item ${tab === "hod_home" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconHome />
                </span>
                <span>HOD Dashboard</span>
              </button>
            )}
          </div>

          {/* Management Section */}
          {canManageDepartment && (
            <div className="sidebar-section">
              <div className="sidebar-section-title">Management</div>
              <button
                onClick={() => setTab("students")}
                className={`sidebar-item ${tab === "students" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconUsers />
                </span>
                <span>Students</span>
              </button>
              <button
                onClick={() => setTab("teachers")}
                className={`sidebar-item ${tab === "teachers" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconUsers />
                </span>
                <span>Teachers</span>
              </button>
              <button
                onClick={() => setTab("courses")}
                className={`sidebar-item ${tab === "courses" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconBook />
                </span>
                <span>Courses</span>
              </button>
              <button
                onClick={() => setTab("enrollments")}
                className={`sidebar-item ${tab === "enrollments" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconClipboard />
                </span>
                <span>Enrollments</span>
              </button>
              <button
                onClick={() => setTab("fees")}
                className={`sidebar-item ${tab === "fees" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconDollar />
                </span>
                <span>Fees</span>
              </button>
              <button
                onClick={() => setTab("analytics")}
                className={`sidebar-item ${tab === "analytics" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconBarChart />
                </span>
                <span>Analytics</span>
              </button>
            </div>
          )}

          {/* Attendance Section */}
          <div className="sidebar-section">
            <div className="sidebar-section-title">Attendance</div>
            {isTeacher && (
              <button
                onClick={() => setTab("teacher_attendance")}
                className={`sidebar-item ${tab === "teacher_attendance" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconCalendar />
                </span>
                <span>Record Attendance</span>
              </button>
            )}
            {isStudent && (
              <button
                onClick={() => setTab("student_attendance")}
                className={`sidebar-item ${tab === "student_attendance" ? "active" : ""}`}
              >
                <span className="sidebar-item-icon">
                  <IconCalendar />
                </span>
                <span>My Attendance</span>
              </button>
            )}
          </div>

          {/* Tools Section */}
          <div className="sidebar-section">
            <div className="sidebar-section-title">Tools</div>
            <button
              onClick={() => setTab("voice")}
              className={`sidebar-item ${tab === "voice" ? "active" : ""}`}
            >
              <span className="sidebar-item-icon">
                <IconMic />
              </span>
              <span>Voice Console</span>
            </button>
          </div>
        </nav>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{getInitials(me.name || me.email)}</div>
            <div className="user-details">
              <div className="user-name">{me.name || me.email}</div>
              <div className="user-role">{role}</div>
            </div>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              <IconLogout />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <div className="top-bar">
          <div className="page-header">
            <h1 className="page-title">{getPageTitle()}</h1>
            <p className="page-subtitle">{getPageSubtitle()}</p>
          </div>
          <DarkModeToggle />
        </div>

        <div className="content-area">
          {tab === "student_home" && isStudent && <StudentHome />}
          {tab === "teacher_home" && isTeacher && <TeacherHome />}
          {tab === "hod_home" && isHod && <HODHome />}

          {tab === "students" && canManageDepartment && <StudentsPage />}
          {tab === "teachers" && canManageDepartment && <TeachersPage />}
          {tab === "courses" && canManageDepartment && <CoursesPage />}
          {tab === "enrollments" && canManageDepartment && <EnrollmentsPage />}
          {tab === "analytics" && canManageDepartment && <AnalyticsPage />}
          {tab === "fees" && canManageDepartment && <AdminFeesPage />}

          {tab === "teacher_attendance" && isTeacher && <TeacherAttendancePage />}
          {tab === "student_attendance" && isStudent && <StudentAttendancePage />}

          {tab === "voice" && <VoiceConsolePage />}
        </div>
      </main>
    </div>
  );
}

export default App;
