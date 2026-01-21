// src/StudentHome.tsx
import React, { useEffect, useState } from "react";
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

const StudentHome: React.FC = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [gpa, setGpa] = useState<GPARes | null>(null);
  const [courses, setCourses] = useState<CoursesRes | null>(null);
  const [enrollments, setEnrollments] = useState<EnrollmentItem[] | null>(null);

  const [open, setOpen] = useState<"profile" | "gpa" | "courses" | "enrollments">(
    "profile"
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    } catch (err: any) {
      console.error(err);
      setError("Failed to load student dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const toggle = (key: typeof open) => {
    setOpen((prev) => (prev === key ? prev : key));
  };

  return (
    <div style={{ padding: 20, maxWidth: 980, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, marginBottom: 6 }}>Student Dashboard</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        View your profile, GPA, courses and enrollments.
      </p>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
        <button
          className={"nav-button" + (open === "profile" ? " active" : "")}
          onClick={() => toggle("profile")}
        >
          My Profile
        </button>
        <button
          className={"nav-button" + (open === "gpa" ? " active" : "")}
          onClick={() => toggle("gpa")}
        >
          GPA
        </button>
        <button
          className={"nav-button" + (open === "courses" ? " active" : "")}
          onClick={() => toggle("courses")}
        >
          Courses
        </button>
        <button
          className={"nav-button" + (open === "enrollments" ? " active" : "")}
          onClick={() => toggle("enrollments")}
        >
          Enrollments
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
                <div style={{ fontSize: 40, fontWeight: 700 }}>
                  {gpa.gpa === null ? "-" : gpa.gpa.toFixed(2)}
                </div>
                <div style={{ color: "#666" }}>
                  Your current GPA (Student #{gpa.student_id})
                </div>
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
    </div>
  );
};

export default StudentHome;
