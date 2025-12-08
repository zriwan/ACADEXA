// src/AnalyticsPage.tsx

import React, { useEffect, useState } from "react";
import { api } from "./api/client";

type CourseEnrollmentStat = {
  course_id: number;
  course_code: string;
  course_title: string;
  enrollment_count: number;
};

type DeptGpaStat = {
  department: string;
  avg_gpa: number;
  student_count: number;
};

type TeacherLoadStat = {
  teacher_id: number;
  teacher_name: string;
  course_count: number;
};

const AnalyticsPage: React.FC = () => {
  const [courseStats, setCourseStats] = useState<CourseEnrollmentStat[]>([]);
  const [deptStats, setDeptStats] = useState<DeptGpaStat[]>([]);
  const [teacherStats, setTeacherStats] = useState<TeacherLoadStat[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const [coursesRes, deptRes, teachersRes] = await Promise.all([
        api.get<CourseEnrollmentStat[]>("/analytics/courses/enrollment_counts"),
        api.get<DeptGpaStat[]>("/analytics/departments/gpa_summary"),
        api.get<TeacherLoadStat[]>("/analytics/teachers/course_load"),
      ]);

      setCourseStats(coursesRes.data || []);
      setDeptStats(deptRes.data || []);
      setTeacherStats(teachersRes.data || []);
    } catch (err: any) {
      console.error(err);
      setError(
        "Failed to load analytics. Make sure you are logged in as admin and backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div>
      <h1 className="page-title">Analytics</h1>
      <p className="page-subtitle">
        High-level overview of course enrollments, department GPA and teacher
        load.
      </p>

      {/* Refresh + error bar */}
      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          alignItems: "center",
          marginBottom: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <button
          className="btn btn-secondary"
          onClick={fetchAnalytics}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      {/* Summary cards */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Total Courses</h2>
          </div>
          <div className="card-body">
            <p style={{ fontSize: "1.5rem", fontWeight: 600 }}>
              {courseStats.length}
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Departments</h2>
          </div>
          <div className="card-body">
            <p style={{ fontSize: "1.5rem", fontWeight: 600 }}>
              {deptStats.length}
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Teachers with Courses</h2>
          </div>
          <div className="card-body">
            <p style={{ fontSize: "1.5rem", fontWeight: 600 }}>
              {teacherStats.length}
            </p>
          </div>
        </div>
      </section>

      {loading && <p>Loading analytics...</p>}

      {/* Course enrollments */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Course Enrollment Counts</h2>
        </div>
        <div className="card-body">
          {courseStats.length === 0 && !loading && (
            <p>
              No course enrollment data yet. Try creating courses and enrolling
              students first.
            </p>
          )}
          {courseStats.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Enrollments</th>
                </tr>
              </thead>
              <tbody>
                {courseStats.map((c) => (
                  <tr key={c.course_id}>
                    <td>
                      {c.course_code} — {c.course_title}
                    </td>
                    <td>{c.enrollment_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* Department GPA */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Department GPA Summary</h2>
        </div>
        <div className="card-body">
          {deptStats.length === 0 && !loading && (
            <p>
              No GPA data available. Once students have GPAs, department
              summaries will appear here.
            </p>
          )}
          {deptStats.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Average GPA</th>
                  <th>Students</th>
                </tr>
              </thead>
              <tbody>
                {deptStats.map((d) => (
                  <tr key={d.department}>
                    <td>{d.department}</td>
                    <td>{d.avg_gpa.toFixed(2)}</td>
                    <td>{d.student_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* Teacher load */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Teacher Course Load</h2>
        </div>
        <div className="card-body">
          {teacherStats.length === 0 && !loading && (
            <p>
              No teacher load data yet. Assign teachers to courses to see their
              course load here.
            </p>
          )}
          {teacherStats.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Teacher</th>
                  <th>Course count</th>
                </tr>
              </thead>
              <tbody>
                {teacherStats.map((t) => (
                  <tr key={t.teacher_id}>
                    <td>{t.teacher_name}</td>
                    <td>{t.course_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
};

export default AnalyticsPage;
