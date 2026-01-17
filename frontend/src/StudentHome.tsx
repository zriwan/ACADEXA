import React, { useEffect, useState } from "react";
import { api } from "./api/client";

export default function StudentHome() {
  const [profile, setProfile] = useState<any>(null);
  const [courses, setCourses] = useState<any>(null);
  const [enrollments, setEnrollments] = useState<any>(null);
  const [gpa, setGpa] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [p, c, e, g] = await Promise.all([
          api.get("/students/me"),
          api.get("/students/me/courses"),
          api.get("/students/me/enrollments"),
          api.get("/students/me/gpa"),
        ]);
        setProfile(p.data);
        setCourses(c.data);
        setEnrollments(e.data);
        setGpa(g.data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div style={{ padding: 16 }}>Loading student dashboard...</div>;

  return (
    <div style={{ padding: 16 }}>
      <h2>Student Dashboard</h2>

      <div style={{ marginTop: 12 }}>
        <h3>My Profile</h3>
        <pre>{JSON.stringify(profile, null, 2)}</pre>
      </div>

      <div style={{ marginTop: 12 }}>
        <h3>My GPA</h3>
        <pre>{JSON.stringify(gpa, null, 2)}</pre>
      </div>

      <div style={{ marginTop: 12 }}>
        <h3>My Courses</h3>
        <pre>{JSON.stringify(courses, null, 2)}</pre>
      </div>

      <div style={{ marginTop: 12 }}>
        <h3>My Enrollments</h3>
        <pre>{JSON.stringify(enrollments, null, 2)}</pre>
      </div>
    </div>
  );
}
