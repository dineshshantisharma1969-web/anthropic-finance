/**
 * n8n Code node — Maharashtra FY2024-25 month router.
 *
 * Turns any month phrasing in a Telegram message ("May", "May-24", "May 2024",
 * "05/2024", "2024005") into the canonical key (e.g. "MAY-24") and the raw-file
 * URLs to fetch. Put this in a Code node AFTER the Telegram Trigger and BEFORE
 * the HTTP Request (fetch CSV) node. It fixes the "data for May-24 not available"
 * error, which happens when the workflow feeds the model a fixed dataset instead
 * of fetching the requested month's file.
 *
 * Input : the incoming message text (adjust `text` extraction to your trigger).
 * Output: { monthKey, corrected, gap_full_attendance, gap_part_days, wants }
 */
const RAW_BASE =
  "https://raw.githubusercontent.com/dineshshantisharma1969-web/anthropic-finance/" +
  "claude/n8n-food-log-meal-timing-Ezdh1/" +
  "docs/pf-salary-reconciliation/maharashtra-fy2024-25";

// fiscal months Apr-24 .. Mar-25
const ORDER = ["APR-24","MAY-24","JUN-24","JUL-24","AUG-24","SEP-24",
               "OCT-24","NOV-24","DEC-24","JAN-25","FEB-25","MAR-25"];
const NAME2NUM = { jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,sept:9,oct:10,nov:11,dec:12 };
// month-number -> canonical key (fiscal year: Apr-Dec = 2024, Jan-Mar = 2025)
const NUM2KEY = { 4:"APR-24",5:"MAY-24",6:"JUN-24",7:"JUL-24",8:"AUG-24",9:"SEP-24",
                  10:"OCT-24",11:"NOV-24",12:"DEC-24",1:"JAN-25",2:"FEB-25",3:"MAR-25" };

function resolveMonth(t) {
  const s = String(t || "").toLowerCase();
  // 1) month name (may / may-24 / may 2024 / may2025)
  const m = s.match(/\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*[-/ ]?\s*(\d{2,4})?\b/);
  if (m) {
    const num = NAME2NUM[m[1]];
    let key = NUM2KEY[num];
    if (m[2]) { // honour an explicit year if given (24/2024 vs 25/2025)
      const yr = m[2].length === 4 ? +m[2] : 2000 + +m[2];
      const suffix = (num >= 4) ? "-24" : "-25";
      key = key.slice(0, 3) + ((num >= 4 && yr === 2024) || (num <= 3 && yr === 2025) ? suffix : suffix);
    }
    return key;
  }
  // 2) payroll code 2024005 (=May-24) / 2025002 (=Feb-25)
  const c = s.match(/\b(202[45])0?(\d{1,2})\b/);
  if (c) return NUM2KEY[+c[2]] || null;
  // 3) numeric 05/2024 or 2024-05
  const n = s.match(/\b(\d{1,2})[-/](\d{4})\b/) || s.match(/\b(\d{4})[-/](\d{1,2})\b/);
  if (n) { const num = +n[1] > 12 ? +n[2] : +n[1]; return NUM2KEY[num] || null; }
  return null;
}

function wantsGap(t) {
  const s = String(t || "").toLowerCase();
  const part = /(part\s*day|partial|part-day)/.test(s);
  const full = /(full\s*day|full\s*attend)/.test(s);
  const gap = /(below\s*15\s*,?0{3}|below\s*15\s*k|<\s*15\s*,?0{3}|ecr\s*pf\s*=?\s*0|not\s*in\s*ecr|gap|coverage)/.test(s)
              || part || full;
  if (!gap) return "corrected";
  if (part) return "gap_part_days";
  return "gap_full_attendance"; // default "below 15k & ecr 0" (and "full attendance") -> coverage-gap set
}

const items = [];
for (const item of $input.all()) {
  // adjust this to where your Telegram text lives (e.g. item.json.message.text)
  const text = item.json.text || item.json.message?.text || item.json.body || "";
  const monthKey = resolveMonth(text);
  const wants = wantsGap(text);
  if (!monthKey || !ORDER.includes(monthKey)) {
    items.push({ json: { error: `Could not resolve a month from: "${text}". Valid: ${ORDER.join(", ")}`, text } });
    continue;
  }
  const urls = {
    corrected:            `${RAW_BASE}/corrected_monthly/CORRECTED_${monthKey}.csv`,
    gap_full_attendance:  `${RAW_BASE}/queries/${monthKey}_below15k_FULLdays_GAP_ecr0.csv`,
    gap_part_days:        `${RAW_BASE}/queries/${monthKey}_below15k_partdays_ecr0.csv`,
  };
  items.push({ json: { monthKey, wants, fetchUrl: urls[wants], ...urls, text } });
}
return items;
