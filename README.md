# Voice Calendar Gemini Server

语音日历工具后端服务。本仓库负责自然语言日程解析、事件持久化、模糊删除/查看、CalDAV 自动同步和 ICS 导出，是“语音版日历工具”的后端实现。

- 后端线上地址：https://aws.naroah.top/calendar/
- 后端 OpenAPI 文档：https://aws.naroah.top/calendar/docs
- 前端仓库：https://github.com/nar-oah/voice_calendar-client
- 在线体验：https://calendar.naroah.top/
- 后端入口：`main.py`

本文档以本后端仓库为主。前端的组件、样式、浏览器语音输入和前端依赖会在前端仓库 README 中单独说明。

## 项目目标

题目要求是实现“以语音交互为核心的日历管理工具”，让用户可以顺畅地通过语音添加、删除、查看事件提醒。后端的目标是把用户的一句中文自然语言变成可执行、可校验、可持久化、可同步到日历生态的数据。

后端覆盖的核心能力：

- 语音文本解析：把前端识别出的中文文本解析为 `create`、`delete`、`read` 三类日程动作。
- 添加事件：解析结构化日程，写入 PostgreSQL，并同步到 CalDAV 日历。
- 删除事件：支持模糊表达，通过时间范围和标题/地点/备注相似度定位已有事件。
- 查看事件：解析查询意图和时间，返回前端可跳转的结构化结果。
- 持久化提醒：事件同步到 CalDAV 后，可由系统日历或支持 CalDAV 的客户端长期保存和提醒。
- ICS 导出：考虑到 CalDAV 配置对部分用户有门槛，提供选定日期的 `.ics` 文件导出，用户可直接导入本地日历进行持久化提醒。

## 完整度说明

后端已完成线上部署并可用，公网 Base URL 为 `https://aws.naroah.top/calendar/`。当前实现不是单独的大模型解析 demo，而是包含数据库、CalDAV、ICS 和部署配置的完整后端闭环。

| 模块 | 完成度 | 说明 |
| --- | --- | --- |
| 线上后端部署 | 已完成 | 服务已部署到 `https://aws.naroah.top/calendar/`，OpenAPI 文档可通过 `/docs` 访问。 |
| 自然语言解析 | 已完成 | 后端提供规则快路径和 Gemini 结构化解析两条路径，统一输出 Pydantic `Event`。 |
| 添加日程 | 已完成 | `/parser` 解析，`/add` 写入 PostgreSQL，并异步同步到 Radicale/CalDAV。 |
| 删除日程 | 已完成 | 支持语音删除意图，使用 PostgreSQL `pg_trgm` 在用户已有事件中模糊匹配目标事件。 |
| 查看日程 | 已完成 | 支持语音查看意图，返回可用于前端跳转日期的结构化时间。 |
| 数据库存储 | 已完成 | 使用 PostgreSQL 保存事件，包含时间约束、标题非空约束、更新时间触发器和模糊匹配索引。 |
| CalDAV 自动同步 | 已完成 | 首次添加事件时创建 Radicale 用户和 `Voice Calendar` 日历，新增/删除事件会同步到 CalDAV。 |
| 持久化提醒 | 已完成 | 通过 CalDAV 同步和 ICS 导出接入系统日历，提醒由用户本地日历或 CalDAV 客户端长期管理。 |
| ICS 导出 | 已完成 | `/export` 从 CalDAV 导出选定日期的 `calendar.ics`，降低用户配置 CalDAV 的门槛。 |
| token 用户隔离 | 已完成 | `/token` 生成随机 token，数据库和 CalDAV 均按 token 隔离用户日程。 |
| systemd 部署配置 | 已完成 | `deploy/voice_calendar.service` 提供后端常驻运行配置。 |

当前边界：

- 未实现周期性日程、冲突检测和修改事件。
- token 是轻量用户隔离方案，不是完整账号体系；拿到 token 即可访问对应日程。
- 后端生成标准 VEVENT；具体提醒提前量由导入/订阅的日历客户端按自身设置决定。

## 创新点

1. 混合解析策略  
   后端不是把所有输入都交给大模型。`parser.py` 对“单个时间实体 + 简单创建意图”的语句使用 JioNLP 和规则直接解析，速度快、成本低；复杂语句、删除和查看意图再交给 Gemini。这样兼顾 72 小时项目的开发效率、响应速度和复杂表达覆盖度。

2. 结构化模型约束大模型输出  
   `service.py` 使用 `Event.model_json_schema()` 作为 Gemini 的 JSON schema，`models.py` 再用 Pydantic 校验字段范围和结束时间必须晚于开始时间。大模型只负责语义理解，数据合法性由后端模型兜底。

3. 模糊语音删除/查看  
   用户删除日程时通常不会记得精确标题或事件 ID。`db.py` 使用 PostgreSQL `pg_trgm` 的 `%` 和 `similarity()`，在 token、时间范围、标题、地点、备注之间做模糊匹配，把“删掉明天那个肯德基”映射到具体事件。

4. 数据库与 CalDAV 双持久化  
   PostgreSQL 负责后端查询、模糊匹配和业务数据一致性；Radicale/CalDAV 负责接入通用日历生态。新增和删除都会同步到 CalDAV，使事件可以自动进入支持 CalDAV 的日历客户端。

5. CalDAV 与 ICS 双同步路径  
   CalDAV 适合长期自动同步，但配置对普通用户可能偏复杂。因此后端额外实现 `/export`，从 CalDAV 中导出选定日期 ICS 文件，用户可以用更低成本把当天日程导入系统日历并获得本地持久化提醒。

6. 无账号快速体验  
   `/token` 生成随机 token，token 同时作为数据库隔离键和 Radicale 账号。用户不需要注册即可体验同一 token 下的同步、导出和多次管理。

## 原创功能边界

本项目不是把第三方日历组件和大模型 API 简单拼接。以下部分为本后端仓库原创实现：

- 后端 API 编排：`main.py` 中的 token、解析、列表、添加、删除、导出接口设计。
- 日程数据模型：`models.py` 中 `Action`、`Time`、`Event`、`StoredEvent` 以及时间顺序校验。
- 规则解析快路径：`parser.py` 中基于 JioNLP 时间识别、危险词过滤、地点/备注/标题抽取的中文日程解析逻辑。
- Gemini 结构化解析封装：`service.py` 中把用户文本转换成受 Pydantic schema 约束的日程对象。
- PostgreSQL 持久化与模糊事件匹配：`db.py` 中的 CRUD、token 隔离、`pg_trgm` 模糊查找和相似度排序。
- CalDAV/ICS 同步封装：`radicale.py` 中的 Radicale 用户创建、日历创建、事件增删、日期范围导出。
- 数据库 schema：`deploy/events.sql` 中事件表、时间约束、更新时间触发器和 trigram 索引。
- systemd 部署配置：`deploy/voice_calendar.service` 中后端常驻运行配置。

第三方库承担的是底层能力：HTTP 框架、中文时间识别、大模型调用、数据库驱动、CalDAV/ICS 协议等。业务流程、数据模型、解析策略、模糊匹配、CalDAV 同步编排和导出逻辑均为本项目实现。

## 技术架构

```text
前端语音文本
    |
    v
FastAPI 后端
  main.py      API 路由、CORS、后台任务
  parser.py    规则快路径解析
  service.py   Gemini 结构化解析
  db.py        PostgreSQL 持久化和模糊匹配
  radicale.py  CalDAV 同步和 ICS 导出
    |
    +--> PostgreSQL + pg_trgm
    |
    +--> Radicale CalDAV
```

### 核心流程

添加事件：

1. 前端把语音识别文本传给 `POST /parser`。
2. 后端优先尝试 `parser.py` 的规则快路径，无法处理时调用 Gemini。
3. 前端确认后调用 `POST /add`。
4. 后端写入 PostgreSQL。
5. 后端用 `BackgroundTasks` 异步创建/更新 Radicale 日历事件。

删除事件：

1. 前端把“删除某个日程”的语音文本传给 `POST /parser`。
2. Gemini 解析出删除意图、时间范围和候选标题/地点/描述。
3. 后端用 `pg_trgm` 在该 token 的事件中找最相近的一条，返回带 `id` 的 `Event`。
4. 前端确认后调用 `POST /del`，后端删除数据库记录并异步删除 CalDAV 事件。

查看事件：

1. 前端把“查看某天日程”的语音文本传给 `POST /parser`。
2. 后端解析查询意图和时间范围，必要时复用模糊匹配定位已有事件。
3. 后端返回 `read` 类型的 `Event`，前端据此跳转到对应日期。

导出 ICS：

1. 前端提供 token 和选定日期，调用 `POST /export`。
2. 后端通过 CalDAV 查询 `Voice Calendar` 中该日期范围内的事件。
3. 后端合并 `VEVENT` 并返回 `text/calendar`，浏览器下载 `calendar.ics`。

## 后端接口

生产环境 Base URL：

```text
https://aws.naroah.top/calendar
```

FastAPI OpenAPI 文档：

```text
https://aws.naroah.top/calendar/docs
```

| 方法 | 路径 | 参数 | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/token` | 无 | `str` | 生成 32 字节 URL-safe token。 |
| `POST` | `/events` | query: `token` | `StoredEvent[]` | 获取 token 下的所有事件。 |
| `POST` | `/parser` | query: `token`, `text` | `Event  null` | 把自然语言文本解析成创建/删除/查看事件。 |
| `POST` | `/add` | query: `token`; body: `Event` | `StoredEvent  null` | 新增事件并同步到 CalDAV。 |
| `POST` | `/del` | query: `token`, `id` | 空 | 删除数据库和 CalDAV 中的事件。 |
| `POST` | `/export` | query: `token`, `date` | `text/calendar` | 导出指定日期的 ICS 文件。 |

## 数据模型

`Action` 支持三类语音动作：

- `create`：创建日程。
- `delete`：删除日程。
- `read`：查看/跳转日程。

`Event` 是语音解析结果：

| 字段 | 说明 |
| --- | --- |
| `action` | 用户要执行的操作。 |
| `id` | 已存事件 ID，创建时默认为 `0`，删除/查看匹配成功后会带上实际 ID。 |
| `title` | 事件标题。 |
| `start` | 事件开始时间，使用 `Time` 模型。 |
| `end` | 事件结束时间，必须晚于 `start`。 |
| `location` | 可选地点。 |
| `description` | 可选备注。 |

`StoredEvent` 是数据库保存后的事件：

| 字段 | 说明 |
| --- | --- |
| `id` | PostgreSQL 生成的主键。 |
| `title` | 事件标题。 |
| `start_at` | 带时区的开始时间。 |
| `end_at` | 带时区的结束时间。 |
| `location` | 可选地点。 |
| `description` | 可选备注。 |

所有服务端时间在 `util.py` 中统一按 `Asia/Shanghai` 处理。

## 数据库配置

后端使用 PostgreSQL。`Db()` 中调用 `psycopg.connect()`，因此连接配置由 libpq/psycopg 支持的环境变量提供。

推荐环境变量：

```bash
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=voice_calendar
export PGUSER=postgres
export PGPASSWORD=your-password
```

### 初始化数据库

创建数据库：

```bash
createdb voice_calendar
```

执行 schema：

```bash
psql -d voice_calendar -f deploy/events.sql
```

验证表结构：

```bash
psql -d voice_calendar -c '\d events'
```

如果执行 `CREATE EXTENSION IF NOT EXISTS pg_trgm;` 时权限不足，需要使用有扩展创建权限的数据库用户执行 `deploy/events.sql`，或提前由管理员启用 `pg_trgm`。

### events 表说明

`deploy/events.sql` 会创建 `events` 表：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `BIGINT IDENTITY PRIMARY KEY` | 数据库生成的事件 ID。 |
| `token` | `TEXT NOT NULL` | 用户隔离 token。 |
| `title` | `TEXT NOT NULL` | 事件标题，带非空白约束。 |
| `start_at` | `TIMESTAMPTZ NOT NULL` | 事件开始时间。 |
| `end_at` | `TIMESTAMPTZ NOT NULL` | 事件结束时间。 |
| `location` | `TEXT` | 可选地点。 |
| `description` | `TEXT` | 可选备注。 |
| `created_at` | `TIMESTAMPTZ` | 创建时间，默认 `now()`。 |
| `updated_at` | `TIMESTAMPTZ` | 更新时间，由触发器自动刷新。 |

约束：

- `events_title_not_blank`：标题去除空白后不能为空。
- `events_time_order`：`end_at` 必须晚于 `start_at`。

索引：

- `events_start_at_idx`：按开始时间查询。
- `events_time_range_idx`：按开始/结束时间范围查询。
- `events_title_trgm_idx`：标题模糊匹配。
- `events_location_trgm_idx`：地点模糊匹配，忽略空地点。
- `events_description_trgm_idx`：备注模糊匹配，忽略空备注。

更新时间触发器：

- `events_touch_updated_at()` 会在更新事件时自动刷新 `updated_at`。

### 模糊匹配逻辑

删除和查看不是按精确 ID 输入，而是按用户口语表达定位事件。`db.py` 中的 `get_blur_event()` 会：

- 限制 `token`，确保只在当前用户事件中匹配。
- 限制 `start_at >= event.start` 和 `end_at <= event.end`，减少时间范围外误匹配。
- 对 `title`、`location`、`description` 使用 trigram `%` 运算符筛选候选。
- 用 `similarity()` 分数排序，优先返回最接近的一条。

这让“删除明天下午在肯德基吃饭”这类表达能够匹配到真实数据库事件。

## CalDAV 与 ICS

后端通过 `radicale.py` 连接本机 Radicale：

| 配置 | 默认值 |
| --- | --- |
| CalDAV URL | `http://127.0.0.1:5232/` |
| 用户文件 | `/etc/radicale/users` |
| 日历名 | `Voice Calendar` |
| 事件 UID 后缀 | `@voice-calendar` |

首次添加某个 token 的事件时：

1. `add_user(token)` 使用 `bcrypt` 为 token 生成密码哈希。
2. 后端把 `token:hash` 写入 `/etc/radicale/users`。
3. 后端为该 token 创建 `Voice Calendar` 日历。
4. 新事件会写入 PostgreSQL，并作为 CalDAV `VEVENT` 写入 Radicale。

后续删除事件时：

1. 数据库按 token 和 id 删除事件。
2. CalDAV 根据 `id@voice-calendar` 搜索对应事件。
3. 找到后删除 CalDAV 中的事件。

ICS 导出：

- `/export` 接收 `token` 和 `date`。
- 后端用 CalDAV 查询该日期 `00:00:00` 到次日 `00:00:00` 范围内的事件。
- 使用 `icalendar` 合并 `VEVENT` 并返回 `text/calendar`。
- 用户可以导入系统日历，获得本地持久化保存和提醒能力。

运行服务的系统用户需要能写入 `/etc/radicale/users`，否则首次创建 token 的 CalDAV 用户会失败。

## 第三方依赖

### Python 依赖

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

### 外部服务和系统依赖

| 依赖 | 用途 |
| --- | --- |
| PostgreSQL | 保存事件数据。 |
| PostgreSQL `pg_trgm` 扩展 | 支持标题、地点、备注的模糊匹配和相似度排序。 |
| Radicale | 提供 CalDAV 日历服务。 |
| Gemini API Key | `google-genai` 调用模型时需要。 |
| systemd | 生产部署时运行 `deploy/voice_calendar.service`。 |

前端依赖不在本后端 README 展开，详见前端仓库。

## 本地运行

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=voice_calendar
export PGUSER=postgres
export PGPASSWORD=your-password
export GEMINI_API_KEY=your-gemini-api-key
```

### 3. 初始化数据库

```bash
createdb voice_calendar
psql -d voice_calendar -f deploy/events.sql
```

### 4. 准备 Radicale

确保 Radicale 运行在 `http://127.0.0.1:5232/`，并确保后端进程有权限写入 `/etc/radicale/users`。

### 5. 启动服务

```bash
uvicorn main:app --reload
```

默认本地访问地址为 `http://127.0.0.1:8000`。

## 生产部署

线上后端服务已经部署并可用：

```text
https://aws.naroah.top/calendar/
```

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
- 运行用户：`admin`

生产 `.env` 至少需要包含：

```bash
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=voice_calendar
PGUSER=postgres
PGPASSWORD=your-password
GEMINI_API_KEY=your-gemini-api-key
```

部署检查：

```bash
curl -I https://aws.naroah.top/calendar/docs
curl -s https://aws.naroah.top/calendar/openapi.json
```

如部署路径、Linux 用户、端口或反向代理路径不同，需要同步修改 `deploy/voice_calendar.service` 和前端 API base URL。

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

使用线上服务：

```bash
BASE_URL=https://aws.naroah.top/calendar
TOKEN=$(curl -s "$BASE_URL/token")

curl -X POST "$BASE_URL/parser?token=$TOKEN&text=明天下午两点在肯德基吃饭"
```

添加事件时把 `/parser` 返回的 `Event` 作为 JSON body 传给 `/add`：

```bash
curl -X POST "$BASE_URL/add?token=$TOKEN" \
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

导出选定日期 ICS：

```bash
curl -X POST "$BASE_URL/export?token=$TOKEN&date=2026-06-01" \
  -o calendar.ics
```
