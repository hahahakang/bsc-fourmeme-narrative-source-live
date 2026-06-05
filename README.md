# BSC Four.meme 叙事源追踪与算法模型

中文 | [English](README.en.md)

这是从原始链上复盘拆出来的新项目。旧仓库 `hahahakang/bsc-fourmeme-analysis` 保留原文章和链上复盘；本仓库专门承接后续工作：追踪 token 最早的叙事来源、消息源强相关性、买入后的发酵窗口，以及 BSC 打狗机器人可复用的信号规则。

公开网站：

https://hahahakang.github.io/bsc-fourmeme-narrative-source-analysis/

## 中文优先，英文可切换

网站首页默认展示中文版本，并提供 `English` 切换按钮。中文版本面向实际研究和复盘阅读；英文版本用于公开协作、外部分享和后续数据说明。

## 这个项目回答什么

- 他买的代币最早的故事从哪里来：人物、公司、项目、官方功能、媒体 IP、中文社区热梗，还是泛名人名 token。
- 哪些消息源和项目强相关：创始人原帖、官方公告、产品发布、公司负责人动态、供应链人物背书等。
- 买入之后故事发酵需要多久：用买入后持有/退出窗口统计胜率、收益和 FDV 桶表现。
- 后续机器人应该沉淀什么：源头强度、时间优势、leader/copycat、FDV/流动性、风险惩罚。
- 为什么不能直接全自动买：当前阶段先做信息雷达和人工确认，避免把单案例包装成确定性。

## 当前新增内容

- 第一批叙事源时间线：把主要 token 连接到候选源头事件、证据等级、买入相对源头窗口、关系强度和机器人含义。
- 源头库：人物、公司、项目、官方账号、媒体 IP、中文短视频 meme，以及黄仁勋/Marvell 这类链外同构案例。
- 叙事候选池：token 名称、描述、叙事标签、源头类型猜测、证据状态和研究优先级。
- 发酵窗口统计：持有/退出窗口、胜率、已实现收益、FDV、流动性。
- FDV 桶 x 持有窗口矩阵：统计哪个买入节点和等待窗口历史上更有效。
- 信号模型草稿：source quality、time advantage、onchain quality、liquidity execution、risk penalty。

## 数据文件

- `data/source_timeline_research.csv`
- `data/source_library.csv`
- `data/narrative_candidates.csv`
- `data/fermentation_window_summary.csv`
- `data/bucket_window_summary.csv`
- `data/source_signal_model.csv`
- `data/token_trade_summary_with_windows.csv`
- `data/buy_detail_with_fdv.csv`
- `data/fdv_bucket_summary.csv`
- `data/top_winners.csv`
- `data/top_losers.csv`

## 口径说明

链上交易重建和窗口统计来自本地解码后的数据。叙事源等级是证据等级，不是买入评级：A 表示原始/官方源，B 表示带原帖上下文的强二手源，C 表示 token/项目页归因，D 表示后验社区解释，E 表示暂未匹配源头。本项目仅用于研究，不构成投资建议。
