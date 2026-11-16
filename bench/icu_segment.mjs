// Word segmentation with Intl.Segmenter (ICU word-break rules + ICU's CJK dictionary).
// Protocol: one JSON string per stdin line -> one JSON array of word-like segments per stdout line.
import { createInterface } from "node:readline";

const seg = new Intl.Segmenter("und", { granularity: "word" });
const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of rl) {
  const text = JSON.parse(line);
  const words = [];
  for (const s of seg.segment(text)) if (s.isWordLike) words.push(s.segment);
  process.stdout.write(JSON.stringify(words) + "\n");
}
