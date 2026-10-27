"use client";

import { useState } from "react";
import { validateReport } from "@/lib/report";

const FIELDS = [
  ["make", "Make", "Toyota"],
  ["model", "Model", "Axio Hybrid"],
  ["year", "Model year", "2022"],
  ["cc", "Engine (cc)", "1496"],
] as const;

export function ReportForm() {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "failed">("idle");

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    const v = validateReport(data);
    if (!v.ok) return setErrors(v.errors);
    setErrors({});
    setStatus("sending");
    const res = await fetch("/api/reports", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(v.report),
    }).catch(() => null);
    if (res?.ok) return setStatus("sent");
    if (res?.status === 422) setErrors((await res.json()).errors);
    setStatus("failed");
  }

  if (status === "sent") {
    return <p className="thanks">Recorded. Thank you — every real price makes the estimates more honest.</p>;
  }

  const err = (k: string) => errors[k] && <p className="error">{errors[k]}</p>;
  const clear = (k: string) => () => {
    if (!errors[k]) return;
    setErrors((prev) => {
      const next = { ...prev };
      delete next[k];
      return next;
    });
  };

  return (
    <form onSubmit={submit} noValidate className="report-form">
      <div className="input-row">
        {FIELDS.map(([k, label, ph]) => (
          <label key={k} className="field">
            <span className="eyebrow">{label}</span>
            <input name={k} className="input" placeholder={ph} onChange={clear(k)} inputMode={k === "year" || k === "cc" ? "numeric" : undefined} />
            {err(k)}
          </label>
        ))}
      </div>
      <label className="field">
        <span className="eyebrow">Bought as</span>
        <select name="condition" className="select" defaultValue="recon" onChange={clear("condition")}>
          <option value="recon">Reconditioned, from a dealer or own import</option>
          <option value="used-local">Used, already registered in Bangladesh</option>
          <option value="new">Brand new</option>
        </select>
        {err("condition")}
      </label>
      <div className="input-row">
        <label className="field">
          <span className="eyebrow">Price paid (৳)</span>
          <input name="paidBdt" className="input num" inputMode="numeric" placeholder="31,50,000" onChange={clear("paidBdt")} />
          {err("paidBdt")}
        </label>
        <label className="field">
          <span className="eyebrow">Asking price (৳, optional)</span>
          <input name="askingBdt" className="input num" inputMode="numeric" placeholder="33,00,000" onChange={clear("askingBdt")} />
          {err("askingBdt")}
        </label>
      </div>
      <div className="input-row">
        <label className="field">
          <span className="eyebrow">Month bought</span>
          <input name="month" type="month" className="input" onChange={clear("month")} />
          {err("month")}
        </label>
        <label className="field">
          <span className="eyebrow">City</span>
          <input name="city" className="input" placeholder="Dhaka" onChange={clear("city")} />
          {err("city")}
        </label>
      </div>
      <p className="hint" style={{ marginTop: 18 }}>We don’t ask for your name, phone or chassis number, and never will.</p>
      <div style={{ marginTop: 16 }}>
        <button className="btn" disabled={status === "sending"}>{status === "sending" ? "Recording…" : "Record this price"}</button>
      </div>
      {status === "failed" && !Object.keys(errors).length && <p className="error">Couldn’t save that. Try again in a moment.</p>}
    </form>
  );
}
