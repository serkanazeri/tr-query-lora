# Deney sonuçları — 3 Ekim 2026

## İlk adapterın eğitim koşulları

Gemma 2B IT, standart PEFT LoRA ile Apple M4 Pro üzerinde 240 adım eğitildi. 768 sentetik eğitim ve 96 doğrulama örneği kullanıldı. Adapter `q_proj` ve `v_proj` katmanlarında `r=8`, `alpha=16`, dropout `0.05` ayarlarını taşır; 4 bit kuantizasyon yoktur. Yaklaşık 2,5 milyar temel parametrenin 921.600'ü (%0,0368) eğitilebilir durumdaydı. Adapter dosyası 3,5 MB'tır. Eğitim yaklaşık 10 dakika sürdü. Python 3.10.11, PyTorch 2.14.1, Transformers 4.57.6 ve PEFT 0.21.2 kullanıldı.

## İlk adapterın ayrılmış sentetik testi: 96 soru

Her soru önce temel modele, sonra aynı temele takılan LoRA adapterına yöneltildi. Gemma chat template'i, deterministik çözümleme, 120 token sınırı ve `<end_of_turn>` bitiş tokenı iki koşulda aynıydı. Soruların cümle kalıpları eğitimden ayrıdır; metrik, gruplama, dönem ve şehir kombinasyonları eğitimde de görülmüştür. İlk adapter için [96 örneğin tüm beklenen planları, ham yanıtları ve tekil sonuçları](../reports/v1-held-out-96.json) yayımlanmıştır.

| Ölçüm | Temel model | LoRA |
| --- | ---: | ---: |
| Geçerli dört alanlı JSON planı | 0/96 (%0) | 96/96 (%100) |
| Tam plan eşleşmesi | 0/96 (%0) | 96/96 (%100) |
| Sentetik SQLite sorgu sonucu eşitliği | 0/96 (%0) | 96/96 (%100) |
| Yerel çıkarım gecikmesi, p50 | 1.775 ms | 870 ms |

Temel model genellikle Markdown veya şemadaki seçeneklerin listesini ürettiği için katı biçim kapısından geçemedi. LoRA sonucu, bu dört alanlı dar görev ve aynı kombinasyonlar üzerindedir; %100 değeri genel dil yeteneğini göstermez. Gecikme tek cihazda sıralı çalıştırmadan gelir ve bulut servis gecikmesiyle karşılaştırılamaz.

## İlk adapterın doğal ifade testi ve düzeltme kararı

İlk adapter, ayrı 12 soruluk [challenge kümesinde](../reports/v1-challenge-12.json) 12/12 geçerli JSON planı, fakat yalnızca **5/12 tam doğru plan** ve **5/12 doğru sorgu sonucu** üretti. Temel model yine 0/12 geçerli planda kaldı. Yedi yanlış planın altısında istenen `branch` veya `city` gruplaması `none` seçildi; birinde ciro yerine teslimat süresi seçildi.

Bu bulgu üzerine eğitim kümesine aynı soruları kopyalamadan farklı gruplama ve dönem söyleyişleri eklendi. İlk challenge sonucu silinmedi; ikinci adapterın tasarımında kullanıldığı için artık bağımsız değerlendirme sayılmaz. İkinci eğitimden önce yeni bir 12 soruluk `audit` kümesi ayrıldı. Her iki küme de küçük ve bağımsız insan değerlendirmesinden geçmedi.

## İkinci adapterın etkisi

İkinci adapter, 192 yeni sentetik gruplama/dönem sorusuyla toplam 960 eğitim örneği üzerinde 320 adım eğitildi. Temel ağırlıklar ve LoRA yapılandırması değişmedi. Eğitim 13 dakika 40 saniye sürdü; son doğrulama loss değeri `0.0117` idi. İlk ve ikinci adapterlar aynı temel model, istem, bitiş tokenı ve test sorularıyla ölçüldü.

| Ayrı küme | Temel model | İlk LoRA | İkinci LoRA |
| --- | ---: | ---: | ---: |
| 12 doğal ifade sorusu, tam plan | 0/12 | [5/12](../reports/v1-challenge-12.json) | [9/12](../reports/v2-challenge-12.json) |
| 12 yeni audit sorusu, tam plan | 0/12 | [4/12](../reports/v1-audit-12.json) | [7/12](../reports/v2-audit-12.json) |

İki LoRA adapterı bu iki kümede de 12/12 kez geçerli biçimde JSON üretti. Challenge kümesi ikinci sürümü tasarlamada kullanıldı; bu satır bağımsız doğrulama değildir. Audit kümesinde tam soru çakışması yoktur, ancak sadece 12 sentetik etiketli soru içerir. İkinci adapterın beş audit hatası gruplama ve ciro ifadelerinde yoğunlaşır; [tekil çıktılar](../reports/v2-audit-12.json) incelenebilir.

96 soruluk ayrılmış sentetik testte ikinci adapter da **96/96 geçerli, 96/96 tam doğru plan ve 96/96 aynı sorgu sonucu** üretti; p50 yerel çıkarım gecikmesi **868 ms** idi. Temel model yine 0/96 geçerli planda kaldı. [Tam ikinci sürüm raporu](../reports/v2-held-out-96.json) ve [ilk sürüm raporu](../reports/v1-held-out-96.json) ayrı yayımlanmıştır. Bu testteki tavan sonuç, doğal ifade kümesindeki hataları ortadan kaldırmaz.

## İlk adapterın canlı Worker denemesi

Üç örnek soru [canlı demo](https://tr-query-lora.serkanazeri.workers.dev) API'sine gönderildi. Her üçünde LoRA'nın ilk JSON nesnesi şemadan geçti ve D1 sonucu döndü; temel model üçünde de şemaya uygun bir JSON planıyla başlamadı. LoRA her üçünde de JSON sonrasında ek metin üretti; demo bunu uyarıyla ve açılabilir ham çıktıyla gösterir. İlk nesne dışında kalan metin SQL'e aktarılmaz.

| Soru | LoRA planı | D1 sonucu | Değerlendirme |
| --- | --- | --- | --- |
| Son 30 günde geciken siparişleri şubeye göre say | `delayed_count`, `branch`, `last_30_days`, `all` | 6 şubenin her birinde 1 | İstenen alanlarla uyumlu |
| Ankara siparişlerinin toplam cirosu ne kadar? | `revenue`, `none`, `all`, `Ankara` | 9.970 TL | İstenen alanlarla uyumlu |
| İzmir için ortalama teslimat süresini şubelere ayır | `delivery_days`, **`none`**, `all`, `İzmir` | 5,17 gün tek toplam | **Yanlış:** istenen `branch` gruplaması kaçırıldı |

Bu üç soru temsilî bir başarı oranı oluşturmaz. Üçüncü hata, geçerli JSON ve güvenli SQL'in doğru iş yanıtı için yeterli olmadığını gösterir. Kullanıcı demoda planı ve sonucu yan yana inceleyebilir.

## Yayındaki ikinci adapterın canlı kontrolü

`tr-query-gemma2b-v2-20261003` Cloudflare Workers AI'ya yüklendikten sonra aynı üç soru yeniden gönderildi. Temel model üçünde de geçerli JSON planıyla başlamadı. LoRA'nın ilk JSON nesnesi üçünde de beklenen alanları taşıdı ve D1 sonuçları döndü:

| Soru özeti | LoRA planı | D1 sonucu |
| --- | --- | --- |
| Son 30 günde gecikenleri şubeye göre say | `delayed_count`, `branch`, `last_30_days`, `all` | Altı şubenin her birinde 1 |
| Ankara toplam ciro | `revenue`, `none`, `all`, `Ankara` | 9.970 TL |
| İzmir ortalama teslimatı şubelere ayır | `delivery_days`, `branch`, `all`, `İzmir` | Bornova 5,67 gün; Konak 4,67 gün |

Bu canlı kontrolde ilk adapterın üçüncü sorudaki gruplama hatası giderildi. LoRA her üç yanıtta da JSON sonrasında metin üretmeye devam etti; ilk nesne şemayla doğrulanıp kullanıldı, geri kalanı uyarı ve ham çıktı olarak görünür kaldı. 3/3 canlı örnek, 12 soruluk audit kümesindeki 7/12 hatalarını geçersiz kılmaz.

## Ölçümün sınırları

Yerel testte Gemma chat template'i ve `<end_of_turn>` bitiş tokenı kullanılır. Bulut modelinin bitiş davranışı farklı gözlendi; canlı demoda ilk tamamlanmış ve şemaya uyan JSON planı kullanılabilir, ancak uyarı kaldırılmaz. Yerel doğruluk rakamları bulut doğruluğu diye sunulmaz. Test soruları sentetiktir, aynı dört alanın kombinasyonları eğitimde görülmüştür ve insan tarafından bağımsız değerlendirilmemiştir. Challenge kümesi ikinci sürüm için geliştirme verisine dönüşmüştür; yeni audit kümesi yalnızca 12 sorudan oluşur.
