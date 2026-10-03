# Değerlendirme yöntemi

## Veri üretimi

`training/generate_data.py` sabit `20261003` tohumuyla örnek üretir. Güncel sayılar `data/manifest.json` içindedir. Eğitim, doğrulama ve test cümle kalıpları ayrıdır. Soru birleşimindeki metrik, grup, dönem ve şehir değerleri split'ler arasında tekrar eder. Bu test parafraz dayanıklılığına dair dar bir sinyal verir; yeni müşteri şeması için kanıt vermez.

## Eğitim

`training/train.py` temel model ağırlıklarını dondurur; PEFT LoRA'yı `q_proj` ve `v_proj` üzerine `r=8`, `alpha=16`, dropout `0.05` ile ekler. Varsayılan 240 optimizasyon adımı ve sabit seed kullanılır. 4 bit kuantizasyon yoktur. Chat template ile yalnızca model cevabı loss'a katılır; kullanıcı sorusu maskelenir. Uzun örnek sessizce kesilmez, hata verir.

## Aynı koşullu karşılaştırma

`training/evaluate.py` test split'ini önce temel modelle, sonra aynı temele takılmış adapterla yürütür. İki koşulda aynı soru, chat template, `max_new_tokens=120` ve deterministik çözümleme kullanılır. Rapor şu ölçümleri içerir:

| Ölçüm | Anlamı | Sınırı |
| --- | --- | --- |
| Geçerli plan oranı | Çıktı katı dört alanlı JSON şemasına uyuyor mu? | İş sonucu doğru olmayabilir. |
| Tam plan doğruluğu | Dört alanın hepsi beklenen değerle aynı mı? | Aynı sonucu veren iki farklı planı farklı sayabilir. |
| Sorgu sonucu eşitliği | Üretilen plan ve hedef plan aynı sentetik veriyi döndürüyor mu? | Küçük veri hatalı planları tesadüfen eşit gösterebilir. |
| Gecikme p50 | Yerel aynı cihazdaki tekil çıkarım süresi | Eşzamanlı trafik ve bulut p95 değildir. |

Ham örnekler ve hatalar `artifacts/evaluation.json` dosyasına yazılır. Bu dosya ilk incelemeden önce Git dışında kalır. Kamuya açık özet, ancak gerçek koşu ve gözden geçirme sonrasında yayımlanır. Sentetik veriyi insan gözden geçirmeden genel Türkçe yetenek iddiası yapılmaz.

## Kabul kapısı

Model deneyinin başarılı sayılması için adapter dosyaları oluşmalı; base ve LoRA aynı test setinde çalışmalı; plan ve yürütme metrikleri raporlanmalı; en az üç hedefli canlı Worker karşılaştırması yerel sonuçlarla incelenmelidir. LoRA temel modelden iyi çıkmazsa bu sonuç saklanmaz; proje yine karar ve hata analizi olarak belgelenir.
