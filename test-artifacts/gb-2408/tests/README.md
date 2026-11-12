# gb-2408 运行合并/重试/恢复测试

无第三方依赖（环境内无 Docker/pip/MySQL/Redis），用标准库运行：

```sh
python3 -I test_runs_merge.py
```

`fakes.py` 提供仅覆盖应用所用接口的 SQLAlchemy/redis/FastAPI 内存替身；被测对象是
`backend/src/services/runs.py` 与 `backend/src/worker.py` 的真实代码。

覆盖点（18 个用例）：

- 同一研究并发提交合并为单条运行、Redis 仅一条队列消息
- completed 运行重复提交原样返回，不重算不覆盖
- failed 运行拒绝普通提交（409），引导重试接口
- 唯一约束冲突的并发兜底（IntegrityError 后回滚并返回已有运行）
- 重试保留失败原因至成功、attempts 递增、completed 拒绝重试
- worker 重复投递不覆盖 completed 结果；带复核/归档的成功运行保持不变
- 计算失败记录原因，重试后成功并清错；中断恢复仅重新入队未完成运行
- 选组/口径不同的研究各自独立产生运行
- 队列不可用时运行置 failed 并保留可重试原因
