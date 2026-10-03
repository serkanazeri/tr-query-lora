import { Hono } from 'hono';
import { compilePlan, parsePlan, SYSTEM_PROMPT } from '../shared/plan';

type Env = {
  AI: { run: (model: string, options: Record<string, unknown>) => Promise<{ response?: string }> };
  DB: D1Database;
  ASSETS: Fetcher;
  BASE_MODEL: string;
  LORA_ID: string;
  REFERENCE_DATE: string;
};

const app = new Hono<{ Bindings: Env }>();
const MAX_COMPARISONS_PER_DAY = 10;

app.get('/api/status', (c) => c.json({
  model: c.env.BASE_MODEL,
  adapter_ready: Boolean(c.env.LORA_ID),
  reference_date: c.env.REFERENCE_DATE,
  dataset: '18 sentetik sipariş',
  daily_demo_limit: MAX_COMPARISONS_PER_DAY,
}));

app.post('/api/compare', async (c) => {
  if (!c.env.LORA_ID) return c.json({ error: 'LoRA adapterı henüz yüklenmedi.' }, 503);
  const body = await c.req.json().catch(() => null);
  const question = typeof body?.question === 'string' ? body.question.trim() : '';
  if (question.length < 8 || question.length > 240) {
    return c.json({ error: 'Soru 8-240 karakter olmalı.' }, 400);
  }

  // Both calls consume the shared free AI quota. Reserve a small public-demo budget first.
  const day = new Date().toISOString().slice(0, 10);
  try {
    await c.env.DB.prepare('INSERT OR IGNORE INTO demo_usage (day, comparisons) VALUES (?, 0)').bind(day).run();
    const reserved = await c.env.DB.prepare('UPDATE demo_usage SET comparisons = comparisons + 1 WHERE day = ? AND comparisons < ?')
      .bind(day, MAX_COMPARISONS_PER_DAY).run();
    if (!reserved.meta.changes) return c.json({ error: 'Bugünkü ücretsiz demo sınırına ulaşıldı.' }, 429);
  } catch {
    return c.json({ error: 'Demo kotası kontrol edilemedi.' }, 503);
  }

  const prompt = `${SYSTEM_PROMPT}\nSoru: ${question}`;
  const infer = async (adapter: boolean) => {
    const started = performance.now();
    try {
      const output = await c.env.AI.run(c.env.BASE_MODEL, {
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 120,
        temperature: 0,
        ...(adapter ? { lora: c.env.LORA_ID } : {}),
      });
      const raw = output.response ?? '';
      const plan = parsePlan(raw);
      const { sql, binds } = compilePlan(plan, c.env.REFERENCE_DATE);
      const rows = await c.env.DB.prepare(sql).bind(...binds).all();
      return { ok: true, raw, plan, sql, rows: rows.results, latency_ms: Math.round(performance.now() - started) };
    } catch (error) {
      return { ok: false, error: error instanceof Error ? error.message : 'Model veya veritabanı hatası', latency_ms: Math.round(performance.now() - started) };
    }
  };

  const [base, lora] = await Promise.all([infer(false), infer(true)]);
  return c.json({ question, base, lora, reference_date: c.env.REFERENCE_DATE });
});

app.all('*', (c) => c.env.ASSETS.fetch(c.req.raw));

export default app;
