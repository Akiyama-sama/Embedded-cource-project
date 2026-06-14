# 银行营业大厅排队叫号系统

这是一个面向 RK3562 Linux 开发板的银行大厅排队叫号演示系统。

## 功能

- 1 台中心板提供取号服务、数据库和实时广播
- 至少 2 个窗口页面作为叫号机
- 两种号码类型：`vip` 和 `normal`
- 按 `优先级 > 等候时间` 自动叫号
- 当日号票有效，跨日自动失效
- SQLite 持久化，重启后可继续服务
- WebSocket 实时同步
- 窗口叫号时浏览器语音播报

## 硬件拓扑

- RK3562 MiniEVM 作为中心板
- 其他 RK3562 板或任意浏览器设备打开窗口页面
- 所有设备接入同一局域网

## 环境要求

- Linux
- Python 3.11+
- Chromium 类浏览器
- 同一局域网内可访问中心板 IP

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## 启动

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 访问地址

- 取号页：`http://<中心板IP>:8000/take-number`
- 窗口 1：`http://<中心板IP>:8000/station/station-1`
- 窗口 2：`http://<中心板IP>:8000/station/station-2`

## 环境变量

- `QUEUE_DB_PATH`：SQLite 文件路径，默认 `data/queue.sqlite3`
- `CALL_STATION_COUNT`：窗口数量，默认 `2`
- `BUSINESS_TZ`：营业日时区，默认 `Asia/Shanghai`

## 使用流程

1. 启动服务后打开取号页
2. 客户点击优先业务或普通业务
3. 窗口页面点击“呼叫下一位”
4. 系统按优先级和等待时间选出下一位客户
5. 叫号时浏览器自动朗读对应号码

## 数据与恢复

- 未叫号的票号会写入 SQLite
- 服务重启后读取同一数据库即可继续叫号
- 跨天后，前一天仍未叫到的等待号会自动失效

## 坐席规模

修改 `CALL_STATION_COUNT` 即可扩展窗口数量。
例如设为 `4` 时，可部署 `station-1` 到 `station-4`。

## 常见问题

### 浏览器不播报

确认浏览器允许语音合成，窗口页点击叫号后会调用 `speechSynthesis`。

### 局域网打不开

确认 `uvicorn` 使用 `--host 0.0.0.0` 启动，并且浏览器访问的是中心板局域网 IP。

### 数据库文件在哪

默认在 `data/queue.sqlite3`。

## 测试

```bash
pytest -v
```
