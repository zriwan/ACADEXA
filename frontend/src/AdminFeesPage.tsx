// frontend/src/AdminFeesPage.tsx
import React, { useEffect, useState } from "react";
import { api } from "./api/client";

type StudentLite = {
  id: number;
  name: string;
  department: string;
  gpa?: any;
};

type FeeTxn = {
  id: number;
  student_id: number;
  txn_type: "payment" | "fine" | "scholarship" | "adjustment";
  amount: number;
  note: string | null;
  created_at: string;
};

type FeeStatus = {
  student_id: number;
  total_fee: number;
  paid: number;
  pending: number;
  transactions: FeeTxn[];
};

const AdminFeesPage: React.FC = () => {
  const [students, setStudents] = useState<StudentLite[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<number | "">("");

  const [status, setStatus] = useState<FeeStatus | null>(null);

  const [totalFee, setTotalFee] = useState<string>("");

  const [txnType, setTxnType] = useState<FeeTxn["txn_type"]>("payment");
  const [amount, setAmount] = useState<string>("");
  const [note, setNote] = useState<string>("");

  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const fetchStudents = async () => {
    const res = await api.get<StudentLite[]>("/students/");
    setStudents(res.data);
  };

  const fetchFeeStatus = async (sid: number) => {
    const res = await api.get<FeeStatus>(`/fees/student/${sid}`);
    setStatus(res.data);
    setTotalFee(res.data.total_fee?.toString() ?? "");
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await fetchStudents();
      } catch (e) {
        setErr("Failed to load students.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    setMsg(null);
    setErr(null);
    setStatus(null);

    if (selectedStudentId !== "") {
      fetchFeeStatus(Number(selectedStudentId)).catch(() => setErr("Failed to load fee status."));
    }
  }, [selectedStudentId]);

  const onSetTotalFee = async () => {
    if (selectedStudentId === "") return;
    try {
      setLoading(true);
      setMsg(null);
      setErr(null);

      await api.post("/fees/accounts/set", {
        student_id: Number(selectedStudentId),
        total_fee: Number(totalFee),
      });

      await fetchFeeStatus(Number(selectedStudentId));
      setMsg("Total fee updated.");
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? "Failed to set total fee.");
    } finally {
      setLoading(false);
    }
  };

  const onAddTxn = async () => {
    if (selectedStudentId === "") return;
    try {
      setLoading(true);
      setMsg(null);
      setErr(null);

      await api.post("/fees/transactions", {
        student_id: Number(selectedStudentId),
        txn_type: txnType,
        amount: Number(amount),
        note: note || null,
      });

      setAmount("");
      setNote("");
      await fetchFeeStatus(Number(selectedStudentId));
      setMsg("Transaction added.");
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? "Failed to add transaction.");
    } finally {
      setLoading(false);
    }
  };

  const selectedStudent = selectedStudentId === "" ? null : students.find(s => s.id === Number(selectedStudentId));

  return (
    <div>
      <h1 className="page-title">Fees (Admin)</h1>
      <p className="page-subtitle">Set total fee and add payments/fines/scholarships for students.</p>

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Select Student</h2>
        </div>
        <div className="card-body">
          <select
            value={selectedStudentId}
            onChange={(e) => setSelectedStudentId(e.target.value ? Number(e.target.value) : "")}
            style={{ padding: 10, width: "100%", maxWidth: 520 }}
          >
            <option value="">-- Select student --</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>
                #{s.id} — {s.name} ({s.department})
              </option>
            ))}
          </select>

          {selectedStudent && (
            <div style={{ marginTop: 10, color: "#666" }}>
              Selected: <b>{selectedStudent.name}</b> — Dept: {selectedStudent.department} — ID: {selectedStudent.id}
            </div>
          )}
        </div>
      </section>

      {selectedStudentId !== "" && (
        <>
          <section className="card" style={{ marginTop: 14 }}>
            <div className="card-header">
              <h2 className="card-title">Set Total Fee</h2>
            </div>
            <div className="card-body" style={{ display: "grid", gap: 10, maxWidth: 520 }}>
              <input
                placeholder="Total fee (e.g. 50000)"
                value={totalFee}
                onChange={(e) => setTotalFee(e.target.value)}
              />
              <button className="btn btn-primary" onClick={onSetTotalFee} disabled={loading}>
                Save Total Fee
              </button>
            </div>
          </section>

          <section className="card" style={{ marginTop: 14 }}>
            <div className="card-header">
              <h2 className="card-title">Add Transaction</h2>
            </div>
            <div className="card-body" style={{ display: "grid", gap: 10, maxWidth: 520 }}>
              <select value={txnType} onChange={(e) => setTxnType(e.target.value as any)}>
                <option value="payment">payment</option>
                <option value="fine">fine</option>
                <option value="scholarship">scholarship</option>
                <option value="adjustment">adjustment</option>
              </select>

              <input
                placeholder="Amount (e.g. 1000)"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />

              <input
                placeholder="Note (optional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />

              <button className="btn btn-primary" onClick={onAddTxn} disabled={loading}>
                Add Transaction
              </button>
            </div>
          </section>

          <section className="card" style={{ marginTop: 14 }}>
            <div className="card-header">
              <h2 className="card-title">Current Fee Status</h2>
            </div>
            <div className="card-body">
              {!status ? (
                <p>Loading status...</p>
              ) : (
                <>
                  <div style={{ display: "flex", gap: 18, flexWrap: "wrap", marginBottom: 10 }}>
                    <div><b>Total Fee:</b> {status.total_fee.toFixed(2)}</div>
                    <div><b>Paid:</b> {status.paid.toFixed(2)}</div>
                    <div style={{ fontWeight: 800 }}><b>Pending:</b> {status.pending.toFixed(2)}</div>
                  </div>

                  <h3 style={{ marginTop: 6 }}>Transactions</h3>
                  {status.transactions.length === 0 ? (
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
                        {status.transactions.map((t) => (
                          <tr key={t.id}>
                            <td>{new Date(t.created_at).toLocaleString()}</td>
                            <td>{t.txn_type}</td>
                            <td>{Number(t.amount).toFixed(2)}</td>
                            <td>{t.note || "-"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </>
              )}

              {msg && <div className="alert alert-success" style={{ marginTop: 10 }}>{msg}</div>}
              {err && <div className="alert alert-error" style={{ marginTop: 10 }}>{err}</div>}
            </div>
          </section>
        </>
      )}

      {loading && <p style={{ marginTop: 10 }}>Working...</p>}
    </div>
  );
};

export default AdminFeesPage;
