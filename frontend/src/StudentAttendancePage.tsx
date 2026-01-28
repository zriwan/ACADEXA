// src/StudentAttendancePage.tsx
import React, { useEffect, useState } from "react";
import { api } from "./api/client";

type SummaryCourse = {
  course_id: number;
  course_code: string | null;
  course_title: string | null;
  total_sessions: number;
  present: number;
  absent: number;
  late: number;
  percent_present: number;
};

type MySummary = {
  student_id: number;
  courses: SummaryCourse[];
};

type DetailRow = {
  session_id: number;
  lecture_date: string; // YYYY-MM-DD
  start_time: string | null;
  end_time: string | null;
  status: "present" | "absent" | "late";
};

type Detail = {
  student_id: number;
  course_id: number;
  course_code: string | null;
  course_title: string | null;
  rows: DetailRow[];
};

const StudentAttendancePage: React.FC = () => {
  const [summary, setSummary] = useState<MySummary | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const loadSummary = async () => {
    const res = await api.get<MySummary>("/attendance/my");
    setSummary(res.data);
  };

  const openCourse = async (courseId: number) => {
    const res = await api.get<Detail>(`/attendance/my/course/${courseId}`);
    setDetail(res.data);
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setErr(null);
        await loadSummary();
      } catch (e) {
        setErr("Failed to load attendance.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div style={{ padding: 20, maxWidth: 980, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, marginBottom: 6 }}>My Attendance</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        View your attendance course-wise (date + lecture time).
      </p>

      {loading && <p>Loading...</p>}
      {err && <div className="alert alert-error">{err}</div>}

      <section className="card" style={{ marginTop: 14 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">Summary</h2>
          <button
            className="btn btn-secondary"
            onClick={() => {
              setDetail(null);
              loadSummary().catch(() => setErr("Failed to refresh attendance."));
            }}
          >
            Refresh
          </button>
        </div>
        <div className="card-body">
          {!summary ? (
            <p>No attendance data.</p>
          ) : summary.courses.length === 0 ? (
            <p>No courses found.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Total</th>
                  <th>Present</th>
                  <th>Absent</th>
                  <th>Late</th>
                  <th>%</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {summary.courses.map((c) => (
                  <tr key={c.course_id}>
                    <td>
                      <b>{c.course_code ?? `#${c.course_id}`}</b>
                      <div style={{ color: "#666" }}>{c.course_title ?? ""}</div>
                    </td>
                    <td>{c.total_sessions}</td>
                    <td>{c.present}</td>
                    <td>{c.absent}</td>
                    <td>{c.late}</td>
                    <td style={{ fontWeight: 700 }}>{Number(c.percent_present ?? 0).toFixed(1)}%</td>
                    <td>
                      <button className="btn btn-secondary" onClick={() => openCourse(c.course_id)}>
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {detail && (
        <section className="card" style={{ marginTop: 14 }}>
          <div className="card-header">
            <h2 className="card-title">
              Details: {detail.course_code} — {detail.course_title}
            </h2>
          </div>
          <div className="card-body">
            {detail.rows.length === 0 ? (
              <p>No sessions found for this course.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.rows.map((r) => (
                    <tr key={r.session_id}>
                      <td>{r.lecture_date}</td>
                      <td>{r.start_time ? `${r.start_time} - ${r.end_time ?? ""}` : "-"}</td>
                      <td style={{ fontWeight: 700 }}>{r.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      )}
    </div>
  );
};

export default StudentAttendancePage;
