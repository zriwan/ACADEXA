// src/VoiceConsolePage.tsx

import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api/client";

type SpeechRecognitionType = any;

const VoiceConsolePage: React.FC = () => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  // voice states
  const [listening, setListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [responseJson, setResponseJson] = useState<any | null>(null);

  const recognitionRef = useRef<SpeechRecognitionType | null>(null);

  // Detect SpeechRecognition support (Chrome/Edge)
  const SpeechRecognitionCtor = useMemo(() => {
    const w: any = window;
    return w.SpeechRecognition || w.webkitSpeechRecognition || null;
  }, []);

  useEffect(() => {
    if (!SpeechRecognitionCtor) {
      setVoiceSupported(false);
      return;
    }

    const rec = new SpeechRecognitionCtor();
    rec.continuous = false; // single utterance
    rec.interimResults = true;
    rec.lang = "en-US"; // change if you want (e.g. "ur-PK")

    rec.onstart = () => {
      setListening(true);
      setError(null);
    };

    rec.onend = () => {
      setListening(false);
    };

    rec.onerror = (e: any) => {
      setListening(false);

      // common cases: "not-allowed", "service-not-allowed", "no-speech"
      if (e?.error === "not-allowed" || e?.error === "service-not-allowed") {
        setError(
          "Microphone permission denied. Allow mic permission in browser site settings, then reload."
        );
      } else if (e?.error === "no-speech") {
        setError("No speech detected. Try again and speak clearly.");
      } else {
        setError(`Speech recognition error: ${e?.error || "unknown"}`);
      }
    };

    rec.onresult = (event: any) => {
      // Build transcript from results
      let transcript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        const chunk = res[0]?.transcript || "";
        transcript += chunk;

        if (res.isFinal) {
          finalTranscript += chunk;
        }
      }

      const merged = (finalTranscript || transcript).trim();
      if (merged) {
        setText(merged);
      }

      // OPTIONAL: Auto-send after final result
      // if (finalTranscript.trim()) sendCommand(finalTranscript.trim());
    };

    recognitionRef.current = rec;

    return () => {
      try {
        rec.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    };
  }, [SpeechRecognitionCtor]);

  const startListening = () => {
    setError(null);

    if (!voiceSupported || !recognitionRef.current) {
      setError(
        "Speech recognition is not supported in this browser. Use Chrome/Edge, or type the command."
      );
      return;
    }

    try {
      recognitionRef.current.start();
    } catch (e) {
      // Some browsers throw if start() called twice
      setError("Could not start microphone. Please try again.");
    }
  };

  const stopListening = () => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // ignore
    }
  };

  const sendCommand = async (overrideText?: string) => {
    const command = (overrideText ?? text).trim();
    if (!command) return;

    try {
      setLoading(true);
      setError(null);
      setResponseJson(null);

      // backend: POST /voice/command  { "text": "..." }
      const res = await api.post("/voice/command", { text: command });

      setResponseJson(res.data);
      setText("");
    } catch (err: any) {
      console.error(err);

      if (err.response) {
        const status = err.response.status;
        const data = err.response.data;

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    await sendCommand();
  };

  const handleClear = () => {
    setText("");
    setError(null);
    setResponseJson(null);
  };

  // ------- UI helper: render structured table from results -------

  const renderResultsTable = () => {
    if (!responseJson) return null;

    const results = responseJson.results;
    const type = responseJson.results_type;

    if (!results || !Array.isArray(results) || results.length === 0) {
      return null;
    }

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

  const renderResultsSection = () => {
    if (!responseJson) return null;

    const results = responseJson.results;
    const intent = responseJson.parsed?.intent || "unknown";

    if (!results || !Array.isArray(results) || results.length === 0) {
      if (intent !== "unknown") {
        return (
          <p className="mt-4 text-sm text-gray-500">
            No records found for this command.
          </p>
        );
      }
      return null;
    }

    return <div className="mt-4">{renderResultsTable()}</div>;
  };

  return (
    <div>
      <h1 className="page-title">Command</h1>
      <p className="page-subtitle">
        Type or speak a command. The system will parse intent and return matching
        results.
      </p>

      {/* Command input card */}
      <section className="card">
        <div className="card-header" style={{ display: "flex", gap: "0.5rem", justifyContent: "space-between", alignItems: "center" }}>
          <h2 className="card-title">Command Console</h2>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClear}
              disabled={loading}
            >
              Clear
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={listening ? stopListening : startListening}
              disabled={loading || !voiceSupported}
              title={!voiceSupported ? "Use Chrome/Edge for mic" : ""}
            >
              {listening ? "Stop Mic" : "Use Mic"}
            </button>

            <button
              type="button"
              className="btn btn-primary"
              onClick={() => sendCommand()}
              disabled={loading || listening || !text.trim()}
            >
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>

        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Command text</label>
              <input
                placeholder='e.g. "list students in course cs101"'
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
          </form>

          {!voiceSupported && (
            <div className="alert alert-error">
              Speech recognition is not supported in this browser. Use
              Chrome/Edge, or type the command.
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}

          {/* Suggested commands */}
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
              {responseJson.info && (
                <div style={{ marginBottom: "0.75rem" }}>
                  <p>
                    <strong>Info:</strong> {responseJson.info}
                  </p>

                  {(responseJson.parsed?.intent || "unknown") === "unknown" && (
                    <p
                      style={{
                        fontSize: "0.75rem",
                        color: "#b91c1c",
                        marginTop: "0.25rem",
                      }}
                    >
                      I couldn't understand this command. Try one of the
                      examples above.
                    </p>
                  )}
                </div>
              )}

              <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                Intent:{" "}
                <strong>{responseJson.parsed?.intent || "unknown"}</strong>
              </p>

              {renderResultsSection()}

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
