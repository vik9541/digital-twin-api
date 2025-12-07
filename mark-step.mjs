import fetch from "node-fetch";

const [, , phase, title, notes] = process.argv;

if (!phase || !title) {
  console.error("Usage: node mark-step.mjs <phase> <title> [notes]");
  process.exit(1);
}

const SUPABASE_URL = process.env.SUPABASE_URL || "https://lvixtpatqrtuwhygtpjx.supabase.co";
const SUPABASE_KEY = process.env.SUPABASE_KEY;

if (!SUPABASE_KEY) {
  console.error("Error: SUPABASE_KEY environment variable is not set");
  process.exit(1);
}

const body = { p_phase: phase, p_step_name: title, p_notes: notes || "" };

try {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/rpc/mark_step_completed`, {
    method: "POST",
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  console.log("Status:", res.status, res.statusText);
  const text = await res.text();
  if (text) {
    console.log("Response:", text);
  }

  if (res.ok) {
    console.log("\u2705 Step marked as completed!");
  } else {
    console.error("\u274C Failed to mark step");
    process.exit(1);
  }
} catch (error) {
  console.error("Error:", error.message);
  process.exit(1);
}
