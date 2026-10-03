# Dağıtım, maliyet ve işletim

## Yayın durumu

İlk 240 adımlık ve ikinci 320 adımlık yerel eğitim tamamlandı. `training/prepare_upload.py` özgün adapterı değiştirmeden Cloudflare için iki dosyalı yükleme klasörü hazırladı. Yayındaki adapter kimliği `tr-query-gemma2b-v2-20261003`; önceki `tr-query-gemma2b-20261003` geri dönüş için korunur. D1 veritabanı `tr-query`, Worker URL'si [tr-query-lora.serkanazeri.workers.dev](https://tr-query-lora.serkanazeri.workers.dev). Uzak veritabanında 18 sentetik sipariş var. İkinci adapterla üç gerçek karşılaştırma, API durumu ve D1 sonuçları doğrulandı. Gözlenen yanlış planlar ve ek çıktı [sonuç raporunda](results.md) yer alır.

Yeniden yayımlama: `npm run deploy`. Yeni adapter yüklemesi gerektiğinde `.venv/bin/python training/prepare_upload.py --adapter artifacts/lora-v2 --output artifacts/cloudflare-upload-v2` ardından `wrangler ai finetune create @cf/google/gemma-2b-it-lora <name> artifacts/cloudflare-upload-v2` çalıştırılır; `wrangler.jsonc` içindeki `LORA_ID` yeni isimle güncellenir. Kota dolmadan önce son dağıtım canlı URL'de doğrulanmalıdır.

## Ücretsiz sınırlar

Apple M4 Pro üzerinde yerel eğitim için ücretli GPU servisi gerekmez; elektrik, indirme ve disk kullanımı sıfır kaynak maliyeti değildir. Workers AI LoRA özelliği [açık beta sırasında ücretsiz](https://developers.cloudflare.com/workers-ai/features/fine-tunes/loras/). Cloudflare'ın [ücretsiz AI tahsisi](https://developers.cloudflare.com/workers-ai/platform/pricing/) hesap genelinde günlük 10.000 Neuron'dur; diğer demolarla paylaşılır ve şartlar değişebilir. Uygulama günde 10 karşılaştırma rezerve eder. Kota dolduğunda yeni model çağrısı yapılmaz; otomatik ücretli sağlayıcıya geçilmez.

## Gizlilik ve kurtarma

Demo yalnızca sentetik veri kullanır. Ham ziyaretçi soruları veritabanına yazılmaz. İstekler Cloudflare AI'ya gönderilir; ziyaretçiler gerçek kişisel veya ticari veri girmemelidir. Yeni adapter güncellemesi yeni fine-tune kaydı gerektirir; önceki `LORA_ID` korunarak geri alınabilir. D1 migration geri alma varsayılmamalı; yeni şema değişiklikleri ayrı incelenmelidir.
