# Mimari ve sınırlar

## Problem ayrıştırması

Model dört alan üretir: `metric`, `group_by`, `period`, `city`. Bu değerler kapalı bir enum kümesinden gelir. SQL oluşturma, model cevabından bağımsız sabit kodda yapılır. Böylece LoRA'nın ölçtüğü beceri Türkçe niyeti şemaya eşleme olur; serbest SQL üretimi ve onun güvenlik yüzeyi bu deneyin parçası değildir.

## İstek akışı

1. Worker 8–240 karakter arası soruyu kabul eder.
2. Hesap genelindeki ücretsiz AI kotasına ek olarak, D1'de günde en fazla 10 karşılaştırmalık uygulama sınırı rezerve eder.
3. Temel modele ve LoRA adapterına aynı kullanıcı mesajı, sıcaklık 0 ve aynı çıktı sınırıyla çağrı yapar.
4. Tam JSON olmayan, fazla alan taşıyan veya enum dışına çıkan yanıtı reddeder.
5. Geçerli planı parametreli ve salt okunur SQL'e dönüştürür. `city` değeri SQL metnine eklenmez; bind parametresi olur.
6. D1 sonucunu, planı ve gecikmeyi arayüzde gösterir. Hatalar karşılaştırmanın ilgili tarafında görünür.

`demo_usage` rezervasyonu başarısız istekte geri alınmaz. Bu, ücretsiz kota koruması için muhafazakâr bir tercihtir; başarılı kullanıcı deneyimi sayacı değildir. Gün sınırı UTC'ye göre döner. Cloudflare Workers AI kotası diğer uygulamalarla paylaşılır.

## Veriler

18 sentetik sipariş, üç şehir ve altı şubeye dağılır. Miktarlar ve teslimat günleri kurgu veridir. `2026-09-30` tarihi sonuçların zamanla değişmesini engeller. Gerçek müşteri verisi, kimlik bilgisi veya işveren verisi kullanılmaz.

## Model ve eğitim sınırı

Eğitimde kullanılan ağırlıklar `google/gemma-2b-it`; Workers AI'da buna karşılık gelen LoRA uyumlu model `@cf/google/gemma-2b-it-lora` hedeflenir. İki ortamın tokenizer/chat-template ve adapter uyumu, canlı yükleme sonrası aynı sabit örneklerde ayrı doğrulanmalıdır. Yerel değerlendirme başarılı olsa da bu, Cloudflare çıkarımının eşdeğer olduğu anlamına gelmez.
