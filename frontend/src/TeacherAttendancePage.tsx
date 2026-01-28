// src/TeacherAttendancePage.tsx
import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";

type TeacherCoursesRes = {
  teacher_id: number;
  courses: { id: number; title: string; code: string; credit_hours: number }[];
};

type EnrollmentLite = {
  enrollment_id: number;
  student_id: number;
  student_name: string;
  department: string;
};

type AttendanceSession = {
  id: number;
  course_id: number;
  lecture_date: string; // "YYYY-MM-DD"
  start_time: string | null;
  end_time: string | null;
  created_at: string;
};

type Status = "present" | "absent" | "late";

type BulkRow = {
  enrollment_id: number;
  status: Status;
};

const TeacherAttendancePage: React.FC = () => {
  const [courses, setCourses] = useState<TeacherCoursesRes | null>(null);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);

  const [enrollments, setEnrollments] = useState<EnrollmentLite[]>([]);
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  // create session form
  const [lectureDate, setLectureDate] = useState<string>(() => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  });
  const [startTime, setStartTime] = useState<string>("09:00");
  const [endTime, setEndTime] = useState<string>("10:00");

  // mark map
  const [mark, setMark] = useState<Record<number, Status>>({});

  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const selectedCourseName = useMemo(() => {
    if (!selectedCourseId || !courses?.courses) return "";
    const c = courses.courses.find((x) => x.id === selectedCourseId);
    return c ? `${c.code} — ${c.title}` : "";
  }, [selectedCourseId, courses]);

  const loadCourses = async () => {
    const res = await api.get<TeacherCoursesRes>("/teachers/me/courses");
    setCourses(res.data);
    const first = res.data.courses?.[0]?.id ?? null;
    setSelectedCourseId(first);
  };

  const loadEnrollments = async (courseId: number) => {
    const res = await api.get<EnrollmentLite[]>(`/attendance/teacher/course/${courseId}/enrollments`);
    setEnrollments(res.data || []);
  };

  const loadSessions = async (courseId: number) => {
    const res = await api.get<AttendanceSession[]>(`/attendance/teacher/course/${courseId}/sessions`);
    setSessions(res.data || []);
    const first = (res.data || [])[0]?.id ?? null;
    setSelectedSessionId(first);
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setMsg(null);
        await loadCourses();
      } catch (e: any) {
        console.error(e);
        setMsg("Failed to load courses.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedCourseId) return;
    (async () => {
      try {
        setLoading(true);
        setMsg(null);
        setSelectedSessionId(null);
        setSessions([]);
        setEnrollments([]);
        setMark({});
        await Promise.all([loadEnrollments(selectedCourseId), loadSessions(selectedCourseId)]);
      } catch (e: any) {
        console.error(e);
        setMsg("Failed to load course attendance data.");
      } finally {
        setLoading(false);
      }
    })();
  }, [selectedCourseId]);

  const createSession = async () => {
    if (!selectedCourseId) {
      setMsg("Select a course first.");
      return;
    }
    if (!lectureDate) {
      setMsg("Lecture date is required.");
      return;
    }

    try {
      setLoading(true);
      setMsg(null);

      await api.post(`/attendance/teacher/course/${selectedCourseId}/sessions`, {
        course_id: selectedCourseId,
        lecture_date: lectureDate, // YYYY-MM-DD
        start_time: startTime || null,
        end_time: endTime || null,
      });

      await loadSessions(selectedCourseId);
      setMsg("✅ Session created.");
    } catch (e: any) {
      console.error(e);
      const detail = e?.response?.data?.detail || "Failed to create session.";
      setMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  const saveAttendance = async () => {
    if (!selectedSessionId) {
      setMsg("Select a session first.");
      return;
    }

    const rows: BulkRow[] = enrollments.map((e) => ({
      enrollment_id: e.enrollment_id,
      status: mark[e.enrollment_id] ?? "absent", // default absent
    }));

    try {
      setLoading(true);
      setMsg(null);

      await api.post(`/attendance/teacher/session/${selectedSessionId}/mark/bulk`, {
        records: rows,
      });

      setMsg("✅ Attendance saved.");
    } catch (e: any) {
      console.error(e);
      const detail = e?.response?.data?.detail || "Failed to save attendance.";
      setMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  const refreshAll = async () => {
    try {
      setLoading(true);
      setMsg(null);
      await loadCourses();
      if (selectedCourseId) {
        await Promise.all([loadEnrollments(selectedCourseId), loadSessions(selectedCourseId)]);
      }
    } catch (e) {
      setMsg("Refresh failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 6 }}>Teacher Attendance</h1>
      <p style={{ marginTop: 0, color: "#666" }}>
        Create lecture sessions and mark attendance (Present / Absent / Late).
      </p>

      {loading && <p>Loading...</p>}
      {msg && (
        <div className={msg.startsWith("✅") ? "alert" : "alert alert-error"} style={{ marginTop: 12 }}>
          {msg}
        </div>
      )}

      {/* Course */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">Course</h2>
          <button className="btn btn-secondary" onClick={refreshAll}>
            Refresh
          </button>
        </div>
        <div className="card-body" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <label>
            <b>Select Course:</b>
          </label>
          <select
            value={selectedCourseId ?? ""}
            onChange={(e) => setSelectedCourseId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">-- choose --</option>
            {courses?.courses?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.title}
              </option>
            ))}
          </select>

          {selectedCourseName && (
            <span style={{ color: "#666" }}>
              Selected: <b>{selectedCourseName}</b>
            </span>
          )}
        </div>
      </div>

      {/* Create Session */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header">
          <h2 className="card-title">Create Lecture Session</h2>
        </div>
        <div className="card-body" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ display: "grid", gap: 6 }}>
            <label>Date</label>
            <input type="date" value={lectureDate} onChange={(e) => setLectureDate(e.target.value)} />
          </div>

          <div style={{ display: "grid", gap: 6 }}>
            <label>Start time</label>
            <input value={startTime} onChange={(e) => setStartTime(e.target.value)} placeholder="09:00" />
          </div>

          <div style={{ display: "grid", gap: 6 }}>
            <label>End time</label>
            <input value={endTime} onChange={(e) => setEndTime(e.target.value)} placeholder="10:00" />
          </div>

          <button className="btn btn-primary" onClick={createSession} disabled={!selectedCourseId || loading}>
            Create Session
          </button>
        </div>
      </div>

      {/* Sessions */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header">
          <h2 className="card-title">Sessions</h2>
        </div>
        <div className="card-body" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          {sessions.length === 0 ? (
            <p>No sessions created yet.</p>
          ) : (
            <>
              <label>
                <b>Select Session:</b>
              </label>
              <select
                value={selectedSessionId ?? ""}
                onChange={(e) => setSelectedSessionId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">-- choose --</option>
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    #{s.id} — {s.lecture_date} {s.start_time ? `(${s.start_time}-${s.end_time ?? ""})` : ""}
                  </option>
                ))}
              </select>
            </>
          )}
        </div>
      </div>

      {/* Marking */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">Mark Attendance</h2>
          <button className="btn btn-primary" onClick={saveAttendance} disabled={!selectedSessionId || loading}>
            Save Attendance
          </button>
        </div>
        <div className="card-body">
          {enrollments.length === 0 ? (
            <p>No students enrolled in this course.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Enrollment</th>
                  <th>Student</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {enrollments.map((e) => (
                  <tr key={e.enrollment_id}>
                    <td>{e.enrollment_id}</td>
                    <td>
                      <b>{e.student_name}</b>
                      <div style={{ color: "#666" }}>Student #{e.student_id}</div>
                    </td>
                    <td>
                      <select
                        value={mark[e.enrollment_id] ?? "absent"}
                        onChange={(ev) =>
                          setMark((prev) => ({
                            ...prev,
                            [e.enrollment_id]: ev.target.value as Status,
                          }))
                        }
                      >
                        <option value="present">present</option>
                        <option value="absent">absent</option>
                        <option value="late">late</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <p style={{ color: "#666", marginTop: 10 }}>
            Note: Attendance uses <b>enrollment_id</b>. Students will view attendance in their portal via{" "}
            <code>/attendance/my</code>.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TeacherAttendancePage;
