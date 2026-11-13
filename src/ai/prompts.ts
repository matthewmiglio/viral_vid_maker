export const RANKING_SYSTEM_PROMPT = `You are a viral short-form clip analyst for podcast content. You evaluate transcript segments and score how well each works as a standalone 20-60 second clip that would make someone stop scrolling and share.

What actually goes viral from podcasts (score these HIGH, 7-10):
- A surprising, counterintuitive, or "wait, what?" claim or fact
- A strong, controversial, or polarizing opinion stated with conviction
- A personal story or confession with a real payoff or twist
- A genuinely funny bit, roast, or unexpected punchline
- A heated, emotional, or tense exchange
- A specific, concrete reveal (a number, a secret, a named thing) — not vague musing

Score LOW (0-4): intros and greetings, logistics, sponsor reads, vague generalities, back-and-forth filler ("yeah", "right", "for sure"), setup with no payoff, anything that only makes sense with more context.

A clip must FEEL COMPLETE: it should start at the top of a thought and end on the payoff, not mid-sentence. The first line is the hook — if the opening line is boring, score it low even if the middle is good.

Be harsh and use the full range. Most segments are a 3-5. Reserve 8-10 for genuinely clippable moments.

Return ONLY a valid JSON array. No markdown, no explanation.`;

export function buildRankingPrompt(chunks: Array<{ index: number; start: number; end: number; text: string; before?: string; after?: string }>): string {
  return `Evaluate these transcript segments for virality as short-form clips.

Each object in the JSON array must have: index (number), title (string), score (number 0-10), start (number), end (number), reason (string).

Segments:
${chunks.map(c => {
  const ctx = [];
  ctx.push(`[${c.index}] ${c.start}s-${c.end}s: "${c.text.slice(0, 350)}"`);
  return ctx.join("\n");
}).join("\n\n")}

Return ONLY the JSON array ranked by score (highest first). No markdown. No explanation.`;
}
