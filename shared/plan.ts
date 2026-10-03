import { z } from 'zod';

export const planSchema = z.object({
  metric: z.enum(['order_count', 'delayed_count', 'revenue', 'delivery_days']),
  group_by: z.enum(['none', 'branch', 'city']),
  period: z.enum(['all', 'last_30_days']),
  city: z.enum(['all', 'Ankara', 'İstanbul', 'İzmir']),
}).strict();

export type QueryPlan = z.infer<typeof planSchema>;

export const SYSTEM_PROMPT = `Türkçe operasyon sorusunu yalnızca JSON sorgu planına dönüştür. Açıklama, Markdown ve SQL yazma.
Şema: {"metric":"order_count|delayed_count|revenue|delivery_days","group_by":"none|branch|city","period":"all|last_30_days","city":"all|Ankara|İstanbul|İzmir"}
Metrikler: order_count tüm sipariş sayısı; delayed_count yalnızca geciken sipariş sayısı; revenue toplam satış tutarı; delivery_days ortalama teslimat günü.
İstenen şehir yoksa city=all, grup istenmiyorsa group_by=none, dönem yoksa period=all. Son 30 gün deniyorsa period=last_30_days.
Yalnızca bu alanları ve değerleri kullan.`;

export function parsePlan(raw: string): QueryPlan {
  const trimmed = raw.trim();
  if (!trimmed.startsWith('{') || !trimmed.endsWith('}')) {
    throw new Error('Model yalnızca JSON sorgu planı üretmeli.');
  }
  return planSchema.parse(JSON.parse(trimmed));
}

export function parseFirstPlan(raw: string): { plan: QueryPlan; format_warning?: string } {
  const text = raw.trim();
  if (!text.startsWith('{')) throw new Error('Model çıktısı JSON planıyla başlamalı.');
  let depth = 0;
  let quoted = false;
  let escaped = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') quoted = false;
    } else if (char === '"') quoted = true;
    else if (char === '{') depth++;
    else if (char === '}' && --depth === 0) {
      const plan = parsePlan(text.slice(0, i + 1));
      return text.slice(i + 1).trim()
        ? { plan, format_warning: 'Model planın ardından ek metin üretti; yalnızca ilk doğrulanmış plan kullanıldı.' }
        : { plan };
    }
  }
  throw new Error('Model tamamlanmış bir JSON planı üretmedi.');
}

export function compilePlan(plan: QueryPlan, referenceDate: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(referenceDate)) {
    throw new Error('Geçersiz referans tarihi.');
  }

  const metric = {
    order_count: 'COUNT(*)',
    delayed_count: "SUM(CASE WHEN status = 'delayed' THEN 1 ELSE 0 END)",
    revenue: 'ROUND(SUM(amount_try), 2)',
    delivery_days: 'ROUND(AVG(delivery_days), 2)',
  }[plan.metric];
  const group = { none: null, branch: 'branch', city: 'city' }[plan.group_by];
  const where: string[] = [];
  const binds: string[] = [];
  if (plan.period === 'last_30_days') {
    where.push("order_date >= date(?, '-29 days') AND order_date <= ?");
    binds.push(referenceDate, referenceDate);
  }
  if (plan.city !== 'all') {
    where.push('city = ?');
    binds.push(plan.city);
  }
  const sql = `SELECT ${group ? `${group} AS segment, ` : "'Tümü' AS segment, "}${metric} AS value FROM orders${where.length ? ` WHERE ${where.join(' AND ')}` : ''}${group ? ` GROUP BY ${group}` : ''} ORDER BY segment LIMIT 20`;
  return { sql, binds };
}
