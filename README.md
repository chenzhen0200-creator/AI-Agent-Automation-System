# AdLearn

## 网页界面

访问 `/` 可打开无需构建步骤的原生 HTML/CSS/JavaScript 页面，资源由 `/static` 提供。Chat 在当前页面保存对话，调用 `POST /chat` 并将回答、平台、意图、执行模式、来源、警告和执行轨迹分层展示；刷新页面后对话清空。Automation 卡片调用 `POST /automation/run`，已禁用的 `ads_information_collection` 不可选择。Learning Progress 从只读 `GET /learning-progress` 获取；System Status 从 `GET /api/status` 读取服务、LLM、Vision 和搜索的布尔状态，不返回密钥。截图按钮标记 Coming Soon，不会伪造上传成功。

前端对超时、HTTP 422/429/500 和工作流错误分别显示提示。Render 实例首次启动较慢时会提示稍候。原有 `/chat`、`/health`、`/docs`、自动化与截图预留 API 仍可直接使用。

AdLearn 是用于 Google Ads 和 Meta Ads 学习与自动化的 AI Agent。它提供概念解释、图文式操作步骤、案例分析、跨平台对比和学习进度。Agent 优先尝试 LLM Tool Calling；模型不可用时保留原有规则路由。所有输出都是 Python dict，命令行入口将其转换为 JSON。

## Chat History 与 PostgreSQL

网页首次打开会在浏览器 `localStorage` 生成匿名 `adlearn_client_id`（UUID）。这个 ID 只是浏览器级标识，不是真正安全的用户账户或登录。历史 API 使用该 ID 限定会话；知道别人的 ID 仍可能冒用，因此不要用此原型保存敏感账户信息。真正的账号隔离需要后续登录和服务端认证。

设置 Render 环境变量 `DATABASE_URL` 为同 Region PostgreSQL 的 Internal Database URL。不要把连接串提交到 Git 或写入日志。服务会以 `CREATE TABLE IF NOT EXISTS` 初始化 `conversations` 和 `messages` 两表；`messages.conversation_id` 外键级联删除。所有 SQL 使用参数，不拼接用户输入。`GET /conversations`、`POST /conversations`、`GET /conversations/{conversation_id}/messages`、`DELETE /conversations/{conversation_id}` 提供会话读写，查询均校验 `client_id`。`POST /chat` 可带 `client_id` 和 `conversation_id`，自动创建会话并保存用户问题及回答，返回 `conversation_id`。网页刷新后会从 PostgreSQL 恢复会话；`localStorage` 只保留 ID。

未配置 `DATABASE_URL` 时 `/chat` 仍正常教学，历史接口提示 `Database Not Configured`；写入失败时回答仍返回，并附 `Chat History Save Failed` 警告。`/api/status` 仅返回 `database_configured` 和 `database_connected` 布尔值。PostgreSQL Chat History 保存完整对话；原有 Learning Memory 继续记录学过的主题，两者用途不同。Render Web Service 已通过环境变量连接 PostgreSQL；Free 数据库有到期日，若需长期保存请在 Render 升级或迁移，并定期备份。

本项目不连接真实广告账户，不创建或修改广告，不执行充值、付款或预算调整。当前默认不启用真实 AI 模型，也没有数据库或视觉模型。

## 运行示例

在有 Python 3 的环境中，从项目目录运行：

    python main.py "Google Ads CTR 是什么"
    python main.py "Meta Pixel 怎么设置"
    python main.py "Google Ads CTR高但转化低为什么"
    python main.py "Google Ads 和 Meta Ads 归因区别"
    python main.py "学到哪里了"
    python main.py "我之前学过 CTR 吗？"
    python main.py "Meta Pixel 学过没有？"
    python main.py "我上次学的是什么？"
    python main.py "Google Ads 现在 Demand Gen 受众规则是什么？"
    python main.py "Google Ads 在哪里添加广告组？" --image-path "C:\path\to\screenshot.png"

不带参数时会提示输入学习目标。当前 Codex 环境没有可用 Python，以上仅为使用说明。

## LLM Tool Calling 与规则回退

Render 诊断：日志同时写入 `logs/app.log` 和标准输出，因此可在 Render Logs 查找 `LLM request started`、`LLM request succeeded`、`LLM request failed` 与 `LLM unavailable, using rule fallback`。日志只记录模型名、开关状态、是否配置密钥、HTTP 状态码和经过筛选的错误代码；不会记录密钥、用户问题或服务端原始错误正文。`MODEL_NAME` 默认是空字符串；若要启用真实 LLM，需要在 Render 环境变量中明确设置可用模型名、`LLM_ENABLED=true` 和 `OPENAI_API_KEY`。当前客户端用 Python 标准库直接请求 Responses API，未使用 OpenAI Python SDK，因此 `requirements.txt` 不需要 `openai` 包。

`llm/tool_schema.py` 根据 Tool Registry 中的十一个条目生成 Function Calling Schema。每个 Schema 包含 name、description、parameters；参数用 JSON Schema 指明必需字段与类型。Memory 搜索工具接收可为 `null` 的 `platform` 和 `topic`；模型必须用它查询用户的学习历史，不能凭模型记忆猜测。`prompts/system_prompt.py` 继续禁止真实账户操作。

`llm/model_client.py` 使用 Python 标准库调用 OpenAI Responses API。模型可返回一个 `tool_call`（工具名和参数），或 `direct_answer`。工具调用先经过 `llm/tool_validation.py`、风险分级和权限检查，再由 Tool Registry 执行。模型只选择本次的首个能力；Agent 可按固定的安全组合追加辅助 Tool，最多执行 3 次 Tool 调用。没有第二轮模型总结。

默认配置为 `LLM_ENABLED=false`，`MODEL_NAME` 为空。若未启用、未设置模型名或环境变量中没有密钥，客户端返回 `LLM Not Configured`，不会模拟模型结果；Agent 随后使用原有 platform routing + intent routing。网络或模型请求不可用时也回退。模型给出无效工具调用时返回 `Invalid Tool Call`，不会借回退执行该调用。

要在未来有 Python 和真实 API Key 的环境中启用，分别设置环境变量 `LLM_ENABLED=true`、`MODEL_NAME` 和由 `API_KEY_ENV_NAME` 指定的密钥变量（默认 `OPENAI_API_KEY`）。不要把密钥写入代码或日志。`config.py` 只保存环境变量名与开关。此处没有进行真实模型调用。

`execution_mode` 表示结果来自 `llm_tool_calling`、`rule_fallback` 或截图专用的 `vision_tool`；真实账户操作在执行前被拒绝时为 `not_executed`。文字流程的日志记录问题、模型可用性与工具结果；截图流程只记录是否收到截图、识别平台和页面、UI 元素数量、置信度及是否调用 Steps Tool，不写入图片路径、原始内容或截图问题文本。

工具调用格式参考 [OpenAI Docs 的 Function Calling 说明](https://developers.openai.com/api/docs/guides/function-calling)。

## 十一个 Tool

| Tool | 平台 | 意图 | 作用 |
| --- | --- | --- | --- |
| explain_google_ads_concept | google_ads | concept | 解释 23 个 Google 指标、广告类型与出价概念 |
| get_google_ads_steps | google_ads | steps | 返回 15 个主题的图文式界面步骤 |
| analyze_google_ads_case | google_ads | analysis | 返回 12 类案例的原因、检查和建议 |
| explain_meta_ads_concept | meta_ads | concept | 解释 20 个 Meta 结构、追踪、受众与指标概念 |
| get_meta_ads_steps | meta_ads | steps | 返回 13 个主题的图文式界面步骤 |
| analyze_meta_ads_case | meta_ads | analysis | 返回 14 类案例的原因、检查和建议 |
| compare_google_meta | cross_platform | comparison | 返回 8 组广告、追踪、受众、出价、归因和结构对比 |
| get_learning_progress | cross_platform | progress | 返回两个平台的学习摘要 |
| search_learning_memory | cross_platform | memory | 搜索是否学过某主题，或读取最近学习记录 |
| search_ads_knowledge | google_ads / meta_ads | retrieval | 搜索外部资料，返回来源、更新时间及相关正文 |
| analyze_ads_screenshot | google_ads / meta_ads | screenshot | 只读识别截图页面和控件，并结合图文步骤提出学习建议 |

Concept Tool 为具体主题返回 name、chinese_name、explanation、formula、why_it_matters、example 和 common_mistakes；非公式概念的 formula 为 null。Analysis Tool 返回 issue、possible_causes、checks、recommended_actions、priority、notes。Comparison Tool 分别给出两平台的 how_it_works、strengths、limitations，并给出 key_difference 和 when_to_use_each。未指定具体主题时，这些工具返回可选目录，而不猜测主题。

案例和步骤均为教学内容，不代表已经读取真实广告数据。具体广告界面与产品名称可能变化；Google Ads 的竞价策略名称也可能调整，应以当前官方界面为准。

## 图文步骤与截图接口

两个 Steps Tool 保留 visual_step_by_step 模式。每一步包含 step_number、title、description、ui_location、action、expected_result、next_page、image_hint。步骤主题现提供完整的只读操作路径，Answer Composer 展示全部步骤及每一步的位置、操作、说明、预期结果和图示提示，不再截取前 6 步。现在只有图文式步骤说明，没有真实截图。直接给旧 Steps Tool 传 screenshot 参数时返回 Vision Not Configured；Agent 收到截图路径后则优先进入 Screenshot Tool。没有真实视觉服务时不会伪称已经识别图片。

## Screenshot / Vision 分析

**Vision** 指从用户提供的图片中识别可见信息。**Screenshot Analysis** 专注于广告后台截图：先确认 Google Ads 或 Meta Ads、当前页面和层级，再整理导航、按钮、字段、选中项、提示、审核状态与可能的下一步。支持的页面名称和层级预留在 `vision/screenshot_analyzer.py`，覆盖 Google Ads 的 Campaigns、Ad groups、Ads、Keywords、Search terms、Audiences、Locations、Budget、Bidding、Conversions、Video campaign、Performance Max、Demand Gen，以及 Meta Ads 的 Campaign、Ad Set、Ad、Audience、Placements、Budget、Optimization、Pixel、Events Manager、Attribution、Creative、Delivery / Review status。

`vision/vision_client.py` 是通用视觉服务接口，只负责把图片和提示交给未来的真实适配器并返回结构化观察；这里没有广告业务判断。当前没有绑定任何视觉适配器，单靠设置 `VISION_ENABLED` 和 `VISION_MODEL_NAME` 也不会虚构识别结果。`vision/screenshot_analyzer.py` 解释视觉观察，校验平台、页面、完整度及最低置信度 0.70。`vision/ui_element_parser.py` 把控件统一成 `element_type`、`text`、`location`、`state`、`confidence`，丢弃格式错误的元素，不补造截图中不存在的按钮。

上传截图时，Agent 绕过普通文字路由，优先执行 `analyze_ads_screenshot`。如果页面识别可靠且用户要找位置或下一步，Agent 再调用对应的 Google / Meta Steps Tool，并合并结果得到 `standard_steps`。只有截图中确实可见且置信度足够的控件才会形成 `recommended_step` 和 `screenshot_guidance`；否则明确要求更完整的截图。审核状态和警告问题只解释视觉结果中实际识别出的文字，不猜测原因。当前不自动串联外部检索；界面疑似更新时会返回 `retrieval_suggestion`，提示可用 `search_ads_knowledge` 核对官方说明。

`Vision Not Configured` 表示没有真实视觉服务；`Low Vision Confidence` 表示页面、平台或控件不能可靠识别；`Incomplete Screenshot` 表示导航栏或关键区域缺失。低置信度时不强行指出按钮，因为错误位置可能误导学习。Agent 中的截图路径先执行 Screenshot Tool，再受控执行 Steps Tool；直接单独调用 Screenshot Tool 时保留原有内部联动。普通 Steps Tool 只提供通用图文步骤，不读取当前后台界面。两者都不点击、不创建、不修改、不删除广告，也不调整预算、充值或付款。截图结果本身不写入 Learning Memory。

命令行示例中的 `--image-path` 仅传入本地路径；目前没有真实视觉适配器，因此不会返回截图识别结果。若问题明确指定平台且适合图文步骤，Agent 会回退到通用 Steps Tool，并标记 `screenshot_unverified=true`；其他问题返回 `Vision Not Configured`。未来接入服务时，可通过 Agent 的 `vision_adapter` 接口传入真实适配器，并继续只返回必要的结构化观察。日志只保存截图流程的状态和计数，不保存图片原始内容、路径或账户信息。

## Guardrail、错误处理与恢复

`guardrails/action_policy.py` 保存 11 个只读学习 Tool 的白名单和真实账户操作的黑名单。`risk_classifier.py` 将概念与进度查询归为 low，截图分析、案例分析与操作教学归为 medium；代为创建广告、修改预算或出价、删除广告、付款、充值和权限修改归为 high。`permission_guard.py` 在 Tool 执行前检查风险、注册状态和白名单。Tool Registry 也会再次检查，因此模型误选或直接调用 Registry 都不能绕过权限检查。高风险动作直接返回 `High Risk Action Blocked`，不会走 fallback。

所有公开失败结果都包含 `success=false`、`error_type`、`message`、`recoverable` 和 `suggested_action`，由 `errors.py` 统一生成或补齐。常见分类包括 Validation Error、Tool Not Found、Invalid Tool Call、LLM Not Configured、LLM Request Failed、Search API Not Configured、No Search Results、Content Extraction Failed、Vision Not Configured、Low Vision Confidence、Incomplete Screenshot、Memory Read Failed、Memory Write Failed、Permission Denied、High Risk Action Blocked 和 Unsupported Learning Goal。无法安全恢复时返回明确错误，不编造模型、搜索或视觉结果。

`recovery/retry_policy.py` 最多重试 3 次，仅对明确的网络超时、429 或临时服务端故障使用指数退避，可选少量 jitter。权限拒绝、校验失败、未注册 Tool 和高风险动作不会重试。当前没有运行 Python，因此没有实际等待或发送重试请求。

Fallback 与 Retry 不同：Retry 对**同一临时失败请求**再次尝试；Fallback 改用**其他已授权能力**。LLM 不可用时进入规则路由；外部搜索失败时可提供稳定的 Concept、Analysis 或 Comparison 内容，但标记 `freshness_unverified=true`，不声称这是最新规则；Vision 不可用时可提供通用 Steps，但标记 `screenshot_unverified=true`，不声称已识别当前页面。若安全的回退工具也失败，返回原始错误。Memory 写入失败时保留已生成的教学内容，返回 `memory_saved=false` 与警告，避免把学习内容一并丢弃。

Agent 结果新增 `execution_trace`，按顺序列出 risk_classifier、llm_tool_calling、validation、permission_guard、tool_execution、rule_fallback、stable_tool_fallback、steps_fallback 等实际经过的阶段。`execution_mode`、`fallback_used`、`risk_level` 和 `retry_count` 帮助判断结果是如何产生的。日志只记录 error_type、tool_name、recoverable、retry_count、fallback_used、risk_level、blocked_action 等元数据；截图流程不记录路径和原图，工具执行不记录敏感账户内容或 API Key。

## 两层路由

1. platform routing：ads_learning_agent.py 先识别 google_ads、meta_ads、cross_platform 或 unknown。
2. intent routing：再识别 concept、steps、analysis、comparison、progress、memory 或 retrieval。“学过吗／上次学了什么／最近学了什么”优先进入 memory；“现在／最新／官方／目前／2026”优先进入 retrieval；一般界面位置和按钮问题进入 steps。
3. 规则回退时，Agent 用 platform + intent 选出工具名；LLM 路径则由模型根据 Tool Schema 选择。两条路径最终都由 tool_registry.py 按 name 找到 handler 并执行。所有注册条目都有 name、platform、intent、description、handler。

    user_message → 截图优先 / LLM Tool Calling → Rule Fallback（LLM 不可用时）
                 → Tool Validation → Risk Classification → Permission Guard
                 → Tool Registry → 必要的辅助 Tool → Answer Composer → Learning Memory
                 → main.py 输出 JSON

规则回退仍可能误解同义表达或混合问题。Agent 成功结果统一包含 `success`、`execution_mode`、`platform`、`intent`、`answer`、`tool_results`、`memory_saved`、`sources`、`warnings` 和 `execution_trace`。失败时补充 `error_type`、`recoverable` 和 `suggested_action`。`tool_results` 按执行顺序保存每个 Tool 的结构化结果；有检索来源时，`sources` 保留标题、链接、来源类别和更新时间。

## 统一执行链与 Answer Composer

`agents/ads_learning_agent.py` 用一个执行上下文追踪用户问题、平台、意图、截图路径、当前 Tool、工具结果、Memory / Retrieval / Vision 上下文和已执行次数。每次 Agent 发起 Tool 调用前都校验参数、评估风险并检查权限；`MAX_TOOL_STEPS = 3` 包含失败的工具调用，达到上限就返回 `Max Tool Steps Exceeded`。高风险请求与无效模型 Tool Call 直接失败，不通过回退绕过。

`agents/answer_composer.py` 从**实际成功的工具结果**整理面向用户的 `answer`。它把步骤、概念、案例、进度、截图指导和检索内容组织成可读文字；检索答案会附来源链接，部分失败会附警告。它不调用模型，也不补造网页、截图识别或广告账户数据。

当前仅允许这些有限协作：

| 学习场景 | 执行方式 |
| --- | --- |
| 上传截图并问下一步 | Screenshot → 对应平台 Steps；Vision 不可用时，只在平台明确时给通用 Steps 并标注截图未核实 |
| 询问现在最新的设置步骤 | External Search → 对应平台 Steps；搜索失败时仍可给通用步骤，但标注时效未核实 |
| 询问以前是否学过 | Memory Search |
| 询问学到哪里 | Learning Progress |
| 询问投放异常且要求最新官方说明 | 对应平台 Analysis + External Search；搜索失败时保留案例教学并标注时效未核实 |

单独的外部检索失败可回退到稳定知识 Tool；截图失败可回退到通用步骤。工具组合中如果一项失败且另一项成功，`tool_results` 同时保留成功与失败，并在 `warnings` 说明限制。`memory_saved=true` 表示本次明确学习主题已写入长期 Memory；`false` 表示尝试保存但失败；`null` 表示本次无需写入。`step_count`、`freshness_unverified` 和 `screenshot_unverified` 让结果更容易检查。

## Learning Memory 与进度

**Short-term Memory** 位于 `memory/memory_manager.py` 的当前进程内字典，保存当前平台、主题、意图、最近 Tool 和当前步骤。它帮助同一进程内的后续调用读取临时上下文；命令行每运行一次通常会启动新进程，所以它不会跨运行保留。

**Long-term Learning Memory** 存在 `data/learning_memory.json`，按 Google Ads、Meta Ads 和跨平台比较分类。`memory_manager.py` 统一实现 Memory Read、Write、Update、Search，以及显式的删除接口；删除接口未注册为 Agent Tool。`learning_memory.py` 提供 `record_learning`、学习历史、单主题、最近记录和统计的领域接口。

六个概念、步骤、案例 Tool 成功返回具体主题后会自动调用 `record_learning`。跨平台对比记在 `cross_platform/comparison`，不算作任一单平台主题。失败结果、主题目录、进度查询和 Memory 搜索都不写入长期记忆。若写入失败，教学内容仍返回，并附带 `memory_saved=false` 和结构化警告。同一平台和类别下的同一主题是同一个 JSON 对象：再次学习只增加 `learn_count`、更新 `last_learned_at`，并保留 `first_learned_at`。`recent_learning` 保存最近 50 次学习事件，包括重复学习。

`get_learning_progress` 现在从 Learning Memory 动态统计两平台已学概念、步骤、案例和总主题数，并返回最近主题、学习阶段与下一步建议。`data/learning_progress.json` 和旧的 `logs/learning_progress.json` 保留为旧版课程进度数据，本版不再把它们作为学习历史来源。主题被展示即记为已学习，不代表已掌握；当前 JSON 方案不处理多进程并发写入。

`search_learning_memory` 是第九个只读 Tool：给出平台和主题时搜索既有记录；主题为 `null` 时读取最近学习。规则路由能处理“我之前学过 CTR 吗”“Meta Pixel 学过没有”“我上次学的是什么”等问题。`logs/app.log` 记录 Memory Read、Write、Update、Search，不记录 API Key。

## External Retrieval：第十个 Tool

`search_ads_knowledge` 用于核实会变化的平台规则、后台界面、广告类型、出价、归因以及 Pixel / CAPI 等内容。普通的“CTR 是什么”仍进入 Concept Tool；“CTR 高但转化低”仍进入 Analysis Tool；“Google Ads 现在 Demand Gen 受众规则是什么”进入外部检索。模型可用时，Tool Schema 会提供 `platform`、`query`、`official_only` 和 `freshness_required` 四个参数；模型不可用时，规则路由也能调用同一工具。

`retrieval/web_search_client.py` 使用可选的 Brave Web Search API。搜索密钥从 `SEARCH_API_KEY_ENV_NAME` 指向的环境变量读取，默认变量名为 `BRAVE_SEARCH_API_KEY`。没有密钥就返回 `Search API Not Configured`，不发送请求，也不生成假搜索结果。使用 `freshness_required=true` 时，搜索接口限定近一年结果；这有助于发现近期变化，但不能保证每篇文章都准确或最新。页面若没有可验证的更新时间，`updated_at` 为 `null`。

`source_filter.py` 只接受可识别的 HTTPS 来源：Google Ads 优先选择 Google Ads 帮助中心、Google Ads、Google 开发者文档及官方广告博客；Meta Ads 优先选择 Meta Business 帮助页、Meta 开发者文档及官方页面。默认 `official_only=true`。仅显式设置为 `false` 且官方页面无法提供内容时，才考虑经过清单筛选的第三方来源，并标记 `source_type="third_party"`。未知站点、广告农场、转载聚合站以及与广告主题无关的第三方页面会被拒绝。这个清单和规则只能做初步筛选，不能代替人工核验。

`source_ranker.py` 使用来源类别、问题相关度、标题匹配、页面更新时间与平台匹配进行规则评分；官方来源排在第三方之前。`content_extractor.py` 只提取所选网页的标题、相关正文段落和可获取的更新时间，限制抓取与输出长度。结果中的 `sources` 保留 `title`、`url`、`source_type`、`updated_at`、`relevance` 和评分；`retrieved_content` 通过 `source_url` 关联原网页。使用这些内容回答时应明确给出来源链接，不能把无法核实的片段说成官方结论。

结构化失败类型包括 `Search API Not Configured`、`No Search Results`、`Official Source Not Found`、`Source Rejected`、`Content Extraction Failed`，以及搜索接口自身失败时的 `Search Request Failed`。由于当前环境没有可用 Python，本次没有执行真实网络检索，也没有验证搜索密钥；上述结果只是代码约定，不代表已取得网页内容。

External Retrieval 从互联网按需查资料，处理知识的**出处与时效**；Learning Memory 在本地 JSON 保存用户**学过什么**。单纯检索不写入 Memory。当前搜索结果由 Tool 返回给用户，尚不自动记为已学习。RAG 通常会先建立维护过的知识库与索引，再检索片段供模型生成答案；本版没有本地知识库、向量索引或生成式检索链。未来可将外部检索与 RAG、Vision 结合，但必须继续保留来源和时间信息。

## 后续升级

真实 LLM 可用后，模型理解与 Tool Calling 会优先于关键词规则；规则仍用于模型不可用时的回退。Tool Registry 继续限制可调用能力。Memory 已用本地 JSON 实现，截图分析的路由和结构化接口已就绪；未来仍需接入真实视觉适配器。RAG 知识库当前尚未实现。

## Chat Mode

`POST /chat` 仍由用户主动提问，路径为 `User → /chat → Agent → Tool → Answer`。原有 11 个 Tool、LLM 与规则回退均保留。

## Automation Mode

`POST /automation/run` 用于手动运行已注册工作流，例如 `{"workflow_name":"scheduled_ads_learning","inputs":{}}`。路径为 `Trigger → Workflow Runner → Workflow → Tool → Result`。`manual` 是当前可直接测试的触发方式；`schedule` 预留给 Render Cron 或外部定时器，`webhook` 预留给外部事件。两者都通过 `POST /automation/webhook/{workflow_name}` 进入，并要求请求头 `X-Automation-Token` 与服务端 `AUTOMATION_WEBHOOK_TOKEN` 相符；定时器还可传 `X-Automation-Trigger: schedule`。令牌未配置时入口拒绝执行，不在代码或日志中记录令牌。

`automation/workflow_registry.py` 登记名称、描述、可用触发类型、handler、风险等级和启用状态；`workflow_runner.py` 建立独立 Context，校验 Tool、检查风险与权限、限制 `MAX_WORKFLOW_STEPS=10`，使用现有 Retry Policy，并返回 `steps_executed`、`results`、`warnings`、`execution_trace`。日志记录工作流名、触发方式、起止时间、步骤数、重试次数、回退情况和最终状态，不记录输入内容或密钥。

`scheduled_ads_learning` 当前会用 `search_ads_knowledge` 检索 Google Ads 官方近期内容并整理来源摘要；可在 `inputs` 中传 `platform`（`google_ads` 或 `meta_ads`）和 `query`。没有真实搜索 API 密钥时，会明确记录检索失败，再回退到稳定概念 Tool，返回 `freshness_unverified=true`、空来源和警告，**不会伪造最新资料**。`ads_information_collection` 已登记但保持禁用：后续可按 URL 输入、抓取、字段提取、清洗、去重、写表、返回结果的顺序扩展；本版不抓取网页，也不写表。

Automation Mode 只允许现有已注册的只读 Tool。真实广告创建、预算或出价修改、付款、删除和账户权限操作继续由 Guardrail 拦截。网络超时、429 与临时服务端错误可按现有重试规则处理；校验或权限错误不重试。当前没有安装定时任务、没有数据库，也没有连接广告账户。

## Deployment：FastAPI 与 Render

本项目保留 `main.py` 作为命令行入口；`api/app.py` 是云端 Web 入口，`api/schemas.py` 定义请求和响应结构。当前 Windows 环境**不需要安装 Python**；Render 在云端 Build 阶段安装 Python 依赖。服务的实际状态需在 Render 核实。

| 接口 | 作用 |
| --- | --- |
| `GET /` | 返回 Agent 网页界面 |
| `GET /api/status` | 返回服务与外部能力的布尔状态，不返回密钥 |
| `GET /health` | 只检查 Web 服务能否响应，不调用 LLM、搜索、Vision 或广告账户 |
| `GET /learning-progress` | 通过只读 Tool 返回学习进度 |
| `POST /chat` | 接收 `{"message":"Google Ads CTR 是什么？"}`，调用现有 Agent 并返回其结构化结果 |
| `POST /analyze-screenshot` | 截图上传预留接口，目前返回 `Screenshot Upload Not Implemented` |

`ChatRequest` 暂时保留可选 `image_path` 字段作为旧接口兼容信息。**云端 `/chat` 收到该字段会明确拒绝**：用户电脑的本地路径并不是云服务器上的文件，也不应该让公开 API 读取服务器任意路径。未来需要专门的文件上传接口与真实视觉适配器，当前不会模拟截图识别成功。

Render 设置示例：

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn api.app:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

`render.yaml` 保存相同的 Web Service 基础配置，不包含密钥，也不会自行触发部署。Render Dashboard 的 Environment 页面用于设置 `LLM_ENABLED`、`MODEL_NAME`、`OPENAI_API_KEY`、`BRAVE_SEARCH_API_KEY`、`VISION_ENABLED` 等变量；缺少密钥时仍走现有安全回退，不会伪造模型或搜索结果。[Render 的 FastAPI 部署文档](https://render.com/docs/deploy-fastapi)也采用 `pip install -r requirements.txt` 和绑定 `$PORT` 的 Uvicorn 启动方式；[环境变量说明](https://render.com/docs/configure-environment-variables)建议用环境变量保存密钥。`.env.example` 只展示变量名和空密钥字段；`.gitignore` 忽略 `.env`、Python 缓存、运行日志和个人学习记忆文件。真实 API Key 不进入 Git 或日志。

`CORS_ALLOW_ORIGINS` 是可选的、逗号分隔的前端来源列表，默认留空；部署前需填明确的 `https://...` 域名，代码不接受 `*` 通配符。FastAPI 的[请求体模型](https://fastapi.tiangolo.com/tutorial/body/)校验 `/chat` 输入；格式错误和未处理异常只向客户端返回安全错误，服务器日志记录异常类型与调用栈，不回传完整 traceback。CORS 的来源限制参考 [FastAPI 官方说明](https://fastapi.tiangolo.com/tutorial/cors/)。

`data/learning_memory.json` 适合当前学习与原型阶段。云端实例重启、重新部署或横向扩容后，本地文件可能丢失或在各实例间不一致；它不应被视为可靠的长期数据库。当前继续使用 JSON 架构，未来可迁移到 PostgreSQL 或其他托管数据库。被 Git 忽略的个人学习记忆文件在云端首次使用时会从空结构开始。

## 参考资料

- Google Ads 术语表：https://support.google.com/google-ads/answer/12851704
- Google Ads 出价策略：https://support.google.com/google-ads/answer/10969287
- Google Ads 出价名称更新说明：https://support.google.com/google-ads/answer/6167148
