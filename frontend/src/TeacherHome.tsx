// frontend/src/TeacherHome.tsx
import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";

type TeacherProfile = {
  id: number;
  name: string;
  department: string;
  email: string;
  expertise?: string | null;
};

type TeacherCoursesRes = {
  teacher_id: number;
  courses: { id: number; title: string; code: string; credit_hours: number }[];
};

type TeacherEnrollmentsRes = {
  teacher_id: number;
  enrollments: {
    enrollment_id: number;
    course_id: number;
    course_code: string;
    course_title: string;
    student_id: number;
    student_name: string;
    semester: string | null;
    status: string | null;
    grade: number | null;
  }[];
};

type AssessmentItem = {
  id: number;
  course_id: number;
  title: string;
  category: "quiz" | "assignment" | "mid" | "final";
  max_marks: number;
  due_date: string | null;
};

type Tab = "quiz" | "assignment" | "mid" | "final";

type BulkScoreRow = {
  assessment_item_id: number;
  enrollment_id: number;
  obtained_marks: number;
};

/** ✅ Attendance Types */
type AttendanceSession = {
  id: number;
  course_id: number;
  lecture_date: string;
  start_time?: string | null;
  end_time?: string | null;
  created_at?: string;
};

type AttendanceEnrollment = {
  enrollment_id: number;
  student_id: number;
  student_name: string;
  department?: string | null;
};

type AttendanceStatus = "present" | "absent";

const TeacherHome: React.FC = () => {
  const [profile, setProfile] = useState<TeacherProfile | null>(null);
  const [courses, setCourses] = useState<TeacherCoursesRes | null>(null);
  const [enrollments, setEnrollments] = useState<TeacherEnrollmentsRes | null>(null);

  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>("quiz");

  const [items, setItems] = useState<AssessmentItem[]>([]);
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);

  // create item form
  const [newTitle, setNewTitle] = useState("");
  const [newMax, setNewMax] = useState("10");
  const [newDue, setNewDue] = useState("");

  // marks entry map: enrollment_id -> obtained_marks
  const [marks, setMarks] = useState<Record<number, string>>({});

  // ✅ Attendance state
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [attendanceEnrollments, setAttendanceEnrollments] = useState<AttendanceEnrollment[]>([]);
  const [attendanceStatusMap, setAttendanceStatusMap] = useState<Record<number, AttendanceStatus>>({});
  const [attendanceMsg, setAttendanceMsg] = useState<string | null>(null);

  // ✅ (STEP A) Session create form fields
  const todayISO = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  const [lectureDate, setLectureDate] = useState<string>(todayISO);
  const [startTime, setStartTime] = useState<string>("11:00:00");
  const [endTime, setEndTime] = useState<string>("12:00:00");

  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const selectedItem = useMemo(() => {
    if (!selectedItemId) return null;
    return items.find((x) => x.id === selectedItemId) || null;
  }, [items, selectedItemId]);

  const selectedMax = selectedItem?.max_marks ?? null;

  const loadBase = async () => {
    try {
      setLoading(true);
      setMsg(null);

      const [p, c, e] = await Promise.all([
        api.get<TeacherProfile>("/teachers/me"),
        api.get<TeacherCoursesRes>("/teachers/me/courses"),
        api.get<TeacherEnrollmentsRes>("/teachers/me/enrollments"),
      ]);

      setProfile(p.data);
      setCourses(c.data);
      setEnrollments(e.data);

      const first = c.data.courses?.[0]?.id ?? null;
      setSelectedCourseId(first);
    } catch (err: any) {
      console.error(err);
      setMsg("Failed to load teacher dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  const loadItems = async (courseId: number, category: Tab) => {
    try {
      setLoading(true);
      setMsg(null);
      setSelectedItemId(null);
      setItems([]);
      setMarks({});

      const res = await api.get<AssessmentItem[]>(
        `/assessments/teacher/course/${courseId}/items?category=${category}`
      );
      setItems(res.data);
    } catch (err: any) {
      console.error(err);
      setMsg("Failed to load assessment items.");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Attendance: load sessions
  const loadSessions = async (courseId: number) => {
    try {
      setAttendanceMsg(null);
      const res = await api.get<AttendanceSession[]>(`/attendance/teacher/course/${courseId}/sessions`);
      const arr = Array.isArray(res.data) ? res.data : [];
      setSessions(arr);
      const firstSessionId = arr?.[0]?.id ?? null;
      setSelectedSessionId(firstSessionId);
    } catch (err: any) {
      console.error(err);
      setAttendanceMsg("Failed to load attendance sessions.");
      setSessions([]);
      setSelectedSessionId(null);
    }
  };

  // ✅ Attendance: load enrollments for course (attendance module)
  const loadAttendanceEnrollments = async (courseId: number) => {
    try {
      setAttendanceMsg(null);
      const res = await api.get<AttendanceEnrollment[]>(`/attendance/teacher/course/${courseId}/enrollments`);
      const rows = Array.isArray(res.data) ? res.data : [];
      setAttendanceEnrollments(rows);

      // default everyone present
      const initial: Record<number, AttendanceStatus> = {};
      rows.forEach((r) => (initial[r.enrollment_id] = "present"));
      setAttendanceStatusMap(initial);
    } catch (err: any) {
      console.error(err);
      setAttendanceMsg("Failed to load course enrollments for attendance.");
      setAttendanceEnrollments([]);
      setAttendanceStatusMap({});
    }
  };

  // ✅ (STEP B) Attendance: create session (send required payload + show real backend error)
 const createSession = async () => {
  if (!selectedCourseId) return;

  try {
    setLoading(true);
    setAttendanceMsg(null);

    const payload = {
      course_id: selectedCourseId,  // ✅ REQUIRED by backend
      lecture_date: lectureDate,
      start_time: startTime,
      end_time: endTime,
    };

    await api.post(`/attendance/teacher/course/${selectedCourseId}/sessions`, payload);

    await loadSessions(selectedCourseId);
    setAttendanceMsg("✅ Session created");
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail || err?.response?.data || "Failed to create session.";
    setAttendanceMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
  } finally {
    setLoading(false);
  }
};


  // ✅ Attendance: submit bulk marks
  const submitAttendance = async () => {
    if (!selectedCourseId) {
      setAttendanceMsg("Select a course first.");
      return;
    }
    if (!selectedSessionId) {
      setAttendanceMsg("Create/select a session first.");
      return;
    }
    if (attendanceEnrollments.length === 0) {
      setAttendanceMsg("No enrollments found for this course.");
      return;
    }

    const records = attendanceEnrollments.map((en) => ({
      enrollment_id: en.enrollment_id,
      status: attendanceStatusMap[en.enrollment_id] ?? "present",
    }));

    try {
      setLoading(true);
      setAttendanceMsg(null);

      await api.post(`/attendance/teacher/session/${selectedSessionId}/mark/bulk`, { records });

      setAttendanceMsg("✅ Attendance saved");
    } catch (err: any) {
      console.error(err);
      const detail = err?.response?.data?.detail || err?.response?.data || "Failed to save attendance";
      setAttendanceMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBase();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      loadItems(selectedCourseId, tab);
      loadSessions(selectedCourseId);
      loadAttendanceEnrollments(selectedCourseId);
    } else {
      setSessions([]);
      setSelectedSessionId(null);
      setAttendanceEnrollments([]);
      setAttendanceStatusMap({});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCourseId, tab]);

  const filteredEnrollments = useMemo(() => {
    if (!enrollments?.enrollments) return [];
    if (!selectedCourseId) return [];
    return enrollments.enrollments.filter((x) => x.course_id === selectedCourseId);
  }, [enrollments, selectedCourseId]);

  const createItem = async () => {
    if (!selectedCourseId) {
      setMsg("Select a course first.");
      return;
    }
    if (!newTitle.trim()) {
      setMsg("Title required");
      return;
    }
    const maxNum = Number(newMax);
    if (!Number.isFinite(maxNum) || maxNum <= 0) {
      setMsg("Max marks must be a valid number");
      return;
    }

    try {
      setLoading(true);
      setMsg(null);

      const payload: any = {
        course_id: selectedCourseId,
        title: newTitle.trim(),
        category: tab,
        max_marks: maxNum,
        due_date: newDue ? newDue : null,
      };

      await api.post(`/assessments/teacher/course/${selectedCourseId}/items`, payload);

      setNewTitle("");
      setNewMax("10");
      setNewDue("");
      await loadItems(selectedCourseId, tab);
      setMsg("✅ Item created");
    } catch (err: any) {
      console.error(err);
      const detail = err?.response?.data?.detail || "Failed to create item";
      setMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  const saveMarks = async () => {
    if (!selectedCourseId) {
      setMsg("Select a course first.");
      return;
    }
    if (!selectedItemId) {
      setMsg("Select an assessment item first (dropdown).");
      return;
    }

    const max = selectedMax;
    const rows: BulkScoreRow[] = [];
    const invalid: number[] = [];

    for (const enr of filteredEnrollments) {
      const v = marks[enr.enrollment_id];
      if (v === undefined || v === "") continue;

      const n = Number(v);
      if (!Number.isFinite(n)) {
        invalid.push(enr.enrollment_id);
        continue;
      }
      if (n < 0) {
        invalid.push(enr.enrollment_id);
        continue;
      }
      if (typeof max === "number" && n > max) {
        invalid.push(enr.enrollment_id);
        continue;
      }

      rows.push({
        assessment_item_id: selectedItemId,
        enrollment_id: enr.enrollment_id,
        obtained_marks: n,
      });
    }

    if (invalid.length > 0) {
      setMsg(
        `Some marks are invalid (enrollment_id: ${invalid.join(", ")}). Make sure marks are numbers and within 0..${
          max ?? "MAX"
        }.`
      );
      return;
    }

    if (rows.length === 0) {
      setMsg("No marks to upload (enter marks first).");
      return;
    }

    try {
      setLoading(true);
      setMsg(null);

      await api.post(`/assessments/teacher/course/${selectedCourseId}/scores/bulk`, {
        scores: rows,
      });

      setMsg("✅ Marks uploaded successfully.");
    } catch (err: any) {
      console.error(err);
      const detail = err?.response?.data?.detail || "Upload failed";
      setMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  const showSelectedCourseName = useMemo(() => {
    if (!selectedCourseId || !courses?.courses) return "";
    const c = courses.courses.find((x) => x.id === selectedCourseId);
    return c ? `${c.code} — ${c.title}` : "";
  }, [selectedCourseId, courses]);

  return (
    <div style={{ padding: 20, maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 6 }}>Teacher Dashboard</h1>
      <p style={{ marginTop: 0, color: "#666" }}>Courses → Attendance → Marks (Quiz / Assignment / Mid / Final)</p>

      {loading && <p>Loading...</p>}
      {msg && (
        <div className={msg.startsWith("✅") ? "alert" : "alert alert-error"} style={{ marginTop: 12 }}>
          {msg}
        </div>
      )}

      {/* Session */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">Session</h2>
          <button className="btn btn-secondary" onClick={loadBase}>
            Refresh
          </button>
        </div>
        <div className="card-body">
          {profile ? (
            <div>
              Logged in as <b>{profile.email}</b> ({profile.department})
            </div>
          ) : (
            <div>Not loaded</div>
          )}
        </div>
      </div>

      {/* Course */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header">
          <h2 className="card-title">Course</h2>
        </div>
        <div className="card-body" style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
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

          {showSelectedCourseName && (
            <span style={{ color: "#666" }}>
              Selected: <b>{showSelectedCourseName}</b>
            </span>
          )}

          {!courses || courses.courses.length === 0 ? (
            <span style={{ color: "#b00" }}>No courses assigned. (Admin must assign teacher_id on courses)</span>
          ) : null}
        </div>
      </div>

      {/* ✅ Attendance */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">Attendance</h2>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn btn-secondary"
              onClick={() => selectedCourseId && loadSessions(selectedCourseId)}
              disabled={!selectedCourseId}
            >
              Refresh Sessions
            </button>
            <button className="btn btn-primary" onClick={createSession} disabled={!selectedCourseId}>
              Create Session
            </button>
          </div>
        </div>

        <div className="card-body">
          {attendanceMsg && (
            <div className={attendanceMsg.startsWith("✅") ? "alert" : "alert alert-error"} style={{ marginBottom: 12 }}>
              {attendanceMsg}
            </div>
          )}

          {!selectedCourseId ? (
            <p>Select a course first.</p>
          ) : (
            <>
              {/* ✅ (STEP C) Inputs for session create */}
              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
                <label><b>Date:</b></label>
                <input
                  value={lectureDate}
                  onChange={(e) => setLectureDate(e.target.value)}
                  placeholder="YYYY-MM-DD"
                  style={{ width: 140 }}
                />

                <label><b>Start:</b></label>
                <input
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  placeholder="HH:MM:SS"
                  style={{ width: 110 }}
                />

                <label><b>End:</b></label>
                <input
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  placeholder="HH:MM:SS"
                  style={{ width: 110 }}
                />
              </div>

              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <label>
                  <b>Session:</b>
                </label>
                <select
                  value={selectedSessionId ?? ""}
                  onChange={(e) => setSelectedSessionId(e.target.value ? Number(e.target.value) : null)}
                >
                  <option value="">-- choose --</option>
                  {sessions.map((s) => (
                    <option key={s.id} value={s.id}>
                      #{s.id} — {s.lecture_date}
                    </option>
                  ))}
                </select>

                <button className="btn btn-primary" onClick={submitAttendance} disabled={!selectedSessionId}>
                  Save Attendance
                </button>
              </div>

              {sessions.length === 0 && <p style={{ marginTop: 10 }}>No sessions yet. Click “Create Session”.</p>}

              {attendanceEnrollments.length === 0 ? (
                <p style={{ marginTop: 10 }}>No students/enrollments found for this course.</p>
              ) : (
                <table className="table" style={{ marginTop: 12 }}>
                  <thead>
                    <tr>
                      <th>Enrollment ID</th>
                      <th>Student</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendanceEnrollments.map((en) => (
                      <tr key={en.enrollment_id}>
                        <td>{en.enrollment_id}</td>
                        <td>
                          <b>{en.student_name}</b>
                          <div style={{ color: "#666" }}>Student #{en.student_id}</div>
                        </td>
                        <td>
                          <select
                            value={attendanceStatusMap[en.enrollment_id] ?? "present"}
                            onChange={(e) =>
                              setAttendanceStatusMap((prev) => ({
                                ...prev,
                                [en.enrollment_id]: e.target.value as AttendanceStatus,
                              }))
                            }
                          >
                            <option value="present">present</option>
                            <option value="absent">absent</option>
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
        {(["quiz", "assignment", "mid", "final"] as Tab[]).map((t) => (
          <button key={t} className={"nav-button" + (tab === t ? " active" : "")} onClick={() => setTab(t)}>
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Items + Create Item */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">{tab.toUpperCase()} Items</h2>
          <button className="btn btn-secondary" onClick={() => selectedCourseId && loadItems(selectedCourseId, tab)}>
            Refresh Items
          </button>
        </div>

        <div className="card-body">
          {/* Create item */}
          <div style={{ display: "grid", gap: 10, marginBottom: 14 }}>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder={`New ${tab} title`}
                style={{ flex: 1, minWidth: 240 }}
              />
              <input
                value={newMax}
                onChange={(e) => setNewMax(e.target.value)}
                placeholder="Max marks"
                style={{ width: 140 }}
              />
              <input
                value={newDue}
                onChange={(e) => setNewDue(e.target.value)}
                placeholder="Due date (optional, ISO or empty)"
                style={{ flex: 1, minWidth: 240 }}
              />
              <button className="btn btn-primary" onClick={createItem}>
                Create Item
              </button>
            </div>
          </div>

          {/* Items list */}
          {items.length === 0 ? (
            <p>No items found for this category.</p>
          ) : (
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
              <label>
                <b>Select Item:</b>
              </label>
              <select
                value={selectedItemId ?? ""}
                onChange={(e) => {
                  const id = e.target.value ? Number(e.target.value) : null;
                  setSelectedItemId(id);
                  setMarks({});
                }}
              >
                <option value="">-- choose --</option>
                {items.map((it) => (
                  <option key={it.id} value={it.id}>
                    #{it.id} — {it.title} (Max {it.max_marks})
                  </option>
                ))}
              </select>

              {selectedItem && (
                <span style={{ color: "#666" }}>
                  Selected Item Max: <b>{selectedItem.max_marks}</b>
                </span>
              )}
            </div>
          )}

          {selectedItem && (
            <div style={{ marginTop: 10, color: "#666" }}>
              You are entering <b>{tab.toUpperCase()}</b> marks for: <b>{selectedItem.title}</b> (Max{" "}
              <b>{selectedItem.max_marks}</b>)
            </div>
          )}
        </div>
      </div>

      {/* Students + marks entry */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 className="card-title">Students (Enrollment-wise)</h2>
          <button className="btn btn-primary" onClick={saveMarks}>
            Save Marks
          </button>
        </div>

        <div className="card-body">
          {!selectedItem && (
            <div className="alert alert-error" style={{ marginBottom: 12 }}>
              Select an item first (dropdown) to enter obtained marks.
            </div>
          )}

          {filteredEnrollments.length === 0 ? (
            <p>No enrollments found for this course.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Enrollment ID</th>
                  <th>Student</th>
                  <th>Semester</th>
                  <th>Status</th>
                  <th>
                    Obtained Marks{" "}
                    {selectedItem ? <span style={{ color: "#666" }}>(out of {selectedItem.max_marks})</span> : null}
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredEnrollments.map((en) => (
                  <tr key={en.enrollment_id}>
                    <td>{en.enrollment_id}</td>
                    <td>
                      <b>{en.student_name}</b>
                      <div style={{ color: "#666" }}>Student #{en.student_id}</div>
                    </td>
                    <td>{en.semester || "-"}</td>
                    <td>{en.status || "-"}</td>
                    <td style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <input
                        disabled={!selectedItem}
                        value={marks[en.enrollment_id] ?? ""}
                        onChange={(e) =>
                          setMarks((prev) => ({
                            ...prev,
                            [en.enrollment_id]: e.target.value,
                          }))
                        }
                        placeholder={selectedItem ? "e.g. 7" : "Select item first"}
                        style={{ width: 120 }}
                      />
                      {selectedItem && <span style={{ color: "#666" }}>/ {selectedItem.max_marks}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <p style={{ color: "#666", marginTop: 10 }}>
            Note: Marks upload uses <b>enrollment_id</b>. Student portal shows marks via <code>/assessments/my</code>.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TeacherHome;
