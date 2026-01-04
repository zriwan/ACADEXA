// src/AnalyticsPage.tsx

import React, { useEffect, useState } from "react";
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
  pass_rate: number | null; // percentage
};

type DepartmentStat = {
  department: string;
  total_students: number;
  total_courses: number;
  avg_gpa: number | null;
};

const AnalyticsPage: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [courseStats, setCourseStats] = useState<CourseStat[]>([]);
  const [departmentStats, setDepartmentStats] = useState<DepartmentStat[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        setError(null);

        // 3 parallel requests
        const [summaryRes, courseRes, deptRes] = await Promise.all([
          api.get("/analytics/summary"),
          api.get("/analytics/course-stats"),
          api.get("/analytics/department-stats"),
        ]);

        setSummary(summaryRes.data);
        setCourseStats(courseRes.data);
        setDepartmentStats(deptRes.data);
      } catch (err: any) {
        console.error(err);

        if (err.response) {
          const status = err.response.status;
          const data = err.response.data;

          if (status === 401) {
            setError(
              "Not authenticated. Please login first on the Students tab."
            );
          } else {
            setError(
              `Error ${status}: ` +
                (typeof data === "string" ? data : JSON.stringify(data))
            );
          }
        } else if (err.request) {
          setError(
            "No response from server. Is backend running on 127.0.0.1:8000?"
          );
        } else {
          setError("Unexpected error: " + err.message);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  const renderSummaryCards = () => {
    if (!summary) return null;

    const items = [
      {
        label: "Total Students",
        value: summary.total_students,
        subtitle: "Active in the system",
      },
      {
        label: "Total Courses",
        value: summary.total_courses,
        subtitle: "Offered courses",
      },
      {
        label: "Total Teachers",
        value: summary.total_teachers,
        subtitle: "Faculty members",
      },
      {
        label: "Total Enrollments",
        value: summary.total_enrollments,
        subtitle: "Student–course enrollments",
      },
      {
        label: "Average GPA",
        value:
          summary.avg_gpa !== null ? summary.avg_gpa.toFixed(2) : "N/A",
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
              <p
                style={{
                  fontSize: "1.8rem",
                  fontWeight: 600,
                }}
              >
                {item.value}
              </p>
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "#9ca3af",
                  marginTop: "0.25rem",
                }}
              >
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
                <td>
                  {c.avg_grade !== null ? c.avg_grade.toFixed(2) : "N/A"}
                </td>
                <td>
                  {c.pass_rate !== null ? `${c.pass_rate.toFixed(2)}%` : "N/A"}
                </td>
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
                <td>
                  {d.avg_gpa !== null ? d.avg_gpa.toFixed(2) : "N/A"}
                </td>
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
        <div className="card-header">
          <h2 className="card-title">Summary</h2>
        </div>
        <div className="card-body">
          {loading && <p>Loading analytics...</p>}
          {error && <div className="alert alert-error">{error}</div>}

          {!loading && !error && !summary && (
            <p>No analytics data available.</p>
          )}

          {!loading && !error && summary && renderSummaryCards()}

          {/* Raw JSON for summary (optional debug) */}
          {summary && (
            <>
              <h3
                style={{
                  marginTop: "1rem",
                  marginBottom: "0.4rem",
                  fontSize: "0.9rem",
                }}
              >
                Summary JSON
              </h3>
              <pre
                style={{
                  background: "#0b1120",
                  color: "#e5e7eb",
                  padding: "0.75rem",
                  borderRadius: 8,
                  fontSize: "0.8rem",
                  overflowX: "auto",
                  maxHeight: 300,
                }}
              >
                {JSON.stringify(summary, null, 2)}
              </pre>
            </>
          )}
        </div>
      </section>

      {/* Course-wise stats */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Course Statistics</h2>
        </div>
        <div className="card-body">
          {!loading && !error && renderCourseStatsTable()}
          {loading && <p>Loading course statistics...</p>}
        </div>
      </section>

      {/* Department-wise stats */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Department Statistics</h2>
        </div>
        <div className="card-body">
          {!loading && !error && renderDepartmentStatsTable()}
          {loading && <p>Loading department statistics...</p>}
        </div>
      </section>
    </div>
  );
};

export default AnalyticsPage;
