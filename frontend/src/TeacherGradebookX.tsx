// src/TeacherGradebook.tsx
import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";

type Course = {
  id: number;
  title: string;
  code: string;
  credit_hours?: number;
};

type TeacherCoursesRes = { teacher_id: number; courses: Course[] } | Course[];

type EnrollmentRow = {
  enrollment_id?: number;
  id?: number; // fallback
  course_id: number;
  course_code?: string;
  course_title?: string;
  student_id: number;
  student_name: string;
};

type TeacherEnrollmentsRes = EnrollmentRow[] | { results: EnrollmentRow[] };

type AssessmentCategory = "quiz" | "assignment" | "mid" | "final";

type AssessmentItem = {
  id: number;
  course_id: number;
  title: string;
  category: AssessmentCategory;
  max_marks: number;
};

type ScoreCell = {
  assessment_item_id: number;
  enrollment_id: number;
  obtained_marks: number;
};

function normalizeCourses(data: TeacherCoursesRes): Course[] {
  if (Array.isArray(data)) return data;
  return data?.courses || [];
}

function normalizeEnrollments(data: TeacherEnrollmentsRes): EnrollmentRow[] {
  if (Array.isArray(data)) return data;
  return data?.results || [];
}

// ✅ TS-safe guard
const isCourseSelected = (v: number | ""): v is number => typeof v === "number";

export default function TeacherGradebook() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrollments, setEnrollments] = useState<EnrollmentRow[]>([]);

  const [courseId, setCourseId] = useState<number | "">("");
  const [items, setItems] = useState<AssessmentItem[]>([]);
  const [scores, setScores] = useState<Record<string, number>>({}); // key = `${itemId}:${enrollmentId}`

  const [newItem, setNewItem] = useState({
    title: "",
    category: "quiz" as AssessmentCategory,
    max_marks: 10,
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // ----------------------------
  // Load teacher courses/enrollments
  // ----------------------------
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);

        const [cRes, eRes] = await Promise.all([
          api.get<TeacherCoursesRes>("/teachers/me/courses"),
          api.get<TeacherEnrollmentsRes>("/teachers/me/enrollments"),
        ]);

        setCourses(normalizeCourses(cRes.data));
        setEnrollments(normalizeEnrollments(eRes.data));
      } catch (err: any) {
        console.error(err);
        setError("Failed to load courses/enrollments for gradebook.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const courseEnrollments = useMemo(() => {
    if (!isCourseSelected(courseId)) return [];
    return enrollments.filter((e) => e.course_id === courseId);
  }, [enrollments, courseId]);

  // ----------------------------
  // Helpers: fetch items + scores (with fallback endpoints)
  // ----------------------------
  async function fetchItemsAndScores(cid: number) {
    setInfo(null);
    setError(null);

    const itemsUrls = [
      `/assessments/teacher/course/${cid}/items`,
      `/assessments/course/${cid}/items`,
    ];
    const scoresUrls = [
      `/assessments/teacher/course/${cid}/scores`,
      `/assessments/course/${cid}/scores`,
    ];

    // fetch items
    let itemsData: AssessmentItem[] = [];
    let okItems = false;
    for (const url of itemsUrls) {
      try {
        const res = await api.get<AssessmentItem[]>(url);
        itemsData = res.data || [];
        okItems = true;
        break;
      } catch {}
    }

    // fetch scores
    let scoresData: ScoreCell[] = [];
    let okScores = false;
    for (const url of scoresUrls) {
      try {
        const res = await api.get<ScoreCell[]>(url);
        scoresData = res.data || [];
        okScores = true;
        break;
      } catch {}
    }

    if (!okItems || !okScores) {
      setError(
        "Gradebook endpoints missing. Backend me assessments routes implement karni hongi (items + scores)."
      );
      setItems([]);
      setScores({});
      return;
    }

    setItems(itemsData);

    const map: Record<string, number> = {};
    for (const s of scoresData) {
      map[`${s.assessment_item_id}:${s.enrollment_id}`] = Number(
        s.obtained_marks || 0
      );
    }
    setScores(map);
  }

  // When course changes → load items + scores
  useEffect(() => {
    if (!isCourseSelected(courseId)) return;
    fetchItemsAndScores(courseId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  // ----------------------------
  // Create assessment item
  // ----------------------------
  async function createItem(e: React.FormEvent) {
    e.preventDefault();
    if (!isCourseSelected(courseId)) return;

    try {
      setSaving(true);
      setError(null);
      setInfo(null);

      const payload = {
        course_id: courseId,
        title: newItem.title.trim(),
        category: newItem.category,
        max_marks: Number(newItem.max_marks),
      };

      if (!payload.title) {
        setError("Title required.");
        return;
      }

      const urls = [
        `/assessments/teacher/course/${courseId}/items`,
        `/assessments/course/${courseId}/items`,
      ];

      let ok = false;
      for (const url of urls) {
        try {
          await api.post(url, payload);
          ok = true;
          break;
        } catch {}
      }

      if (!ok) {
        setError("Create item endpoint missing (POST items).");
        return;
      }

      setNewItem({ title: "", category: "quiz", max_marks: 10 });
      setInfo("Assessment item created.");
      await fetchItemsAndScores(courseId);
    } catch (err: any) {
      console.error(err);
      setError("Failed to create assessment item.");
    } finally {
      setSaving(false);
    }
  }

  // ----------------------------
  // Change score input
  // ----------------------------
  function setCell(itemId: number, enrollmentId: number, value: string) {
    const num = value === "" ? 0 : Number(value);
    setScores((prev) => ({
      ...prev,
      [`${itemId}:${enrollmentId}`]: isNaN(num) ? 0 : num,
    }));
  }

  // ----------------------------
  // Save scores (bulk)
  // ----------------------------
  async function saveScores() {
    if (!isCourseSelected(courseId)) return;

    try {
      setSaving(true);
      setError(null);
      setInfo(null);

      const bulk: ScoreCell[] = [];
      for (const it of items) {
        for (const enr of courseEnrollments) {
          const enrollmentId = (enr.enrollment_id ?? enr.id) as number;
          const key = `${it.id}:${enrollmentId}`;
          const val = Number(scores[key] ?? 0);

          bulk.push({
            assessment_item_id: it.id,
            enrollment_id: enrollmentId,
            obtained_marks: val,
          });
        }
      }

      const urls = [
        `/assessments/teacher/course/${courseId}/scores/bulk`,
        `/assessments/course/${courseId}/scores/bulk`,
        `/assessments/scores/bulk`,
      ];

      let ok = false;
      for (const url of urls) {
        try {
          await api.post(url, { scores: bulk });
          ok = true;
          break;
        } catch {}
      }

      if (!ok) {
        setError("Save scores endpoint missing (bulk POST).");
        return;
      }

      setInfo("Scores saved successfully.");
      await fetchItemsAndScores(courseId);
    } catch (err: any) {
      console.error(err);
      setError("Failed to save scores.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div style={{ padding: 16 }}>Loading gradebook...</div>;

  return (
    <div className="card">
      <div
        className="card-header"
        style={{ display: "flex", justifyContent: "space-between" }}
      >
        <h2 className="card-title">Gradebook</h2>
        <button
          className="btn btn-secondary"
          onClick={() => isCourseSelected(courseId) && fetchItemsAndScores(courseId)}
        >
          Refresh
        </button>
      </div>

      <div className="card-body">
        {error && (
          <div className="alert alert-error" style={{ marginBottom: 12 }}>
            {error}
          </div>
        )}
        {info && (
          <div className="alert" style={{ marginBottom: 12 }}>
            {info}
          </div>
        )}

        <div className="form-row" style={{ maxWidth: 420 }}>
          <label>Select Course</label>
          <select
            value={courseId === "" ? "" : String(courseId)}
            onChange={(e) =>
              setCourseId(e.target.value ? Number(e.target.value) : "")
            }
          >
            <option value="">-- choose --</option>
            {courses.map((c) => (
              <option key={c.id} value={String(c.id)}>
                {c.code} — {c.title}
              </option>
            ))}
          </select>
        </div>

        {isCourseSelected(courseId) && (
          <>
            <hr style={{ margin: "14px 0" }} />

            {/* Add new item */}
            <h3 style={{ marginTop: 0 }}>Add Quiz / Assignment / Mid / Final</h3>
            <form
              onSubmit={createItem}
              style={{ display: "grid", gap: 10, maxWidth: 520 }}
            >
              <div className="form-row">
                <label>Title</label>
                <input
                  value={newItem.title}
                  onChange={(e) =>
                    setNewItem((p) => ({ ...p, title: e.target.value }))
                  }
                  placeholder="e.g. Quiz 1"
                  required
                />
              </div>

              <div className="form-row">
                <label>Category</label>
                <select
                  value={newItem.category}
                  onChange={(e) =>
                    setNewItem((p) => ({
                      ...p,
                      category: e.target.value as AssessmentCategory,
                    }))
                  }
                >
                  <option value="quiz">Quiz</option>
                  <option value="assignment">Assignment</option>
                  <option value="mid">Mid</option>
                  <option value="final">Final</option>
                </select>
              </div>

              <div className="form-row">
                <label>Max Marks</label>
                <input
                  type="number"
                  min={0}
                  step="1"
                  value={newItem.max_marks}
                  onChange={(e) =>
                    setNewItem((p) => ({
                      ...p,
                      max_marks: Number(e.target.value),
                    }))
                  }
                  required
                />
              </div>

              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? "Saving..." : "Create Item"}
              </button>
            </form>

            <hr style={{ margin: "14px 0" }} />

            {/* Marks grid */}
            <h3 style={{ marginTop: 0 }}>Enter Marks</h3>

            {courseEnrollments.length === 0 ? (
              <p>No students enrolled in this course yet.</p>
            ) : items.length === 0 ? (
              <p>No assessment items yet. Add Quiz/Assignment/Mid/Final first.</p>
            ) : (
              <>
                <div style={{ overflowX: "auto" }}>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Student</th>
                        {items.map((it) => (
                          <th key={it.id}>
                            {it.title}
                            <div style={{ color: "#666", fontSize: 12 }}>
                              {it.category} / {it.max_marks}
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>

                    <tbody>
                      {courseEnrollments.map((enr) => {
                        const enrollmentId = (enr.enrollment_id ?? enr.id) as number;
                        return (
                          <tr key={enrollmentId}>
                            <td>
                              <strong>{enr.student_name}</strong>
                              <div style={{ color: "#666", fontSize: 12 }}>
                                ID: {enr.student_id} / Enr: {enrollmentId}
                              </div>
                            </td>

                            {items.map((it) => {
                              const key = `${it.id}:${enrollmentId}`;
                              const val = scores[key] ?? 0;

                              return (
                                <td key={key}>
                                  <input
                                    type="number"
                                    min={0}
                                    max={it.max_marks}
                                    step="1"
                                    value={val}
                                    onChange={(e) =>
                                      setCell(it.id, enrollmentId, e.target.value)
                                    }
                                    style={{ width: 90 }}
                                  />
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
                  <button className="btn btn-primary" onClick={saveScores} disabled={saving}>
                    {saving ? "Saving..." : "Save Marks"}
                  </button>

                  <button
                    className="btn btn-secondary"
                    onClick={() => isCourseSelected(courseId) && fetchItemsAndScores(courseId)}
                    disabled={saving}
                  >
                    Reload
                  </button>
                </div>

                <p style={{ color: "#666", marginTop: 10 }}>
                  Notes: Ye page bulk save use karta hai. Agar backend endpoints missing hon to error show hoga.
                </p>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
