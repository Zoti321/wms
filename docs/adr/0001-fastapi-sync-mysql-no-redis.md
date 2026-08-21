# MVP：FastAPI 同步写库 + MySQL，不上 Redis

仓脉 WMS 后端以 FastAPI + MySQL 8.0 承载库存唯一账本；出库软分配/实扣必须在单事务内完成。我们选定 SQLAlchemy **同步 Session** 处理库存写路径（边界清晰、面试与排障成本低），并在 MVP **不上 Redis/任务队列**：幂等键与业务数据落 MySQL，库存预警在记账成功后同步判定。若日后读多写少需要缓存或异步任务，可再引入 Redis/Worker，但不得把缓存当作库存真相。
