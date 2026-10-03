import { describe, expect, it } from 'vitest';
import { compilePlan, parsePlan } from './plan';

describe('model plan boundary', () => {
  it('rejects prose, extra keys and arbitrary SQL', () => {
    expect(() => parsePlan('```json\n{}\n```')).toThrow();
    expect(() => parsePlan('{"metric":"order_count","group_by":"none","period":"all","city":"all","sql":"DROP TABLE orders"}')).toThrow();
  });

  it('compiles only fixed read queries with bound filters', () => {
    const plan = parsePlan('{"metric":"delayed_count","group_by":"branch","period":"last_30_days","city":"Ankara"}');
    const query = compilePlan(plan, '2026-09-30');
    expect(query.sql).toContain('GROUP BY branch');
    expect(query.sql).toContain('city = ?');
    expect(query.binds).toEqual(['2026-09-30', '2026-09-30', 'Ankara']);
    expect(query.sql).not.toContain('Ankara');
  });
});
