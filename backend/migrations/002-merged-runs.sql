-- 002: 同一研究合并为单次计算（每研究至多一条运行），并记录尝试次数与更新时间。
-- 全新环境由 SQLAlchemy metadata.create_all 按最新模型建表；本脚本供已存在数据的环境演进。
-- 兼容 MySQL 8.4（不支持 ADD COLUMN IF NOT EXISTS），用 information_schema 守卫，可重复执行。

SET @db_name := DATABASE();

SET @sql := (SELECT IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA=@db_name AND TABLE_NAME='envelope_runs' AND COLUMN_NAME='attempts')=0,
  'ALTER TABLE envelope_runs ADD COLUMN attempts INT NOT NULL DEFAULT 0',
  'SELECT 1'));
PREPARE stmt FROM @sql;EXECUTE stmt;DEALLOCATE PREPARE stmt;

SET @sql := (SELECT IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA=@db_name AND TABLE_NAME='envelope_runs' AND COLUMN_NAME='updated_at')=0,
  'ALTER TABLE envelope_runs ADD COLUMN updated_at VARCHAR(64) NOT NULL DEFAULT ''''',
  'SELECT 1'));
PREPARE stmt FROM @sql;EXECUTE stmt;DEALLOCATE PREPARE stmt;

-- 历史上同一研究可能产生多条运行：保留最早一条作为合并后的运行，删除其余重复行。
-- 若重复行已被复核或归档引用（外键），先把引用改挂到保留运行，保证复核归档不丢失。
UPDATE footprint_reviews r
  JOIN envelope_runs dup ON r.run_id = dup.id
  JOIN (
    SELECT study_id, MIN(id) AS keep_id
    FROM envelope_runs
    GROUP BY study_id
    HAVING COUNT(*) > 1
  ) k ON dup.study_id = k.study_id
SET r.run_id = k.keep_id
WHERE dup.id <> k.keep_id;

UPDATE reports rp
  JOIN envelope_runs dup ON rp.run_id = dup.id
  JOIN (
    SELECT study_id, MIN(id) AS keep_id
    FROM envelope_runs
    GROUP BY study_id
    HAVING COUNT(*) > 1
  ) k ON dup.study_id = k.study_id
SET rp.run_id = k.keep_id
WHERE dup.id <> k.keep_id;

DELETE dup FROM envelope_runs dup
  JOIN (
    SELECT study_id, MIN(id) AS keep_id
    FROM envelope_runs
    GROUP BY study_id
    HAVING COUNT(*) > 1
  ) k ON dup.study_id = k.study_id
WHERE dup.id <> k.keep_id;

SET @sql := (SELECT IF(
  (SELECT COUNT(*) FROM information_schema.STATISTICS
   WHERE TABLE_SCHEMA=@db_name AND TABLE_NAME='envelope_runs' AND INDEX_NAME='uq_envelope_runs_study')=0,
  'ALTER TABLE envelope_runs ADD UNIQUE KEY uq_envelope_runs_study (study_id)',
  'SELECT 1'));
PREPARE stmt FROM @sql;EXECUTE stmt;DEALLOCATE PREPARE stmt;
