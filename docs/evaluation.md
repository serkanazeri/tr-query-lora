# Değerlendirme yöntemi

## Veri üretimi

`training/generate_data.py` sabit `20261003` tohumuyla örnek üretir. Güncel sayılar `data/manifest.json` içindedir. Eğitim, doğrulama ve test cümle kalıpları ayrıdır. Soru birleşimindeki metrik, grup, dönem ve şehir değerleri split'ler arasında tekrar eder. Bu test parafraz dayanıklılığına dair dar bir sinyal verir; yeni müşteri şeması için kanıt vermez.

`data/challenge.jsonl` 12 daha doğal Türkçe soru içerir. İlk adapterın gruplama ifadelerindeki hataları burada görülünce ikinci eğitim veri tasarımı bu gözleme göre değiştirildi. Bu yüzden challenge artık ikinci adapter için bağımsız test değil, geliştirme/diagnostik kümesidir. `data/audit.jsonl` ikinci eğitim başlamadan önce hazırlanmış, eğitim, test ve challenge sorularıyla birebir çakışmayan 12 ayrı sorudur. Her iki küçük kümenin etiketleri proje için hazırlanmıştır; bağımsız insan incelemesi yoktur.

## Eğitim

`training/train.py` temel model ağırlıklarını dondurur; PEFT LoRA'yı `q_proj` ve `v_proj` üzerine `r=8`, `alpha=16`, dropout `0.05` ile ekler. İlk adapter 240, yayındaki ikinci adapter 320 optimizasyon adımı ve sabit seed kullanır. 4 bit kuantizasyon yoktur. Chat template ile yalnızca model cevabı loss'a katılır; kullanıcı sorusu maskelenir. Uzun örnek sessizce kesilmez, hata verir.

## Aynı koşullu karşılaştırma

`training/evaluate.py` test split'ini önce temel modelle, sonra aynı temele takılmış adapterla yürütür. İki koşulda aynı soru, chat template, `max_new_tokens=120`, Gemma `<end_of_turn>` bitiş tokenı ve deterministik çözümleme kullanılır. Rapor şu ölçümleri içerir:

```bash
.venv/bin/python training/evaluate.py --adapter artifacts/lora-v2 --limit 96
.venv/bin/python training/evaluate.py --adapter artifacts/lora-v2 --dataset data/challenge.jsonl --limit 12 --output artifacts/challenge-v2-evaluation.json
.venv/bin/python training/evaluate.py --adapter artifacts/lora-v2 --dataset data/audit.jsonl --limit 12 --output artifacts/audit-v2-evaluation.json
```

| Ölçüm | Anlamı | Sınırı |
| --- | --- | --- |
| Geçerli plan oranı | Çıktı katı dört alanlı JSON şemasına uyuyor mu? | İş sonucu doğru olmayabilir. |
| Tam plan doğruluğu | Dört alanın hepsi beklenen değerle aynı mı? | Aynı sonucu veren iki farklı planı farklı sayabilir. |
| Sorgu sonucu eşitliği | Üretilen plan ve hedef plan aynı sentetik veriyi döndürüyor mu? | Küçük veri hatalı planları tesadüfen eşit gösterebilir. |
| Gecikme p50 | Yerel aynı cihazdaki tekil çıkarım süresi | Eşzamanlı trafik ve bulut p95 değildir. |

Ham örnekler ve hatalar `artifacts/evaluation.json` dosyasına veya `--output` ile seçilen yola yazılır. İncelenen 96 soruluk [ilk adapter raporu](../reports/v1-held-out-96.json) ve [ikinci adapter raporu](../reports/v2-held-out-96.json), özet ve canlı hatalarla birlikte [sonuç sayfasında](results.md) yayımlanır. Sentetik veriyi insan gözden geçirmeden genel Türkçe yetenek iddiası yapılmaz.

## Kabul kapısı

Model deneyinin başarılı sayılması için adapter dosyaları oluşmalı; base ve LoRA aynı test setinde çalışmalı; plan ve yürütme metrikleri raporlanmalı; en az üç hedefli canlı Worker karşılaştırması yerel sonuçlarla incelenmelidir. LoRA temel modelden iyi çıkmazsa bu sonuç saklanmaz; proje yine karar ve hata analizi olarak belgelenir.
