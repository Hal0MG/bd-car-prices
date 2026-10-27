import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { validateReport } from "@/lib/report";

// Local JSONL store for development. Swap for Postgres before deploying:
// serverless hosts don't keep files written at runtime.
const STORE = path.join(process.cwd(), "data", "reports.jsonl");

export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return Response.json({ errors: { form: "Send the form as JSON." } }, { status: 400 });
  }
  const v = validateReport(body);
  if (!v.ok) return Response.json({ errors: v.errors }, { status: 422 });

  await mkdir(path.dirname(STORE), { recursive: true });
  await appendFile(STORE, JSON.stringify({ ...v.report, receivedAt: new Date().toISOString() }) + "\n");
  return Response.json({ ok: true }, { status: 201 });
}
