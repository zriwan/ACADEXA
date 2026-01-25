// src/StudentHome.tsx
import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";

type Profile = {
  id: number;
  name: string;
  department: string;
  gpa: string; // backend returns string
};

type GPARes = {
  student_id: number;
  gpa: number | null;
};

type CourseItem = {
  course_id: number;
  title: string;
  code: string;
  credit_hours: number;
};

type CoursesRes = {
  student_id: number;
  courses: CourseItem[];
};

type EnrollmentItem = {
  id: number;
  student_id: number;
  course_id: number;
  semester: string | null;
  status: string | null;
  grade: string | null;
};

/** Grades summary (from backend /assessments/my) */
type GradeSummary = {
  course_id: number;
  course_code: string | null;
  course_title: string | null;
  internal_percent: number;
  mid_percent: number;
  final_percent: number;
  total_out_of_100: number;
};

/** Grades detail (from backend /assessments/my/course/:id) */
type GradeDetailItem = {
  item_id: number;
  title: string;
  category: "quiz" | "assignment" | "mid" | "final";
  max_marks: number;
  obtained_marks: number | null;
  due_date: string | null;
};

type GradeDetail = {
  course_id: number;
  course_code: string | null;
  course_title: string | null;

  items: GradeDetailItem[];

  internal_percent: number;
  mid_percent: number;
  final_percent: number;
  total_out_of_100: number;
};

/** Fees */
type FeeTxn = {
  id: number;
  student_id: number;
  txn_type: "payment" | "fine" | "scholarship" | "adjustment";
  amount: number;
  note: string | null;
  created_at: string;
};

type FeeMy = {
  student_id: number;
  total_fee: number;
  paid: number;
  pending: number;
  transactions: FeeTxn[];
};

type OpenTab = "profile" | "gpa" | "courses" | "enrollments" | "grades" | "fees";

function toNumberSafe(v: unknown): number {
  if (v === null || v === undefined) return 0;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : 0;
}

const StudentHome: React.FC = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [gpa, setGpa] = useState<GPARes | null>(null);
  const [courses, setCourses] = useState<CoursesRes | null>(null);
  const [enrollments, setEnrollments] = useState<EnrollmentItem[] | null>(null);

  const [gradeSummary, setGradeSummary] = useState<GradeSummary[] | null>(null);
  const [gradeDetail, setGradeDetail] = useState<GradeDetail | null>(null);
  const [fee, setFee] = useState<FeeMy | null>(null);

  const [open, setOpen] = useState<OpenTab>("profile");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const courseMap = useMemo(() => {
    const m = new Map<number, CourseItem>();
    if (courses?.courses) {
      courses.courses.forEach((c) => m.set(c.course_id, c));
    }
    return m;
  }, [courses]);

  // -------------------------
  // Load Basics
  // -------------------------
  const loadAll = async () => {
    try {
      setLoading(true);
      setError(null);

      const [p, g, c, e] = await Promise.all([
        api.get<Profile>("/students/me"),
        api.get<GPARes>("/students/me/gpa"),
        api.get<CoursesRes>("/students/me/courses"),
        api.get<EnrollmentItem[]>("/students/me/enrollments"),
      ]);

      setProfile(p.data);
      setGpa(g.data);
      setCourses(c.data);
      setEnrollments(e.data);

      // Reset derived tabs so they refresh from latest data
      setGradeSummary(null);
      setGradeDetail(null);
      setFee(null);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load student dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // ✅ Grades Summary (FIX)
  // Uses /assessments/my if available.
  // If your backend summary is still buggy, it falls back to building from /assessments/my/course/:id per course.
  // -------------------------
  const loadGrades = async () => {
    try {
      setLoading(true);
      setError(null);
      setGradeDetail(null);

      // 1) try summary endpoint
      try {
        const res = await api.get<GradeSummary[]>("/assessments/my");
        if (Array.isArray(res.data)) {
          setGradeSummary(res.data);
          return;
        }
      } catch (e) {
        // ignore, fallback below
      }

      // 2) fallback: compute from detail endpoint per course (MOST RELIABLE)
      let courseIds: number[] = [];
      if (courses?.courses?.length) {
        courseIds = courses.courses.map((c) => c.course_id);
      } else {
        const c = await api.get<CoursesRes>("/students/me/courses");
        setCourses(c.data);
        courseIds = c.data.courses.map((x) => x.course_id);
      }

      const details = await Promise.all(
        courseIds.map(async (cid) => {
          const r = await api.get<GradeDetail>(`/assessments/my/course/${cid}`);
          return r.data;
        })
      );

      const sumCat = (items: GradeDetailItem[], cat: GradeDetailItem["category"]) => {
        const filtered = items.filter((i) => i.category === cat);
        const max = filtered.reduce((a, i) => a + (toNumberSafe(i.max_marks) || 0), 0);
        const obt = filtered.reduce((a, i) => a + (toNumberSafe(i.obtained_marks) || 0), 0);
        return { obt, max };
      };

      // weights: internal(quiz+assignment) 30%, mid 30%, final 40%
      const W_INTERNAL = 0.3;
      const W_MID = 0.3;
      const W_FINAL = 0.4;

      const summary: GradeSummary[] = details.map((d) => {
        const quiz = sumCat(d.items, "quiz");
        const asg = sumCat(d.items, "assignment");
        const mid = sumCat(d.items, "mid");
        const fin = sumCat(d.items, "final");

        const internalObt = quiz.obt + asg.obt;
        const internalMax = quiz.max + asg.max;

        const internalPercent = internalMax > 0 ? (internalObt / internalMax) * 100 : 0;
        const midPercent = mid.max > 0 ? (mid.obt / mid.max) * 100 : 0;
        const finalPercent = fin.max > 0 ? (fin.obt / fin.max) * 100 : 0;

        const totalOutOf100 =
          internalPercent * W_INTERNAL + midPercent * W_MID + finalPercent * W_FINAL;

        return {
          course_id: d.course_id,
          course_code: d.course_code,
          course_title: d.course_title,
          internal_percent: internalPercent,
          mid_percent: midPercent,
          final_percent: finalPercent,
          total_out_of_100: totalOutOf100,
        };
      });

      setGradeSummary(summary);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load grades.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // ✅ Grade Detail
  // -------------------------
  const openCourseDetail = async (course_id: number) => {
    try {
      setLoading(true);
      setError(null);

      const res = await api.get<GradeDetail>(`/assessments/my/course/${course_id}`);
      setGradeDetail(res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load course grade detail.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // ✅ Fees (Swagger: /fees/me)
  // -------------------------
  const loadFees = async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await api.get<FeeMy>("/fees/me");
      setFee(res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load fee status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = (key: OpenTab) => {
    setOpen(key);
    if (key === "grades" && gradeSummary === null) loadGrades();
    if (key === "fees" && fee === null) loadFees();
  };

  return (
    <div style={{ padding: 20, maxWidth: 980, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, marginBottom: 6 }}>Student Dashboard</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        View your profile, GPA, courses, enrollments, grades and fee status.
      </p>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
        <button className={"nav-button" + (open === "profile" ? " active" : "")} onClick={() => toggle("profile")}>
          My Profile
        </button>
        <button className={"nav-button" + (open === "gpa" ? " active" : "")} onClick={() => toggle("gpa")}>
          GPA
        </button>
        <button className={"nav-button" + (open === "courses" ? " active" : "")} onClick={() => toggle("courses")}>
          Courses
        </button>
        <button
          className={"nav-button" + (open === "enrollments" ? " active" : "")}
          onClick={() => toggle("enrollments")}
        >
          Enrollments
        </button>
        <button className={"nav-button" + (open === "grades" ? " active" : "")} onClick={() => toggle("grades")}>
          Grades
        </button>
        <button className={"nav-button" + (open === "fees" ? " active" : "")} onClick={() => toggle("fees")}>
          Fees
        </button>

        <button className="btn btn-secondary" onClick={loadAll} style={{ marginLeft: "auto" }}>
          Refresh
        </button>
      </div>

      {loading && <p style={{ marginTop: 14 }}>Loading...</p>}
      {error && (
        <div className="alert alert-error" style={{ marginTop: 14 }}>
          {error}
        </div>
      )}

      {/* PROFILE */}
      {open === "profile" && (
        <section className="card" style={{ marginTop: 18 }}>
          <div className="card-header">
            <h2 className="card-title">My Profile</h2>
          </div>
          <div className="card-body">
            {!profile ? (
              <p>No profile found.</p>
            ) : (
              <div style={{ display: "grid", gap: 10 }}>
                <div>
                  <strong>Name:</strong> {profile.name}
                </div>
                <div>
                  <strong>Department:</strong> {profile.department}
                </div>
                <div>
                  <strong>CGPA:</strong> {profile.gpa}
                </div>
                <div>
                  <strong>Student ID:</strong> {profile.id}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* GPA */}
      {open === "gpa" && (
        <section className="card" style={{ marginTop: 18 }}>
          <div className="card-header">
            <h2 className="card-title">My GPA</h2>
          </div>
          <div className="card-body">
            {!gpa ? (
              <p>No GPA data.</p>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div style={{ fontSize: 40, fontWeight: 700 }}>{gpa.gpa === null ? "-" : gpa.gpa.toFixed(2)}</div>
                <div style={{ color: "#666" }}>Your current GPA (Student #{gpa.student_id})</div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* COURSES */}
      {open === "courses" && (
        <section className="card" style={{ marginTop: 18 }}>
          <div className="card-header">
            <h2 className="card-title">My Courses</h2>
          </div>
          <div className="card-body">
            {!courses ? (
              <p>No courses data.</p>
            ) : courses.courses.length === 0 ? (
              <p>You are not enrolled in any courses yet.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Title</th>
                    <th>Credit Hours</th>
                  </tr>
                </thead>
                <tbody>
                  {courses.courses.map((c) => (
                    <tr key={c.course_id}>
                      <td>{c.code}</td>
                      <td>{c.title}</td>
                      <td>{c.credit_hours}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      )}

      {/* ENROLLMENTS */}
      {open === "enrollments" && (
        <section className="card" style={{ marginTop: 18 }}>
          <div className="card-header">
            <h2 className="card-title">My Enrollments</h2>
          </div>
          <div className="card-body">
            {!enrollments ? (
              <p>No enrollments data.</p>
            ) : enrollments.length === 0 ? (
              <p>You have no enrollments yet.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Enrollment ID</th>
                    <th>Course ID</th>
                    <th>Semester</th>
                    <th>Status</th>
                    <th>Grade</th>
                  </tr>
                </thead>
                <tbody>
                  {enrollments.map((e) => (
                    <tr key={e.id}>
                      <td>{e.id}</td>
                      <td>{e.course_id}</td>
                      <td>{e.semester || "-"}</td>
                      <td>{e.status || "-"}</td>
                      <td>{e.grade || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      )}

      {/* GRADES */}
      {open === "grades" && (
        <section className="card" style={{ marginTop: 18 }}>
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
            <h2 className="card-title">Grades (Quiz/Assignment/Mid/Final)</h2>
            <button className="btn btn-secondary" onClick={loadGrades}>
              Refresh Grades
            </button>
          </div>

          <div className="card-body">
            {!gradeSummary ? (
              <p>Loading grades...</p>
            ) : gradeSummary.length === 0 ? (
              <p>No grade data found (teacher may not have entered marks yet).</p>
            ) : (
              <>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Course</th>
                      <th>Internal % (Quiz+Assignment)</th>
                      <th>Mid %</th>
                      <th>Final %</th>
                      <th>Total / 100</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gradeSummary.map((g) => (
                      <tr key={g.course_id}>
                        <td>
                          <strong>{g.course_code || `#${g.course_id}`}</strong>
                          <div style={{ color: "#666" }}>{g.course_title || ""}</div>
                        </td>
                        <td>{toNumberSafe(g.internal_percent).toFixed(2)}%</td>
                        <td>{toNumberSafe(g.mid_percent).toFixed(2)}%</td>
                        <td>{toNumberSafe(g.final_percent).toFixed(2)}%</td>
                        <td style={{ fontWeight: 700 }}>{toNumberSafe(g.total_out_of_100).toFixed(2)}</td>
                        <td>
                          <button className="btn btn-secondary" onClick={() => openCourseDetail(g.course_id)}>
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {gradeDetail && (
                  <div style={{ marginTop: 18 }}>
                    <h3 style={{ marginBottom: 8 }}>
                      Details: {gradeDetail.course_code} — {gradeDetail.course_title}
                    </h3>

                    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 10 }}>
                      <div>
                        <strong>Internal:</strong> {toNumberSafe(gradeDetail.internal_percent).toFixed(2)}%
                      </div>
                      <div>
                        <strong>Mid:</strong> {toNumberSafe(gradeDetail.mid_percent).toFixed(2)}%
                      </div>
                      <div>
                        <strong>Final:</strong> {toNumberSafe(gradeDetail.final_percent).toFixed(2)}%
                      </div>
                      <div>
                        <strong>Total:</strong> {toNumberSafe(gradeDetail.total_out_of_100).toFixed(2)} / 100
                      </div>
                    </div>

                    <table className="table">
                      <thead>
                        <tr>
                          <th>Type</th>
                          <th>Title</th>
                          <th>Obtained</th>
                          <th>Max</th>
                        </tr>
                      </thead>
                      <tbody>
                        {gradeDetail.items.map((it) => (
                          <tr key={it.item_id}>
                            <td>{it.category}</td>
                            <td>{it.title}</td>
                            <td style={{ fontWeight: 700 }}>
                              {it.obtained_marks === null || it.obtained_marks === undefined ? "-" : it.obtained_marks}
                            </td>
                            <td>{it.max_marks}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        </section>
      )}

      {/* FEES */}
      {open === "fees" && (
        <section className="card" style={{ marginTop: 18 }}>
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
            <h2 className="card-title">Fee Status</h2>
            <button className="btn btn-secondary" onClick={loadFees}>
              Refresh Fees
            </button>
          </div>

          <div className="card-body">
            {!fee ? (
              <p>Loading fee status...</p>
            ) : (
              <>
                <div style={{ display: "flex", gap: 18, flexWrap: "wrap", marginBottom: 12 }}>
                  <div>
                    <strong>Total Fee:</strong> {toNumberSafe(fee.total_fee).toFixed(2)}
                  </div>
                  <div>
                    <strong>Paid:</strong> {toNumberSafe(fee.paid).toFixed(2)}
                  </div>
                  <div style={{ fontWeight: 800 }}>
                    <strong>Pending:</strong> {toNumberSafe(fee.pending).toFixed(2)}
                  </div>
                </div>

                {toNumberSafe(fee.pending) > 0 && (
                  <div className="alert alert-error" style={{ marginBottom: 12 }}>
                    Your fee is pending: {toNumberSafe(fee.pending).toFixed(2)}
                  </div>
                )}

                <h3 style={{ marginTop: 6 }}>Transactions</h3>
                {fee.transactions.length === 0 ? (
                  <p>No transactions yet.</p>
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fee.transactions.map((t) => (
                        <tr key={t.id}>
                          <td>{new Date(t.created_at).toLocaleString()}</td>
                          <td>{t.txn_type}</td>
                          <td>{toNumberSafe(t.amount).toFixed(2)}</td>
                          <td>{t.note || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </>
            )}
          </div>
        </section>
      )}
    </div>
  );
};

export default StudentHome;
