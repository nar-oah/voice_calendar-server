# Voice Calendar Gemini Server

语音日历工具后端服务。项目围绕“用语音完成日历管理”这个题目实现，前端负责中文语音输入、确认与日历展示，后端负责把自然语言解析为结构化日程、持久化、模糊匹配删除/查看目标，并同步到 CalDAV 日历服务。

- 前端仓库：https://github.com/nar-oah/voice_calendar-client
- 在线体验：https://calendar.naroah.top/
- 后端入口：`main.py`

## 项目目标

真实用户在日历管理中的高频痛点通常不是“会不会创建日程”，而是创建动作太碎：打开日历、选日期、填标题、填时间、补地点、再保存。这个项目把这些步骤收敛到一句中文语音，例如“明天下午两点在肯德基吃饭”，再通过确认弹窗给用户二次校验，降低误识别带来的成本。

项目覆盖题目要求中的核心能力：

- 语音添加事件：前端使用浏览器语音识别，后端解析为结构化 `Event`，确认后写入数据库和 CalDAV。
- 语音删除事件：后端把“删除明天下午的肯德基吃饭”这类模糊表达映射到已存事件，前端确认后删除。
- 语音查看事件：后端识别查询意图和时间，前端跳转到对应日历日期。
- 事件提醒：前端在创建后用浏览器通知 API 注册当前页面生命周期内的提醒。
- 日历同步：使用 token 同步同一用户的已存事件，并提供当天 ICS 导出。

## 完整度说明

当前作品已经形成可运行的端到端闭环，而不是单独的语音识别演示：

| 模块 | 完成度 | 说明 |
| --- | --- | --- |
| 语音输入 | 已完成 | 前端通过 Web Speech API 识别 `zh-CN`，支持实时中间结果和手动编辑文本。 |
| 自然语言解析 | 已完成 | 后端提供规则快路径和 Gemini 结构化解析两条路径，输出统一的 Pydantic `Event`。 |
| 添加日程 | 已完成 | `/parser` 解析，`/add` 写入 PostgreSQL，并异步同步到 Radicale/CalDAV。 |
| 删除日程 | 已完成 | 支持语音解析删除意图，并用 PostgreSQL `pg_trgm` 在用户已有事件中做模糊匹配。 |
| 查看日程 | 已完成 | 支持语音解析查看意图，前端根据返回时间跳转到日历日期。 |
| 事件列表同步 | 已完成 | `/events` 按 token 拉取已存事件，前端启动时可恢复 token 并同步日程。 |
| 日历展示 | 已完成 | 前端使用 Schedule-X 展示当天日历、当前时间线和事件弹窗。 |
| 提醒 | 已完成基础版 | 创建成功后使用浏览器 Notification + `setTimeout` 提醒；页面关闭后不会持久保留。 |
| ICS 导出 | 已完成 | `/export` 从 CalDAV 中导出指定日期的 `calendar.ics`。 |
| 部署 | 已完成基础配置 | 提供 PostgreSQL schema 和 systemd service，前端使用 Cloudflare Pages 配置。 |

当前边界：

- 未实现周期性日程、冲突检测、跨端持久化提醒和修改事件。
- token 是轻量用户隔离方案，不是完整账号体系；拿到 token 即可访问对应日程。
- Radicale 服务本身的安装配置不在本仓库内，后端假设本机 `127.0.0.1:5232` 已可访问。
- 暂未加入自动化测试，主要依赖 FastAPI 的 OpenAPI schema、Pydantic 校验和手动联调。

## 创新点

1. 混合解析策略  
   后端不是把所有输入都交给大模型。`parser.py` 对“单个时间实体 + 简单创建意图”的语句使用 JioNLP 和规则直接解析，速度快、成本低；复杂语句、删除和查看意图再交给 Gemini。这样兼顾 72 小时项目的可控性和复杂表达的覆盖度。

2. 结构化模型约束大模型输出  
   `service.py` 使用 `Event.model_json_schema()` 作为 Gemini 的 JSON schema，`models.py` 再用 Pydantic 校验字段范围和结束时间必须晚于开始时间。大模型只负责语义理解，数据合法性由后端模型兜底。

3. 模糊语音删除/查看  
   用户删除日程时往往不会说出精确标题或 ID。`db.py` 使用 PostgreSQL `pg_trgm` 的 `%` 和 `similarity()`，在 token、时间范围、标题、地点、描述之间做模糊匹配，把“删掉明天那个肯德基”映射到具体事件。

4. 语音交互保留人工确认  
   前端不会直接执行高风险操作。语音解析结果先进入确认弹窗，用户可以修改标题、时间、地点、备注和操作类型，再执行创建、删除或查看，降低语音识别和模型解析的误操作风险。

5. 日历生态兼容  
   后端除了数据库持久化，还把事件同步到 Radicale/CalDAV，并支持 ICS 导出。这个设计让项目不局限在自定义页面中，具备和通用日历客户端集成的基础。

6. 无账号快速体验  
   `/token` 生成随机 token，前端保存到 localStorage。用户不需要注册即可体验同一 token 下的多次同步，适合比赛演示和短周期开发。

## 原创功能边界

本项目不是把第三方日历组件和大模型 API 简单拼接。以下部分为本项目原创实现：

- 后端 API 编排：`main.py` 中的 token、解析、列表、添加、删除、导出接口设计。
- 日程数据模型：`models.py` 中 `Action`、`Time`、`Event`、`StoredEvent` 以及时间顺序校验。
- 规则解析快路径：`parser.py` 中基于 JioNLP 时间识别、危险词过滤、地点/备注/标题抽取的中文日程解析逻辑。
- Gemini 结构化解析封装：`service.py` 中把用户文本转换成受 Pydantic schema 约束的日程对象。
- PostgreSQL 持久化与模糊事件匹配：`db.py` 中的 CRUD、token 隔离、`pg_trgm` 模糊查找和相似度排序。
- CalDAV/ICS 同步封装：`radicale.py` 中的 Radicale 用户创建、日历创建、事件增删、日期范围导出。
- 数据库 schema：`deploy/events.sql` 中事件表、时间约束、更新时间触发器和 trigram 索引。
- 前端交互流程：语音输入、确认编辑、Schedule-X 日历联动、token 同步、ICS 下载和浏览器提醒的业务流程由前端仓库实现。

第三方库承担的是底层能力：HTTP 框架、语音识别浏览器 API、中文时间识别、大模型调用、数据库驱动、CalDAV/ICS 协议、日历 UI 组件等。业务流程、数据模型、解析策略、模糊匹配和前后端联动逻辑均为项目实现。

## 技术架构

```text
浏览器前端
  Web Speech API -> 可编辑文本 -> /parser -> 确认弹窗
                                      |
                                      v
FastAPI 后端
  parser.py 规则快路径 -> Event
  service.py Gemini 解析 -> Event
  db.py PostgreSQL 持久化/模糊匹配
  radicale.py CalDAV 同步/ICS 导出
                                      |
                                      v
PostgreSQL + pg_trgm       Radicale CalDAV
```

### 核心流程

添加事件：

1. 前端把语音识别文本传给 `POST /parser`。
2. 后端优先尝试 `parser.py` 的规则快路径，无法处理时调用 Gemini。
3. 前端展示确认弹窗，用户确认后调用 `POST /add`。
4. 后端写入 PostgreSQL，并用 `BackgroundTasks` 异步写入 Radicale。
5. 前端把返回的 `StoredEvent` 添加到 Schedule-X 日历，并注册浏览器提醒。

删除事件：

1. 前端把“删除某个日程”的语音文本传给 `POST /parser`。
2. Gemini 解析出删除意图、时间范围和候选标题/地点/描述。
3. 后端用 `pg_trgm` 在该 token 的事件中找最相近的一条，返回带 `id` 的 `Event`。
4. 前端确认后调用 `POST /del`，后端删除数据库记录并异步删除 CalDAV 事件。

查看事件：

1. 前端把查询语音传给 `POST /parser`。
2. 后端解析查询时间和候选信息，必要时模糊匹配已有事件。
3. 前端确认后跳转到对应日期。

## 后端接口

FastAPI 启动后可访问 `/docs` 查看自动生成的 OpenAPI 文档。

| 方法 | 路径 | 参数 | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/token` | 无 | `str` | 生成 32 字节 URL-safe token。 |
| `POST` | `/events` | query: `token` | `StoredEvent[]` | 获取 token 下的所有事件。 |
| `POST` | `/parser` | query: `token`, `text` | `Event | null` | 把自然语言文本解析成创建/删除/查看事件。 |
| `POST` | `/add` | query: `token`; body: `Event` | `StoredEvent | null` | 新增事件并同步到 CalDAV。 |
| `POST` | `/del` | query: `token`, `id` | 空 | 删除数据库和 CalDAV 中的事件。 |
| `POST` | `/export` | query: `token`, `date` | `text/calendar` | 导出指定日期的 ICS 文件。 |

## 数据模型

`Action` 支持三类语音动作：

- `create`：创建日程。
- `delete`：删除日程。
- `read`：查看/跳转日程。

`Event` 是语音解析结果，包含动作、标题、开始时间、结束时间、地点和备注。`StoredEvent` 是数据库保存后的事件，额外包含数据库生成的 `id` 和 timezone-aware 的 `start_at`、`end_at`。

所有服务端时间在 `util.py` 中统一按 `Asia/Shanghai` 处理。

## 第三方依赖

### 后端 Python 依赖

来自本仓库 `requirements.txt`：

| 依赖 | 用途 |
| --- | --- |
| `fastapi` | 后端 HTTP API 框架和 OpenAPI schema 生成。 |
| `uvicorn` | ASGI 服务运行器。 |
| `google-genai` | 调用 Gemini，把复杂自然语言解析成结构化 JSON。 |
| `pydantic` | 请求/响应模型、字段范围校验和 JSON schema 生成。 |
| `jionlp` | 中文时间实体识别，用于规则快路径解析。 |
| `psycopg[binary]` | PostgreSQL 连接、SQL 执行和事务提交。 |
| `bcrypt` | 为 Radicale 用户文件生成 bcrypt 密码哈希。 |
| `caldav` | 通过 CalDAV 协议操作 Radicale 日历、事件搜索和删除。 |
| `icalendar` | 生成和解析 `.ics`/`VEVENT` 数据。 |

### 后端外部服务和系统能力

| 依赖 | 用途 |
| --- | --- |
| PostgreSQL | 保存事件数据。 |
| PostgreSQL `pg_trgm` 扩展 | 支持标题、地点、备注的模糊匹配和相似度排序。 |
| Radicale | 提供本地 CalDAV 服务，后端默认连接 `http://127.0.0.1:5232/`。 |
| Gemini API Key | `google-genai` 调用模型时需要。 |
| systemd | 生产部署时运行 `deploy/voice_calendar.service`。 |

### 前端运行依赖

来自前端仓库 `package.json` 的 `dependencies`：

| 依赖 | 用途 |
| --- | --- |
| `@preact/signals` | 响应式状态能力。 |
| `@schedule-x/calendar` | 日历核心组件。 |
| `@schedule-x/calendar-controls` | 控制日历日期跳转。 |
| `@schedule-x/current-time` | 当前时间线插件。 |
| `@schedule-x/event-modal` | 日历事件弹窗插件。 |
| `@schedule-x/events-service` | 前端事件增删服务。 |
| `@schedule-x/svelte` | Schedule-X 的 Svelte 绑定。 |
| `@schedule-x/theme-default` | Schedule-X 默认主题样式。 |
| `@schedule-x/theme-shadcn` | Schedule-X shadcn 主题样式。 |
| `openapi-fetch` | 基于 OpenAPI 类型调用后端接口。 |
| `preact` | 部分依赖所需的轻量 UI 运行时。 |
| `temporal-polyfill` | 浏览器 Temporal 时间对象兼容。 |

前端还使用浏览器原生能力，不属于 npm 第三方库：

- Web Speech API：中文语音识别。
- Notification API：浏览器提醒。
- localStorage：保存 token。

### 前端开发和部署依赖

来自前端仓库 `package.json` 的 `devDependencies`：

`@eslint/compat`、`@eslint/js`、`@sveltejs/adapter-cloudflare`、`@sveltejs/kit`、`@sveltejs/vite-plugin-svelte`、`@types/dom-speech-recognition`、`@types/node`、`@unocss/extractor-svelte`、`eslint`、`eslint-config-prettier`、`eslint-plugin-svelte`、`globals`、`openapi-typescript`、`prettier`、`prettier-plugin-svelte`、`svelte`、`svelte-check`、`typescript`、`typescript-eslint`、`unocss`、`vite`、`wrangler`。

这些依赖用于 SvelteKit 开发、Cloudflare Pages 构建、UnoCSS 样式、OpenAPI 类型生成、TypeScript 检查、ESLint 和 Prettier 格式化。

## 本地运行

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境

后端使用 `psycopg.connect()` 默认读取 libpq/psycopg 支持的连接配置。可通过环境变量配置数据库：

```bash
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=voice_calendar
export PGUSER=postgres
export PGPASSWORD=your-password
export GEMINI_API_KEY=your-gemini-api-key
```

生产部署时也可以把变量写入 `/home/admin/voice_calendar/.env`，供 systemd service 加载。

### 3. 初始化数据库

```bash
psql -d voice_calendar -f deploy/events.sql
```

`deploy/events.sql` 会：

- 启用 `pg_trgm`。
- 创建 `events` 表。
- 添加标题非空和结束时间晚于开始时间的约束。
- 创建时间索引和标题/地点/备注 trigram 索引。
- 创建 `updated_at` 自动更新时间触发器。

### 4. 准备 Radicale

后端默认：

- CalDAV 地址为 `http://127.0.0.1:5232/`。
- Radicale 用户文件为 `/etc/radicale/users`。
- 每个 token 对应一个 Radicale 用户。
- 日历名为 `Voice Calendar`。

首次添加某个 token 的事件时，后端会向 `/etc/radicale/users` 写入用户，并创建对应日历。

### 5. 启动服务

```bash
uvicorn main:app --reload
```

默认访问地址为 `http://127.0.0.1:8000`。

## 部署

仓库提供 systemd 服务文件：

```bash
sudo cp deploy/voice_calendar.service /etc/systemd/system/voice_calendar.service
sudo systemctl daemon-reload
sudo systemctl enable --now voice_calendar
sudo systemctl status voice_calendar
```

`deploy/voice_calendar.service` 默认配置：

- 工作目录：`/home/admin/voice_calendar`
- 环境文件：`/home/admin/voice_calendar/.env`
- 启动命令：`/home/admin/voice_calendar/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8007`

如部署路径、用户或端口不同，需要同步修改 service 文件。

## 代码目录

```text
.
├── main.py                    # FastAPI 入口和接口定义
├── models.py                  # Action/Event/StoredEvent 数据模型
├── parser.py                  # 中文规则解析快路径
├── service.py                 # Gemini 结构化解析
├── db.py                      # PostgreSQL 访问和模糊匹配
├── radicale.py                # Radicale/CalDAV/ICS 操作
├── util.py                    # Asia/Shanghai 时间转换
├── requirements.txt           # 后端 Python 第三方依赖
└── deploy/
    ├── events.sql             # PostgreSQL schema
    └── voice_calendar.service # systemd 服务文件
```

## 示例请求

```bash
TOKEN=$(curl -s http://127.0.0.1:8000/token)

curl -X POST "http://127.0.0.1:8000/parser?token=$TOKEN&text=明天下午两点在肯德基吃饭"
```

添加事件时把 `/parser` 返回的 `Event` 作为 JSON body 传给 `/add`：

```bash
curl -X POST "http://127.0.0.1:8000/add?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "id": 0,
    "title": "吃饭",
    "start": {"year": 2026, "month": 6, "day": 1, "hour": 14, "minute": 0, "second": 0},
    "end": {"year": 2026, "month": 6, "day": 1, "hour": 15, "minute": 0, "second": 0},
    "location": "肯德基",
    "description": null
  }'
```
