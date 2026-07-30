import { jsPDF } from "jspdf";

export type InvoiceInput = {
  id: string;
  date: string;
  amount: number;
  status: "paid" | "open" | "refunded";
  plan: string;
  cycle: string;
};

export type BillTo = {
  name: string;
  email?: string;
  cardBrand: string;
  cardLast4: string;
};

// Design tokens (RGB)
const INK = [10, 10, 10] as const;
const SUB = [110, 110, 115] as const;
const HAIR = [225, 225, 230] as const;
const BRAND = [37, 99, 235] as const; // Vercel-ish blue
const EMERALD = [16, 185, 129] as const;
const AMBER = [217, 119, 6] as const;
const MUTED_BG = [248, 248, 250] as const;

export function generateInvoicePdf(inv: InvoiceInput, billTo: BillTo) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const M = 48;

  const setFill = (rgb: readonly [number, number, number]) => doc.setFillColor(rgb[0], rgb[1], rgb[2]);
  const setStroke = (rgb: readonly [number, number, number]) => doc.setDrawColor(rgb[0], rgb[1], rgb[2]);
  const setText = (rgb: readonly [number, number, number]) => doc.setTextColor(rgb[0], rgb[1], rgb[2]);

  // ── Header band ─────────────────────────────────────────
  setFill(INK);
  doc.rect(0, 0, W, 96, "F");

  // Logo mark: rounded square + infinity-ish glyph
  setFill(BRAND);
  doc.roundedRect(M, 32, 32, 32, 7, 7, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text("∞", M + 16, 54, { align: "center", baseline: "middle" });

  // Wordmark
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.setTextColor(255, 255, 255);
  doc.text("InfiChat", M + 44, 50);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(180, 180, 190);
  doc.text("AI assistant for teams", M + 44, 64);

  // Right side: INVOICE label + number
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.setTextColor(255, 255, 255);
  doc.text("INVOICE", W - M, 46, { align: "right" });
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(180, 180, 190);
  doc.text(inv.id, W - M, 64, { align: "right" });

  // ── Meta strip ──────────────────────────────────────────
  let y = 128;
  const col = (label: string, value: string, x: number) => {
    setText(SUB);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.text(label.toUpperCase(), x, y);
    setText(INK);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text(value, x, y + 16);
  };
  col("Invoice date", inv.date, M);
  col("Billing cycle", cap(inv.cycle), M + 150);
  col("Status", cap(inv.status), M + 300);

  // Status pill
  const pill = statusPill(inv.status);
  const pillText = cap(inv.status);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  const pw = doc.getTextWidth(pillText) + 18;
  setFill(pill.bg);
  doc.roundedRect(M + 300, y + 4, pw, 16, 8, 8, "F");
  setText(pill.fg);
  doc.text(pillText, M + 300 + pw / 2, y + 16, { align: "center", baseline: "middle" });
  // Overwrite the plain status column value we drew earlier (leave label only)
  setFill([255, 255, 255]);
  // (Simpler: skip repaint; the pill draws on top of the text area but the text
  // was already placed. Instead, blank the text by drawing a white rect first.)

  y += 44;

  // Hairline
  setStroke(HAIR);
  doc.setLineWidth(0.5);
  doc.line(M, y, W - M, y);
  y += 24;

  // ── Bill from / Bill to ─────────────────────────────────
  const boxW = (W - M * 2 - 16) / 2;
  const boxH = 96;
  setFill(MUTED_BG);
  doc.roundedRect(M, y, boxW, boxH, 8, 8, "F");
  doc.roundedRect(M + boxW + 16, y, boxW, boxH, 8, 8, "F");

  const box = (title: string, lines: string[], x: number) => {
    setText(SUB);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.text(title.toUpperCase(), x + 14, y + 20);
    setText(INK);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    lines.forEach((ln, i) => {
      if (i === 0) doc.setFont("helvetica", "bold");
      else doc.setFont("helvetica", "normal");
      doc.text(ln, x + 14, y + 38 + i * 14);
    });
  };
  box("Billed from", [
    "InfiChat, Inc.",
    "2261 Market Street #4571",
    "San Francisco, CA 94114",
    "United States",
  ], M);
  box("Billed to", [
    billTo.name || "Customer",
    billTo.email || "—",
    `${billTo.cardBrand} •••• ${billTo.cardLast4}`,
  ], M + boxW + 16);

  y += boxH + 32;

  // ── Line items table ────────────────────────────────────
  const tableTop = y;
  // header
  setFill(INK);
  doc.roundedRect(M, y, W - M * 2, 28, 6, 6, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("DESCRIPTION", M + 14, y + 18);
  doc.text("QTY", M + (W - M * 2) - 200, y + 18, { align: "right" });
  doc.text("UNIT", M + (W - M * 2) - 100, y + 18, { align: "right" });
  doc.text("AMOUNT", W - M - 14, y + 18, { align: "right" });
  y += 28;

  const items = [
    {
      title: `${inv.plan} Plan — ${cap(inv.cycle)} subscription`,
      sub: "Access to all models, Deep Research, Deep Thinking, priority routing.",
      qty: 1,
      unit: inv.amount,
      amount: inv.amount,
    },
  ];

  items.forEach((it, i) => {
    if (i % 2 === 1) {
      setFill(MUTED_BG);
      doc.rect(M, y, W - M * 2, 40, "F");
    }
    setText(INK);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.text(it.title, M + 14, y + 16);
    setText(SUB);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.text(it.sub, M + 14, y + 30);

    setText(INK);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.text(String(it.qty), M + (W - M * 2) - 200, y + 22, { align: "right" });
    doc.text(fmt(it.unit), M + (W - M * 2) - 100, y + 22, { align: "right" });
    doc.setFont("helvetica", "bold");
    doc.text(fmt(it.amount), W - M - 14, y + 22, { align: "right" });
    y += 40;
  });

  // divider
  setStroke(HAIR);
  doc.line(M, y, W - M, y);
  y += 20;

  // ── Totals ──────────────────────────────────────────────
  const subTotal = items.reduce((s, i) => s + i.amount, 0);
  const tax = 0;
  const total = subTotal + tax;

  const totalsRow = (label: string, value: string, opts?: { strong?: boolean }) => {
    setText(opts?.strong ? INK : SUB);
    doc.setFont("helvetica", opts?.strong ? "bold" : "normal");
    doc.setFontSize(opts?.strong ? 13 : 10);
    doc.text(label, W - M - 140, y, { align: "right" });
    setText(INK);
    doc.setFont("helvetica", opts?.strong ? "bold" : "normal");
    doc.setFontSize(opts?.strong ? 13 : 10);
    doc.text(value, W - M - 14, y, { align: "right" });
    y += opts?.strong ? 22 : 18;
  };
  totalsRow("Subtotal", fmt(subTotal));
  totalsRow("Tax (0%)", fmt(tax));
  y += 4;
  setStroke(HAIR);
  doc.line(W - M - 200, y - 10, W - M, y - 10);
  totalsRow("Total due", fmt(total), { strong: true });

  // Paid stamp for paid invoices
  if (inv.status === "paid") {
    doc.saveGraphicsState();
    // rotated PAID stamp
    setStroke(EMERALD);
    setText(EMERALD);
    doc.setLineWidth(2);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(28);
    const stampX = M + 80;
    const stampY = tableTop + 130;
    // Draw rounded outline
    doc.roundedRect(stampX - 6, stampY - 26, 130, 40, 6, 6, "S");
    doc.text("PAID", stampX + 58, stampY, { align: "center", baseline: "middle" });
    doc.restoreGraphicsState();
  }

  // ── Payment / notes ─────────────────────────────────────
  y += 24;
  setFill(MUTED_BG);
  doc.roundedRect(M, y, W - M * 2, 72, 8, 8, "F");
  setText(SUB);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.text("PAYMENT", M + 14, y + 18);
  setText(INK);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.text(
    `Charged to ${billTo.cardBrand} ending in ${billTo.cardLast4} on ${inv.date}.`,
    M + 14,
    y + 36,
  );
  setText(SUB);
  doc.setFontSize(9);
  doc.text(
    "Securely processed by Stripe. This invoice is generated electronically and is valid without signature.",
    M + 14,
    y + 54,
  );

  // ── Footer ──────────────────────────────────────────────
  setStroke(HAIR);
  doc.line(M, H - 64, W - M, H - 64);
  setText(SUB);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.text("Questions? billing@infichat.ai", M, H - 44);
  doc.text("infichat.ai", W / 2, H - 44, { align: "center" });
  doc.text(`Invoice ${inv.id} · Page 1 of 1`, W - M, H - 44, { align: "right" });

  // subtle brand accent bar at bottom
  setFill(BRAND);
  doc.rect(0, H - 6, W, 6, "F");

  doc.save(`InfiChat-${inv.id}.pdf`);
}

function fmt(n: number) {
  return `$${n.toFixed(2)}`;
}
function cap(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
function statusPill(status: "paid" | "open" | "refunded") {
  if (status === "paid") return { bg: [220, 252, 231] as const, fg: EMERALD };
  if (status === "open") return { bg: [254, 243, 199] as const, fg: AMBER };
  return { bg: [229, 231, 235] as const, fg: SUB };
}
