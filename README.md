# 韩国现货公开行情采集

仅直接读取 Upbit、Bithumb 和 Binance 官方公开 API，无交易所账户或个人 API Key。

## 手动刷新

Actions → Manual Korean public market acceptance → Run workflow。仅人工触发，无定时运行。标准 GitHub 托管 Ubuntu 服务器执行，不依赖个人电脑开机。

每次抓取最近完整72小时的 CT（Concrete）、BIGTIME（Big Time）KRW现货1m/5m，并重复抓取同一窗口；保留空缺时槽和原始请求证据。另外尝试 Binance USDT永续及BIGTIME正式现货。

## 读取结果

生成后从 [验收结果](data/acceptance.json) 检查实际运行编号、时间范围和各数据集状态。`data/*.normalized.json` 是规范化行情；`data/public-evidence.zip` 包含两遍采集的原始响应和元数据。

数据是该次人工运行的历史快照，不是持续实时行情。失败会保留为缺失，不切换代理。USDT不等于USD；本采集器不提供已验收的美元换算或因果归因。

云端运行成功、公开网址可读、普通ChatGPT对话可读、原自动任务实际调用是独立验收项。未实测前不声称已接入普通对话或原任务。

本项目不修改原V1.1监控名单、模块、阈值、频率或任务。
