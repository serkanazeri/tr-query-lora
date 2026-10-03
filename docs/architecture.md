# Mimari ve sınırlar

## Problem ayrıştırması

Model dört alan üretir: `metric`, `group_by`, `period`, `city`. Bu değerler kapalı bir enum kümesinden gelir. SQL oluşturma, model cevabından bağımsız sabit kodda yapılır. Böylece LoRA'nın ölçtüğü beceri Türkçe niyeti şemaya eşleme olur; serbest SQL üretimi ve onun güvenlik yüzeyi bu deneyin parçası değildir.

## İstek akışı

1. Worker 8–240 karakter arası soruyu kabul eder.
2. Hesap genelindeki ücretsiz AI kotasına ek olarak, D1'de günde en fazla 10 karşılaştırmalık uygulama sınırı rezerve eder.
3. Temel modele ve LoRA adapterına eğitimdeki Gemma chat template'i ile aynı ham istemi, sıcaklık 0 ve aynı çıktı sınırıyla gönderir.
4. İlk tamamlanmış JSON nesnesini dört alanlı şemayla doğrular. Fazla alan veya enum dışı değerleri reddeder. Model nesneden sonra metin üretirse bunu uyarıyla ve ham çıktıda gösterir.
5. Geçerli planı parametreli ve salt okunur SQL'e dönüştürür. `city` değeri SQL metnine eklenmez; bind parametresi olur.
6. D1 sonucunu, planı ve gecikmeyi arayüzde gösterir. Hatalar karşılaştırmanın ilgili tarafında görünür.

`demo_usage` rezervasyonu başarısız istekte geri alınmaz. Bu, ücretsiz kota koruması için muhafazakâr bir tercihtir; başarılı kullanıcı deneyimi sayacı değildir. Gün sınırı UTC'ye göre döner. Cloudflare Workers AI kotası diğer uygulamalarla paylaşılır.

## Veriler

18 sentetik sipariş, üç şehir ve altı şubeye dağılır. Miktarlar ve teslimat günleri kurgu veridir. `2026-09-30` tarihi sonuçların zamanla değişmesini engeller. Gerçek müşteri verisi, kimlik bilgisi veya işveren verisi kullanılmaz.

## Model ve eğitim sınırı

Eğitimde kullanılan ağırlıklar `google/gemma-2b-it`; Workers AI'da LoRA uyumlu model `@cf/google/gemma-2b-it-lora` kullanılır. Cloudflare'ın aynı istemde JSON sonrasında fazladan metin üretebildiği üç canlı örnekte görüldü. Yerel test katı tam JSON ölçer; canlı demo ilk doğrulanmış planı ayrıca kullanabilir. Bu nedenle yerel ve bulut çıktıları eşdeğer sayılmaz.
