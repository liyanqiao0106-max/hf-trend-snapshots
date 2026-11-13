# GPU 与存储报价审计：2026-11-13

本轮属于现有 AI 看板改进。只读获取公开看板、原始报价与官网，修复采集/展示代码；本机 history/、site/data/、翻译缓存未覆盖。发布前的真实样本留在 work/tmp，不能把本地实现称为已经公开上线。

## 核验结论

| 范围 | 对照及结果 | 解释与修复 |
| --- | --- | --- |
| 既有 Azure 报价 | 156 条按 SKU、地区、计费方式与最新官方 Retail Prices API 匹配，156/156 同价 | 这次未发现数值错价。目录价不是成交记录；跨区域中位数持平也不证明全部地区报价都不变。补逐条同口径变化统计。 |
| GPU 覆盖 | 当前已验证 Azure 7 SKU、555 条、5 个型号标签；Lambda 官方表另有 9 条未来挂牌，必须排除 | Azure 新增 H200、H100 NVL、T4 等；NVL 保留原规格。实例总价除以确认卡数，显存取每卡容量，不取 VM RAM。Lambda 脚注写明价格 2026-11-16 00:00 UTC 生效，11/13 不得作为现价。此前含未来价的 564 行样本只供审计，不能进入当前看板。 |
| 存储原表提取 | 18 条 DRAM、模组、NAND、GDDR、SSD 与 DRAMeXchange 当前原表价格全部一致 | 已验证当前提取；不能外推为全部历史或真实成交已独立核验。 |
| 存储日期 | 18/18 原有 as_of 被设成采集日期；真实 DRAM 源日 11/12，部分模组/NAND/GDDR 为 11/2，SSD 为 10/30 | 修复分区源时间解析。as_of 为源报价日，observed_on 为采集日；未知源日留空。历史图仍按每日观察日，重复观察不声称发生新报价。 |
| 独立 SSD 渠道 | Samsung 美国官方 990 PRO 1TB（MZ-V9P1T0B/AM）挂牌 $319.99，缺货；TrendForce 10/30 街价均值 $259.92 | 单店挂牌、跨店平均和不同日期不可互换；新增独立 SSD official retail 类别，明示缺货，保留原街价均值。 |
| 缓存/回退 | 发现通用请求在网络异常时可静默返回旧缓存 | 价格来源改为严格请求；失败报源错误。存储原源失败时保留上次数据、标 stale，不增加今日历史点。304 是源成功确认未修改，仍可使用。 |

## 来源与边界

- Azure 官方价格接口说明：https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
- Azure 官方 Spot 说明：https://learn.microsoft.com/en-us/azure/virtual-machines/spot-vms
- Lambda 官方实例表：https://lambda.ai/instances （只读取经单卡标题确认的表；包含该实例 CPU/RAM/存储，非裸 GPU 或保证可租容量；必须检查价格生效日。本轮公布未来价格，因此 11/13 不能用这些数代表现价。）
- 存储原始表：https://www.dramexchange.com/
- 第二发布端：https://www.trendforce.com/price/dram/dram_spot 和 https://www.trendforce.com/price/flash/ssd_street 。这两个发布端与 DRAMeXchange 同属 TrendForce，不能算独立的市场调查。
- 独立厂商挂牌：https://www.samsung.com/us/memory-storage/nvme-ssd/990-pro-pcie-4-0-nvme-ssd-2tb-sku-mz-v9p1t0b-am/ 。通过结构化 Product 的 SKU 和 1TB 容量确认身份，不按 URL 中的 2tb 旧路径猜测。
- HBM rental proxy = 云 GPU 小时价 / 每卡显存，包含计算成本；不是 HBM 芯片现货价。BLS 是月度行业价格指数，不能当逐个 SSD 的实时交易价。
- 未取得覆盖全部 DRAM/NAND 型号的独立免费成交数据，因此不声明全市场实时报价已经核验。按原源正确展示、标注日期、区分市场口径，比人为制造波动更符合证据。

## 复现

在项目根目录运行 `.venv/bin/python -B scripts/audit_storage_prices.py --day 2026-11-13`。只在 work/tmp/storage-audit-2026-11-13/ 保存公开快照、原始 HTML、第二发布端、Samsung 独立挂牌与 audit.json，不改正式数据。

GPU 当前有效样本：work/tmp/gpu-catalog-2026-11-13-current.json；旧公开样本：work/tmp/gpu-pages-current.json。work/tmp/gpu-catalog-2026-11-13-multicloud.json 含已发现的未来价，仅作错误复核，不作为当前价。SkyPilot 的公开目录已评估，但本轮使用直接官方报价，没有把未经核实许可的上游源码或 CSV 并入采集。
