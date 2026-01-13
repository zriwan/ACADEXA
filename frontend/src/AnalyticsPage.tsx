// src/AnalyticsPage.tsx

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api/client";

type AnalyticsSummary = {
  total_students: number;
  total_courses: number;
  total_teachers: number;
  total_enrollments: number;
  avg_gpa: number | null;
};

type CourseStat = {
  id: number;
  code: string | null;
  title: string | null;
  total_enrollments: number;
  avg_grade: number | null;
  pass_rate: number | null;
};

type DepartmentStat = {
  department: string;
  total_students: number;
  total_courses: number;
  avg_gpa: number | null;
};

const TOKEN_KEY = "acadexa_token";

function normalizeError(err: any): string {
  // Axios error shapes:
  // - err.response => server responded (401/403/500)
  // - err.request => no response (network/CORS/backend down)
  // - otherwise => configuration/runtime issue
  if (err?.response) {
    const status = err.response.status;
    const detail =
      err.response.data?.detail ??
      (typeof err.response.data === "string"
        ? err.response.data
        : JSON.stringify(err.response.data));

    if (status === 401) return "Not authenticated. Please login first.";
    if (status === 403) return "Forbidden. Your role may not allow analytics access.";
    return `Analytics failed (HTTP ${status}): ${detail}`;
  }

  if (err?.request) {
    return "No response from server. Is backend running on http://127.0.0.1:8000 ?";
  }

  return `Unexpected error: ${err?.message ?? String(err)}`;
}

const AnalyticsPage: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [courseStats, setCourseStats] = useState<CourseStat[]>([]);
  const [departmentStats, setDepartmentStats] = useState<DepartmentStat[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ✅ token presence (reads from localStorage)
  const token = useMemo(() => localStorage.getItem(TOKEN_KEY), []);

  const clearData = () => {
    setSummary(null);
    setCourseStats([]);
    setDepartmentStats([]);
  };

  const fetchAll = useCallback(async () => {
    // Don’t call analytics if not logged in
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) {
      clearData();
      setError("Please login first (Students tab) to view analytics.");
      return;
    }

    setLoading(true);
    setError(null);

    // ✅ Don’t fail everything if one endpoint fails
    const results = await Promise.allSettled([
      api.get("/analytics/summary"),
      api.get("/analytics/course-stats"),
      api.get("/analytics/department-stats"),
    ]);

    try {
      const [summaryRes, courseRes, deptRes] = results;

      // Summary
      if (summaryRes.status === "fulfilled") {
        setSummary(summaryRes.value.data);
      } else {
        setSummary(null);
        setError(normalizeError(summaryRes.reason));
      }

      // Course stats
      if (courseRes.status === "fulfilled") {
        setCourseStats(courseRes.value.data);
      } else {
        setCourseStats([]);
        // If there is already an error, append; else set
        setError((prev) => prev ?? normalizeError(courseRes.reason));
      }

      // Department stats
      if (deptRes.status === "fulfilled") {
        setDepartmentStats(deptRes.value.data);
      } else {
        setDepartmentStats([]);
        setError((prev) => prev ?? normalizeError(deptRes.reason));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // ✅ initial load
  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // ✅ OPTIONAL: auto-refresh analytics after login in another tab/page
  // This listens for localStorage changes (login stores token)
  useEffect(() => {
  const onAuthChanged = () => {
    fetchAll(); // refetch analytics immediately after login/logout
  };

  window.addEventListener("acadexa-auth-changed", onAuthChanged);
  return () => window.removeEventListener("acadexa-auth-changed", onAuthChanged);
}, [fetchAll]);


  const renderSummaryCards = () => {
    if (!summary) return null;

    const items = [
      { label: "Total Students", value: summary.total_students, subtitle: "Active in the system" },
      { label: "Total Courses", value: summary.total_courses, subtitle: "Offered courses" },
      { label: "Total Teachers", value: summary.total_teachers, subtitle: "Faculty members" },
      { label: "Total Enrollments", value: summary.total_enrollments, subtitle: "Student–course enrollments" },
      {
        label: "Average GPA",
        value: summary.avg_gpa !== null ? summary.avg_gpa.toFixed(2) : "N/A",
        subtitle: "Across all students with GPA",
      },
    ];

    return (
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "1rem",
          marginTop: "1rem",
        }}
      >
        {items.map((item) => (
          <section className="card" key={item.label}>
            <div className="card-body">
              <p
                style={{
                  fontSize: "0.8rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "#6b7280",
                  marginBottom: "0.25rem",
                }}
              >
                {item.label}
              </p>
              <p style={{ fontSize: "1.8rem", fontWeight: 600 }}>{item.value}</p>
              <p style={{ fontSize: "0.8rem", color: "#9ca3af", marginTop: "0.25rem" }}>
                {item.subtitle}
              </p>
            </div>
          </section>
        ))}
      </div>
    );
  };

  const renderCourseStatsTable = () => {
    if (!courseStats || courseStats.length === 0) {
      return <p>No course statistics available.</p>;
    }

    return (
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Title</th>
              <th>Enrollments</th>
              <th>Avg Grade</th>
              <th>Pass Rate</th>
            </tr>
          </thead>
          <tbody>
            {courseStats.map((c) => (
              <tr key={c.id}>
                <td>{c.code ?? "-"}</td>
                <td>{c.title ?? "-"}</td>
                <td>{c.total_enrollments}</td>
                <td>{c.avg_grade !== null ? Number(c.avg_grade).toFixed(2) : "N/A"}</td>
                <td>{c.pass_rate !== null ? `${Number(c.pass_rate).toFixed(2)}%` : "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderDepartmentStatsTable = () => {
    if (!departmentStats || departmentStats.length === 0) {
      return <p>No department statistics available.</p>;
    }

    return (
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Department</th>
              <th>Total Students</th>
              <th>Total Courses</th>
              <th>Avg GPA</th>
            </tr>
          </thead>
          <tbody>
            {departmentStats.map((d) => (
              <tr key={d.department}>
                <td>{d.department}</td>
                <td>{d.total_students}</td>
                <td>{d.total_courses}</td>
                <td>{d.avg_gpa !== null ? Number(d.avg_gpa).toFixed(2) : "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div>
      <h1 className="page-title">Analytics Overview</h1>
      <p className="page-subtitle">
        High-level snapshot of students, courses, teachers and enrollments.
      </p>

      <section className="card">
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">Summary</h2>
          <button className="btn btn-secondary" onClick={fetchAll} disabled={loading}>
            Retry
          </button>
        </div>

        <div className="card-body">
          {loading && <p>Loading analytics...</p>}

          {!loading && !token && (
            <div className="alert alert-error">
              Please login first (Students tab) to view analytics.
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}

          {!loading && !error && summary && renderSummaryCards()}

          {!loading && !error && !summary && token && (
            <p>No analytics data available.</p>
          )}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Course Statistics</h2>
        </div>
        <div className="card-body">
          {loading && <p>Loading course statistics...</p>}
          {!loading && !error && renderCourseStatsTable()}
          {!loading && error && <p>Course stats unavailable due to error.</p>}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Department Statistics</h2>
        </div>
        <div className="card-body">
          {loading && <p>Loading department statistics...</p>}
          {!loading && !error && renderDepartmentStatsTable()}
          {!loading && error && <p>Department stats unavailable due to error.</p>}
        </div>
      </section>
    </div>
  );
};

export default AnalyticsPage;
