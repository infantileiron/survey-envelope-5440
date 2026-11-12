# 岚图测绘 · 采集足迹包络比较

在声明的局部米制平面中，对原始采集点比较凸包、轴对齐框与最小面积定向框，保留退化几何、来源快照和人工复核。

岚图测绘整理组是一个模拟的12人团队。上游提供 `lantu_local_footprints_20261112.json`，5组各120条米制点记录。原先人工画轴框：把凹点当边界、斜长足迹产生大量框外冗余、共线/单位置却返回伪多边形。本项目替代点组校验、去重口径锁定、几何包络计算到复核归档；下游是采集整理人员核对的足迹图册，不是地籍、地理边界或真实采集覆盖判定。

## 一天的整理流程

1. 09:00 导入600条模拟点，声明coordinate_system=local_m，不将经纬度度数当米。
2. 09:05 分别检查G01斜长带、G02 L形、G03重复点、G04共线、G05单位置原始记录。
3. 09:10 选择精确坐标去重或拒绝重复，锁定同面积方向规则与算法版本。
4. 09:15 选择需要计算的组，冻结完整来源、口径和组选择；未选组也保留在快照。
5. 09:20 提交Redis worker，计算Andrew凸包与逐凸包边方向的最小面积包围框。
6. 09:25 在同一x/y比例米制图中切换三种边界，核对原始/唯一/重复计数、面积、顶点和包含性。
7. 09:30 说明凸包填平凹口和退化几何，不把包络当覆盖，提交接受或待补充复核版本。
8. 09:40 负责人批准最新接受版本，CSV保存凸包顶点、轴框/定向框角点、单位、面积和来源计数。

## 快速启动

```sh
cp .env.example .env
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
# 启动自动seed；也可显式幂等复跑，不覆盖用户编辑
docker compose exec backend python -m scripts.seed_demo
```

前端 `http://localhost:18237`，API文档 `http://localhost:19237/docs`，MySQL `localhost:17737`。演示密码均为 `Envelope2026!`。

| 角色 | 演示账号 | 权限与动作 |
|---|---|---|
| analyst | analyst@lantu.demo | 导入米制测组、保存口径、冻结研究、运行、足迹复核 |
| admin | admin@lantu.demo | 全部整理功能，批准最新接受复核归档 |
| viewer | viewer@lantu.demo | 读取全部结果/审计，下载已批准CSV，无写入或批准权限 |

JWT角色由后端校验，审计记录写入与拒绝状态；全局错误与输入处理返回可恢复信息。演示凭据与JWT密钥只供本地模拟环境。

## 几何口径

`backend/src/services/hull.py::convex_hull(points, deduplicate=True)` 使用Andrew单调链。输入有限[x,y]对，精确数值坐标去重；False拒绝重复。排序并按叉积构造CCW凸包，共线内点不作为顶点，无重复闭合点。面积先平移到第一个顶点，再以shoelace计算，避免大绝对坐标乘积抵消；polygon周长为边长和，单位m。

`services/rectangle.py::minimum_rectangle(points, tie_relative=1e-12)` 枚举每条凸包边方向，逐方向投影全部h个凸包点，因此是**O(h²)方向枚举**，不是线性旋转卡尺。面对象方向规范为[0,90)，在 `tie_relative*max(1,最小候选面积)` 内视作同面积，按最小方向、角点字典序稳定选择。保存方向数、角点和全部原点包含性偏差/容差；不通过膨胀角点伪造覆盖。`axis_aligned(points)` 独立给出与坐标轴平行的框。

一个唯一位置返回point，恰好共线返回line；凸包和定向框面积0，顶点分别只有1/2个，不伪造polygon或四角。周长只有polygon有值，point/line为null；凸包线另报line_length，点长度0。line方向是[0,180)，不适用面对象同面积的[0,90)规则；point无方向，API的angle0仅作显示占位，页面明确“点无方向”。轴框对斜线仍可有正面积，因为它是另一种包络。

面积单位m²，长度m。图形x/y缩放相同；单位置视窗留白仅用于可视化，不是物理缓冲面。三种面积分别展示；分母0的比值返回null，不输出0%假占比。凸包填平凹口，不能解释为真实采集覆盖或地理边界。

API必须声明local_m，每组1至300条、最多8组，组ID唯一、组内点ID唯一，坐标有限且绝对值≤1e9；重复坐标不是重复点ID。没有自动投影、吸附、重采样或坐标修补。

## 实体、精度与技术

六实体 PointSurvey、BoundaryPolicy、EnvelopeStudy、EnvelopeRun、FootprintReview、Report，贯穿表/model/schema/service/route、前端API/store/page。研究快照冻结完整原始测组、去重口径、方向参数、算法版本与选组范围；运行和复核新增版本记录，报告绑定最新接受复核ID，后续复核不改旧CSV。

科学坐标、group_ids、快照和结果使用 **MySQL LONGTEXT保存JSON**，由 `backend/src/config/json_type.py::PreciseJSON` 调用Python json序列化/解析，保留Float64往返数字。没有将x/y/面积声称为不存在的独立原生Double列；真正的 `boundary_policies.area_tie_relative` 是DOUBLE列。原生MySQL JSON读回百万级小数时可能改动1ULP，因此最终版本明确使用文本JSON。显示8位坐标或2位面积不改变底层值；CSV JSON保留完整往返数字。

| 部分 | 技术 |
|---|---|
| 前端 | Vue3、TypeScript、Vite、真实比例SVG点组/边界 |
| API/算法 | Python3.11、FastAPI、SQLAlchemy、标准库几何算法/JWT |
| 后台 | Redis真实队列、独立worker及心跳健康检查 |
| 数据库 | MySQL8.4，科学数组LONGTEXT JSON、口径容差DOUBLE |
| Docker | 恰好frontend/backend/worker/db/redis，五服务均真实健康检查 |

运行不依赖Shapely；独立测试使用Shapely2.1.2作参考。`frontend/src`按api/stores/types/components/common/hooks/pages/router/utils/constants分工，六领域页加登录；比例图、口径条、面积摘要、点组表跨页共享。`backend/src`按models/schemas/services/controllers/routes/middlewares/config/utils/constants分工，seed在backend/scripts，初始schema说明在backend/migrations。测试、日志与截图在批根 `test-artifacts/gb-2408`，不混入源码。

`.env.example`：COMPOSE_PROJECT_NAME=survey-envelope，FRONTEND_PORT=18237，BACKEND_PORT=19237，DB_PORT=17737，SEED_DEMO=true，JWT_SECRET；数据库/Redis连接在compose注入。三个命名卷保存数据库、Redis、worker产物，Nginx代理/api并SPA回落，健康检查用127.0.0.1。前端依赖用匹配锁执行npm ci。开发时前端 `npm ci && npm run dev`，API `uvicorn src.main:app --host 0.0.0.0`，worker `python -m src.worker`，设置可连接的DATABASE_URL/REDIS_URL。

role、deduplication、coordinate_system、run_status、review_decision、geometry_type枚举位于 `backend/src/constants/enums.py` 和 `frontend/src/constants/enums.ts`，schema Literal与服务共同约束实际口径。

## 边界与清理

仅局部二维平面，不读取经纬度或执行投影；精确浮点去重不是测量误差聚合。没有凹包、真实覆盖估计或行政边界推断。有限精度与同面积容差公开；单worker无生产级租约，无生产迁移回滚或多租户隔离。原生JSON旧表迁移不自动执行，本演示使用已验收的全新LONGTEXT schema；生产迁移需单独设计。

```sh
docker compose down -v --remove-orphans
```

License: MIT。全部采集点与点组均为模拟数据。
