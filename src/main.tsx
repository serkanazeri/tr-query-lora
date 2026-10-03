import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Result = { ok: true; raw: string; plan: Record<string, string>; sql: string; rows: Array<{ segment: string; value: number }>; latency_ms: number }
  | { ok: false; raw: string; error: string; latency_ms: number };
type Comparison = { question: string; base: Result; lora: Result; reference_date: string };
type Status = { model: string; adapter_ready: boolean; reference_date: string; dataset: string; daily_demo_limit: number };

const examples = [
  'Son 30 günde geciken siparişleri şubeye göre say',
  'Ankara siparişlerinin toplam cirosu ne kadar?',
  'İzmir için ortalama teslimat süresini şubelere ayır',
];

function ResultCard({ title, result }: { title: string; result: Result }) {
  return <section className="result-card">
    <div className="result-heading"><h3>{title}</h3><span>{result.latency_ms} ms</span></div>
    {result.ok ? <>
      <div className="label">Model çıktısı</div><pre>{JSON.stringify(result.plan, null, 2)}</pre>
      <div className="label">Derlenen salt okunur sorgu</div><code className="sql">{result.sql}</code>
      <div className="label">Veritabanı sonucu</div>
      <table><thead><tr><th>Grup</th><th>Değer</th></tr></thead><tbody>{result.rows.map((row, i) => <tr key={i}><td>{row.segment}</td><td>{row.value}</td></tr>)}</tbody></table>
    </> : <div className="result-error">{result.error}</div>}
    {result.raw && <details><summary>Ham model çıktısı</summary><pre>{result.raw}</pre></details>}
  </section>;
}

function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [question, setQuestion] = useState(examples[0]);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { fetch('/api/status').then((res) => res.json() as Promise<Status>).then(setStatus).catch(() => setError('API durumuna ulaşılamadı.')); }, []);

  async function compare(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true); setError(''); setComparison(null);
    try {
      const response = await fetch('/api/compare', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) });
      const data = await response.json() as Comparison & { error?: string };
      if (!response.ok) throw new Error(data.error ?? 'Karşılaştırma yapılamadı.');
      setComparison(data);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Bilinmeyen hata'); }
    finally { setLoading(false); }
  }

  return <main className="shell">
    <header><a className="brand" href="/">TR<span>·</span>QUERY</a><span className="tag">LoRA deney laboratuvarı</span></header>
    <div className="hero"><div className="eyebrow">TÜRKÇE ANALİTİK · AÇIK KARŞILAŞTIRMA</div><h1>Bir soru.<br /><em>İki model davranışı.</em></h1>
      <p>Türkçe iş sorusundan güvenli bir sorgu planı çıkarıyoruz. Aynı temel modeli LoRA adapterı olmadan ve adapterla çalıştırıp üretilen planı, SQL’i ve gerçek veri sonucunu yan yana gösteriyoruz.</p>
    </div>
    <div className="notice"><strong>Deney sınırı</strong><span>Veriler tamamen sentetiktir. Referans tarihi {status?.reference_date ?? '2026-09-30'}. Son 30 gün bu tarihe göre hesaplanır. Model serbest SQL çalıştıramaz; yalnızca doğrulanan plan derlenir.</span></div>
    <form onSubmit={compare} className="query-form"><label htmlFor="question">Operasyon sorusu</label><textarea id="question" value={question} maxLength={240} onChange={(e) => setQuestion(e.target.value)} rows={3} />
      <div className="form-foot"><div className="examples">{examples.map((example) => <button type="button" key={example} onClick={() => setQuestion(example)}>{example}</button>)}</div><button className="primary" type="submit" disabled={loading || !status?.adapter_ready}>{loading ? 'Karşılaştırılıyor…' : 'Modelleri karşılaştır →'}</button></div>
    </form>
    {!status?.adapter_ready && status && <div className="warning">Canlı LoRA adapterı henüz bağlı değil. Eğitim ve dağıtım tamamlandığında bu karşılaştırma etkinleşir.</div>}
    {error && <div className="warning" role="alert">{error}</div>}
    {comparison && <div className="results"><ResultCard title="Temel model" result={comparison.base} /><ResultCard title="LoRA uyarlanmış model" result={comparison.lora} /></div>}
    <footer><span>Model: {status?.model ?? 'yükleniyor'} · Günlük karşılaştırma sınırı: {status?.daily_demo_limit ?? '…'}</span><span>Kaynak kod, eğitim ve değerlendirme raporu GitHub’da yayımlanacak.</span></footer>
  </main>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
