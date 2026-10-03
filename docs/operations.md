# Dağıtım, maliyet ve işletim

## Planlanan yayın akışı

1. Yerel eğitim ve 96 soruluk test raporunu doğrula.
2. `python training/prepare_upload.py` ile Cloudflare LoRA kısıtlarını denetle ve ayrı yükleme klasörünü üret: desteklenen model, `r=8`, adapter dosyaları `<300 MB`, `adapter_config.json` içinde `model_type=gemma`.
3. `wrangler ai finetune create @cf/google/gemma-2b-it-lora <name> artifacts/cloudflare-upload` ile adapterı yükle. Üretilen kimliği `LORA_ID` olarak kaydet.
4. Ayrı `tr-query` D1 veritabanını oluştur ve sentetik veri migration'ını uygula. **Tamamlandı:** uzak veritabanında 18 sipariş doğrulandı.
5. `npm run build` ve `wrangler deploy` çalıştır.
6. HTTPS demo URL'sinde durum, üç gerçek model karşılaştırması, kota davranışı, mobil görünüm ve veritabanı sonucu doğrula. URL'yi README'ye ancak sonra ekle.

Model eğitimi, adapter yükleme ve Worker yayını henüz tamamlanmadı. Config'de gerçek D1 kimliği ve boş `LORA_ID` vardır; uygulama adapter hazır olmadan karşılaştırmayı açmaz.

## Ücretsiz sınırlar

Apple M4 Pro üzerinde yerel eğitim için ücretli GPU servisi gerekmez; elektrik, indirme ve disk kullanımı sıfır kaynak maliyeti değildir. Workers AI LoRA özelliği [açık beta sırasında ücretsiz](https://developers.cloudflare.com/workers-ai/features/fine-tunes/loras/). Cloudflare'ın [ücretsiz AI tahsisi](https://developers.cloudflare.com/workers-ai/platform/pricing/) hesap genelinde günlük 10.000 Neuron'dur; diğer demolarla paylaşılır ve şartlar değişebilir. Uygulama günde 10 karşılaştırma rezerve eder. Kota dolduğunda yeni model çağrısı yapılmaz; otomatik ücretli sağlayıcıya geçilmez.

## Gizlilik ve kurtarma

Demo yalnızca sentetik veri kullanır. Ham ziyaretçi soruları veritabanına yazılmaz. İstekler Cloudflare AI'ya gönderilir; ziyaretçiler gerçek kişisel veya ticari veri girmemelidir. Yeni adapter güncellemesi yeni fine-tune kaydı gerektirir; önceki `LORA_ID` korunarak geri alınabilir. D1 migration geri alma varsayılmamalı; yeni şema değişiklikleri ayrı incelenmelidir.
