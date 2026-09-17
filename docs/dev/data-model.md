# 数据模型（核心）

## ER 关系（文字版）

Warehouse 1—N Location；SKU 跨仓共享；Inventory 为（Warehouse × SKU × Location）余额；InboundOrder / OutboundOrder 1—N Line，均属 Warehouse；每次上架/拣货/盈亏写 InventoryLedger（含 ref_line_id）。

## 关键表（简化 DDL 示意）

```sql
CREATE TABLE warehouse (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  warehouse_code  VARCHAR(64) NOT NULL UNIQUE,
  name            VARCHAR(200) NOT NULL,
  status          TINYINT NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE sku (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku_code      VARCHAR(64) NOT NULL UNIQUE,
  name          VARCHAR(200) NOT NULL,
  unit          VARCHAR(16) NOT NULL,
  safety_stock  DECIMAL(18,3) NOT NULL DEFAULT 0,
  status        TINYINT NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE location (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  warehouse_id  BIGINT NOT NULL,
  location_code VARCHAR(64) NOT NULL,
  zone          VARCHAR(32),
  status        TINYINT NOT NULL DEFAULT 1, -- 含盘点锁等作业状态
  UNIQUE (warehouse_id, location_code),
  CONSTRAINT fk_location_wh FOREIGN KEY (warehouse_id) REFERENCES warehouse(id)
) ENGINE=InnoDB;

CREATE TABLE inventory (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  warehouse_id  BIGINT NOT NULL,
  sku_id        BIGINT NOT NULL,
  location_id   BIGINT NOT NULL,
  qty_on_hand   DECIMAL(18,3) NOT NULL DEFAULT 0,
  qty_frozen    DECIMAL(18,3) NOT NULL DEFAULT 0,
  version       BIGINT NOT NULL DEFAULT 0,
  UNIQUE (warehouse_id, sku_id, location_id)
  -- qty_available = qty_on_hand - qty_frozen（查询计算或生成列）
) ENGINE=InnoDB;

CREATE TABLE inventory_ledger (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  warehouse_id  BIGINT NOT NULL,
  sku_id        BIGINT NOT NULL,
  location_id   BIGINT NOT NULL,
  change_qty    DECIMAL(18,3) NOT NULL,
  bal_qty       DECIMAL(18,3) NOT NULL,
  ref_type      VARCHAR(32) NOT NULL,  -- PUTAWAY / ALLOCATE / PICK / RELEASE / STOCKTAKE
  ref_id        BIGINT NOT NULL,
  ref_line_id   BIGINT NULL,
  ref_no        VARCHAR(64) NOT NULL,
  operator_id   BIGINT NOT NULL,
  created_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;
```

## 分配伪代码

在事务内：

```sql
UPDATE inventory
SET qty_frozen = qty_frozen + :q, version = version + 1
WHERE id = :id AND version = :ver AND (qty_on_hand - qty_frozen) >= :q
```

- **实扣**：同步减少 `qty_frozen` 与 `qty_on_hand`
- **释放预留**：仅减少 `qty_frozen`
