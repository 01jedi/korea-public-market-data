# 韩国现货公开行情采集

直接读取 Upbit、Bithumb 官方公开 API；另外独立尝试 Binance 官方 API。没有交易所账户、个人 API Key、代理或聚合数据。

## 已完成的云端验收

[第一次运行](https://github.com/01jedi/korea-public-market-data/actions/runs/45988446355)已成功执行。CT（Concrete）、BIGTIME（Big Time）两所KRW市场的72小时1m/5m均完整分页采集两次并逐条相同，trades和orderbook实际读取通过。空缺时槽保留。

该GitHub运行地区对Binance返回451，Binance数据为N/A；没有绕过地区限制。云端通过仅指韩所公开采集，不指Binance或原监控任务通过。

## 人工刷新

Actions → Manual Korean public market acceptance → Run workflow；或通过已授权的GitHub连接，显式更新 `.github/manual-request.json` 的request_id。只有人工运行请求或该文件的提交触发采集。没有schedule，不会定时刷新，不依赖Mac开机。

## 公开读取

- [验收JSON](https://raw.githubusercontent.com/01jedi/korea-public-market-data/main/data/acceptance.json)
- [全部数据文件](https://github.com/01jedi/korea-public-market-data/tree/main/data)
- [原始证据ZIP](https://github.com/01jedi/korea-public-market-data/blob/main/data/public-evidence.zip)

`data/<upbit或bithumb>_<CT或BIGTIME>_<1或5>m.normalized.json` 提供全部已采K线、KRW成交额、UTC时间及原始字段。文件名区分交易所、币种和周期。ZIP保留两次采集的请求URL、HTTP状态、响应头、原始JSON及获取时间。

读取时核对run_id和end_exclusive_utc；公开地址可能有CDN缓存，需要准确复现时使用具体提交SHA的网址。每次运行是历史快照，不是持续实时服务。USDT不等于USD；本路径不提供已验收的美元换算或因果归因。

当前对话的云端网页工具已实际读取验收JSON及1m/5m文件。原普通ChatGPT对话已实际测试：网页路径9次Cache miss，但GitHub连接的fetch_file及fetch_blob已成功读取验收和两份真实行情，抽样与云端原始文件一致，普通对话GitHub读取通过。详见[消费端验收回执](data/consumer-acceptance.json)。原自动监控任务尚未验收，不声称已接入。本项目未修改原V1.1任务、名单、模块、阈值或频率。
