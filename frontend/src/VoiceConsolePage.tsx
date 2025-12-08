// src/VoiceConsolePage.tsx

import React, { useState } from "react";
import { api } from "./api/client";

const VoiceConsolePage: React.FC = () => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responseJson, setResponseJson] = useState<any | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setResponseJson(null);

      // backend: POST /voice/command  { "text": "..." }
      const res = await api.post("/voice/command", { text });

      setResponseJson(res.data);
      // ✅ success ke baad input clear
      setText("");
    } catch (err: any) {
      console.error(err);

      if (err.response) {
        const status = err.response.status;
        const data = err.response.data;

        // ✅ 401 ke liye friendly message
        if (status === 401) {
          setError("Not authenticated. Please login first on the Students tab.");
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

  // ------- UI helper: render structured table from results -------
  const renderResultsTable = () => {
    if (!responseJson) return null;

    const results = responseJson.results;
    const type = responseJson.results_type;

    if (!results || !Array.isArray(results) || results.length === 0) {
      return <p>No structured results returned.</p>;
    }

    // Students table
    if (type === "students") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Department</th>
              <th>GPA</th>
            </tr>
          </thead>
          <tbody>
            {results.map((s: any) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.name}</td>
                <td>{s.department}</td>
                <td>{s.gpa}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    // Courses table
    if (type === "courses") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Code</th>
              <th>Title</th>
              <th>Credit hours</th>
            </tr>
          </thead>
          <tbody>
            {results.map((c: any) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.code}</td>
                <td>{c.title}</td>
                <td>{c.credit_hours}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    // Teachers table
    if (type === "teachers") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Department</th>
              <th>Email</th>
              <th>Expertise</th>
            </tr>
          </thead>
          <tbody>
            {results.map((t: any) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.name}</td>
                <td>{t.department}</td>
                <td>{t.email}</td>
                <td>{t.expertise}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    // Enrollments table
    if (type === "enrollments") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Student</th>
              <th>Course</th>
              <th>Semester</th>
              <th>Status</th>
              <th>Grade</th>
            </tr>
          </thead>
          <tbody>
            {results.map((en: any) => (
              <tr key={en.id}>
                <td>{en.id}</td>
                <td>
                  {en.student_name
                    ? `${en.student_name} (#${en.student_id})`
                    : `#${en.student_id}`}
                </td>
                <td>
                  {en.course_code
                    ? `${en.course_code} — ${en.course_title}`
                    : `#${en.course_id}`}
                </td>
                <td>{en.semester ?? "-"}</td>
                <td>{en.status ?? "-"}</td>
                <td>{en.grade ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    // Unknown type: just show JSON of results
    return (
      <pre
        style={{
          background: "#0b1120",
          color: "#e5e7eb",
          padding: "0.75rem",
          borderRadius: 8,
          fontSize: "0.8rem",
          overflowX: "auto",
        }}
      >
        {JSON.stringify(results, null, 2)}
      </pre>
    );
  };

  return (
    <div>
      <h1 className="page-title">AI Command Console</h1>
      <p className="page-subtitle">
        Type natural language commands like{" "}
        <span className="badge">"list students"</span>,{" "}
        <span className="badge">"list courses"</span>,{" "}
        <span className="badge">"list teachers"</span>,{" "}
        <span className="badge">"list enrollments for student 3"</span>.
      </p>

      {/* Command input card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Enter Command</h2>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Command</label>
              <input
                placeholder='e.g. "list students in course cs101"'
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !text.trim()}
            >
              {loading ? "Running..." : "Run Command"}
            </button>
          </form>

          {error && <div className="alert alert-error">{error}</div>}

          {/* ✅ Suggested commands */}
          <div style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
            <p style={{ marginBottom: "0.25rem" }}>
              <strong>Examples:</strong>
            </p>
            <ul
              style={{
                paddingLeft: "1.2rem",
                margin: 0,
                color: "#6b7280",
                lineHeight: 1.4,
              }}
            >
              <li>list students</li>
              <li>list courses</li>
              <li>list teachers</li>
              <li>list enrollments for student 3</li>
              <li>list students in course cs101</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Response card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Response</h2>
        </div>
        <div className="card-body">
          {!responseJson && !loading && <p>No command run yet.</p>}
          {loading && <p>Waiting for response...</p>}

          {responseJson && !loading && (
            <>
              {/* Info line */}
              {responseJson.info && (
                <p style={{ marginBottom: "0.75rem" }}>
                  <strong>Info:</strong> {responseJson.info}
                </p>
              )}

              {/* Parsed intent summary */}
              <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                Intent:{" "}
                <strong>{responseJson.parsed?.intent || "unknown"}</strong>
              </p>

              {/* Structured results (table) */}
              {renderResultsTable()}

              {/* Raw JSON debug */}
              <h3
                style={{
                  marginTop: "1rem",
                  marginBottom: "0.4rem",
                  fontSize: "0.9rem",
                }}
              >
                Raw JSON
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
                {JSON.stringify(responseJson, null, 2)}
              </pre>
            </>
          )}
        </div>
      </section>
    </div>
  );
};

export default VoiceConsolePage;
