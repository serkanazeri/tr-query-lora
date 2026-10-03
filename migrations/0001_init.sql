CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY,
  order_date TEXT NOT NULL,
  city TEXT NOT NULL CHECK (city IN ('Ankara', 'İstanbul', 'İzmir')),
  branch TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('delivered', 'delayed')),
  amount_try REAL NOT NULL CHECK (amount_try >= 0),
  delivery_days INTEGER NOT NULL CHECK (delivery_days >= 0)
);

CREATE TABLE IF NOT EXISTS demo_usage (
  day TEXT PRIMARY KEY,
  comparisons INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO orders (id, order_date, city, branch, status, amount_try, delivery_days) VALUES
  (1,'2026-09-28','İstanbul','Kadıköy','delivered',1490,2),
  (2,'2026-09-27','İstanbul','Kadıköy','delayed',2350,7),
  (3,'2026-09-24','İstanbul','Beşiktaş','delivered',890,3),
  (4,'2026-09-23','İstanbul','Beşiktaş','delayed',3100,8),
  (5,'2026-09-20','Ankara','Çankaya','delivered',1790,2),
  (6,'2026-09-18','Ankara','Çankaya','delayed',2250,6),
  (7,'2026-09-15','Ankara','Keçiören','delivered',1190,4),
  (8,'2026-09-14','Ankara','Keçiören','delayed',2740,9),
  (9,'2026-09-11','İzmir','Konak','delivered',960,3),
  (10,'2026-09-09','İzmir','Konak','delayed',1850,7),
  (11,'2026-09-05','İzmir','Bornova','delivered',1300,2),
  (12,'2026-09-02','İzmir','Bornova','delayed',2180,6),
  (13,'2026-08-30','İstanbul','Kadıköy','delivered',990,3),
  (14,'2026-08-28','İstanbul','Beşiktaş','delayed',3040,10),
  (15,'2026-08-20','Ankara','Çankaya','delivered',720,2),
  (16,'2026-08-14','Ankara','Keçiören','delayed',1280,8),
  (17,'2026-08-09','İzmir','Konak','delivered',1410,4),
  (18,'2026-07-29','İzmir','Bornova','delayed',1990,9);
