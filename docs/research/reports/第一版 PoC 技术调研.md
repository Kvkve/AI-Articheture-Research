# Copilot SDK 能用自己的模型密钥支撑第一版 PoC，但它改动很快，多用户隔离和对话列表都要应用自己做

调研结论是：计划中的代理层（agent layer，即后端里负责"把用户的话交给模型、管理多轮对话、调用工具"的那一层）可以用。它就是 GitHub Copilot SDK，现在正在改名为 Microsoft Copilot SDK。第一版 PoC 由 React 前端、Python FastAPI 后端、多个用户和每人多段对话组成。按厂商文档，这一版可以建在它上面：只用项目自己的模型 API 密钥（BYOK）时，不需要 Copilot 订阅【厂商】；Python 有官方 BYOK 示例【厂商】；回答可以一段一段地流式产出【厂商】。不过，README 里"它驱动 Copilot CLI 作为运行时"这句话已经过时。从 2026 年 11 月的 2.0 版起，运行时默认直接加载进我们自己的 Python 进程。主要风险有五条。第一，变化快：8 个月里接口大改了三轮，2.0.1 版发布才 5 天，包名也换了，PyPI 上仍标着 "Alpha"。第二，SDK 不区分用户，用户隔离全靠应用自己做。第三，BYOK 相关的缺陷报告不少。第四，引擎（运行时）本身的许可证、是否开源、是否向厂商回传数据，读过的官方页面都没有写明；README 说 BYOK 不需要 GitHub 认证，但还没有实际运行验证过（主代理补查）。第五，对话历史存放在运行时所在机器的磁盘文件里，而给界面"读回历史消息"的方法没有核实。另外，三份笔记都没有调研 SDK 以外的替代方案，所以"用 SDK"和"先用普通模型客户端"哪个更好，目前没有研究支撑。

**阅读说明。** 所有来源的访问日期都是 2026-11-23（美国东部时间）。正文用四种标签标明证据强弱：【实测】指测量得到的数据，例如发布日期、元数据或某人实际测出的内存数字；【厂商】指 SDK 或库的作者对自己产品的说法；【经验】指某一个人或某一个团队的报告，例如一条 issue；【推断】指研究笔记或本报告自己的推理，没有直接来源。只在搜索结果摘要里看到、没有打开原文的内容，标"仅见摘要"；笔记标为未核实的，标"未核实"。研究笔记读网页时用的抓取工具会先由模型把网页摘要一遍，所以文中引文可能和原文措辞略有不同。本报告只使用三份研究笔记（[基础](../research_notes/第一版%20PoC%20技术调研/copilot_sdk_basics.md)、[多用户](../research_notes/第一版%20PoC%20技术调研/copilot_sdk_multi_user.md)、[开源组件](../research_notes/第一版%20PoC%20技术调研/open_source_components.md)）里的内容。写作时没有另外抓取任何网页。报告写完后，主代理在 2026-11-23 又读了四个官方页面（README、in-process-runtime.md、byok.md、SUPPORT.md），更正之处在文中标为“主代理补查”。第 12 节是主代理做的一次实际试跑，它更新了第 3、4、11 节里的几处“未核实”。

## 1. 结论摘要

- **能不能用：能，但要固定版本。** BYOK、Python、流式输出三项都有厂商文档和示例【厂商】。没有找到会挡住第一版 PoC 的硬性障碍【推断】（[基础笔记](../research_notes/第一版%20PoC%20技术调研/copilot_sdk_basics.md)）。
- **README 需要更新的地方：** 运行时已经不是 CLI 进程，默认在我们自己的进程里运行（见第 2 节）。
- **最需要自己动手的部分：** 一张"会话归属表"（记录哪段对话属于哪个用户），每次操作前都查它；再加上同一会话的并发锁（见第 5 节）。
- **最大的未知：** 引擎本身的许可证和是否回传数据；怎样把历史消息读出来给界面显示（见第 3、4、11 节）。

## 2. Copilot SDK 现在是什么，和 README 的描述有什么不同

**先解释几个词。** SDK（Software Development Kit，软件开发包）是一个可以 `import` 的库，类似 Python 里的 `pandas`。运行时（runtime）是真正干活的引擎：它负责和模型对话、调用工具、保存对话。CLI（Command-Line Interface，命令行程序）是在终端里输入命令运行的程序。Copilot CLI 就是一个这样的程序，它背后用的也是这个引擎。

- **它是什么。** 厂商的描述是"把 Copilot 的代理工作流嵌入你的应用"，用的是和 Copilot CLI 相同的引擎【厂商】（[仓库 README](https://github.com/microsoft/copilot-sdk)）。许可证是 MIT【厂商】（[仓库 README](https://github.com/microsoft/copilot-sdk)、[PyPI](https://pypi.org/project/microsoft-copilot-sdk/)）。官方支持六种语言：Node.js/TypeScript、Python、Go、.NET、Rust、Java【厂商】（[GA 公告 2026-06-02](https://github.blog/changelog/2026-06-02-copilot-sdk-is-now-generally-available/)）。
- **改名。** 2026-10-28 的公告说，"GitHub Copilot SDK" 正在改名为 "Microsoft Copilot SDK"，并分阶段迁到 Microsoft 组织下，没有给出具体日期；公告称"现有用户无需立即改动"【厂商】（[改名公告](https://github.blog/changelog/2026-10-28-github-copilot-sdk-is-becoming-microsoft-copilot-sdk)）。仓库页面现在可以在 `github.com/microsoft/copilot-sdk` 打开【厂商】（[仓库](https://github.com/microsoft/copilot-sdk)）。多用户笔记说旧地址 `github/copilot-sdk` 会自动跳转过来；主代理复查时看到新页面上的 Issues 链接仍指向旧地址，说明迁移还在进行中，两个地址之间谁跳转到谁，未核实。
- **运行时不再是 CLI。** 1.x 及预览期，每个 SDK 通过 JSON-RPC 和一个 Copilot CLI 服务器通信，必须先装好 CLI（JSON-RPC 是一种"用 JSON 格式远程调用函数"的约定，可以理解为跨进程的函数调用）【厂商，仅见摘要】（[技术预览公告 2026-01-14](https://github.blog/changelog/2026-01-14-copilot-sdk-in-technical-preview/)）。2.0 起，默认把一个用 Rust 写的原生运行时直接加载到我们自己的进程里（in-process，进程内）。它不再需要 Node.js，也不需要另起进程。另外还有两种方式：作为子进程启动，或者单独运行一个运行时服务器（`copilot-runtime --server`）【厂商】（[v2 破坏性变更](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)）。厂商自己提醒，进程内运行"没有崩溃隔离，也没有沙箱"【厂商】（同上）。
- **包名变了。** 2.0 的安装命令是 `pip install microsoft-copilot-sdk`，1.x 是 `pip install github-copilot-sdk`；代码里的 `import copilot` 不变。官方建议先卸载旧包【厂商】（[v2 破坏性变更](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)）。旧包在 PyPI 上已标为弃用（deprecated，即不再推荐使用）【厂商】（[PyPI 旧包](https://pypi.org/project/github-copilot-sdk/)）。
- **发布状态。** 时间线如下：2026-01-14 技术预览（仅见摘要），2026-04-02 公开预览（仅见摘要，只看到标题），2026-06-02 正式发布（GA，General Availability），公告称"API 已稳定、可用于生产"【厂商】（[GA 公告](https://github.blog/changelog/2026-06-02-copilot-sdk-is-now-generally-available/)）。2.0 在 Ignite 大会上发布，报道日期是 2026-11-17（[AlphaSignal](https://alphasignal.ai/news/microsoft-s-copilot-sdk-2-0-runs-95x-faster-by-ditching-containers-for-rust)，二手报道）。当前正式版是 v2.0.1（2026-11-18），之后几乎每天都有预发布版【实测】（[Releases](https://github.com/microsoft/copilot-sdk/releases)、[PyPI](https://pypi.org/project/microsoft-copilot-sdk/)）。2.0 的破坏性改动包括：改包名、`mode` 变成必填、参数改成分组、`provider` 改名为 `inference`、默认改为进程内运行；SDK 和运行时必须一起升级【厂商】（[v2 破坏性变更](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)）。
- **来源之间的矛盾，如实列出。**（1）厂商说"已正式发布、遵循语义化版本"（semantic versioning，指版本号的主版本号变了才允许不兼容的改动）【厂商】（[仓库 README](https://github.com/microsoft/copilot-sdk)），但 PyPI 上的分类仍是 "Development Status 3 - Alpha"【实测】（[PyPI](https://pypi.org/project/microsoft-copilot-sdk/)）。这是有意为之还是忘了更新，不知道。（2）旧包 `github-copilot-sdk` 1.0.35 和新包 `microsoft-copilot-sdk` 2.0.1 都在 2026-11-18 发布【实测】（[PyPI 旧包](https://pypi.org/project/github-copilot-sdk/)、[PyPI 新包](https://pypi.org/project/microsoft-copilot-sdk/)），说明两条版本线还在同时更新。（3）基础笔记读到的 CHANGELOG 没有任何 v2 条目，看起来是旧的缓存；多用户笔记读到的原始 CHANGELOG 文件则写了 v2 默认进程内运行（[CHANGELOG](https://github.com/microsoft/copilot-sdk/blob/main/CHANGELOG.md)）。两份笔记读到的是不同时刻的版本。
- **结论：README 哪句过时了。** 第 42 行的"The planned choice is the GitHub Copilot SDK, which drives the Copilot CLI as its runtime"已经不对。现在应该说：它的运行时默认在应用自己的进程里运行，也可以作为子进程或独立服务器运行，不再需要单独安装 Copilot CLI；产品名也正在改成 Microsoft Copilot SDK【推断】。

## 3. 只用项目自己的模型密钥（BYOK）

**BYOK**（Bring Your Own Key，自带密钥）指不用 Copilot 账户付费，而是把请求直接发给我们自己付费的模型服务（例如 OpenAI 或 Azure OpenAI）。API 密钥（API key）就是那家服务发的一串密码，类似数据库连接串里的密码。

**来源确认了什么：**
- 官方认证方式表格里，BYOK 一行写的是"不需要 GitHub Copilot 订阅"，费用直接由模型服务商收取；其他认证方式都需要 Copilot 订阅【厂商】（[认证方式](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate)）。主代理复查时也确认了这一点。
- 支持的服务商包括：OpenAI 及兼容接口、Microsoft Foundry / Azure OpenAI、Anthropic、Google Gemini（标为"实验性"）、Ollama、Foundry Local、vLLM、LiteLLM 等【厂商】（[BYOK 文档](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md)）。
- BYOK 下，能用的模型只限服务商提供的那些；限流和用量统计都由服务商负责；SDK 本身没有文档化的限流【厂商】（[BYOK 文档](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md)）。
- BYOK 只改变"模型请求发到哪里"，Copilot 运行时照样在运行【厂商，一位厂商工程师的博客】（[.NET 博客 2026-10-19](https://devblogs.microsoft.com/dotnet/bring-your-own-model-to-the-github-copilot-sdk-with-csharp/)）。Python 包会在第一次使用时自动下载运行时，缓存在 `~/.cache/copilot-sdk/` 下，也可以用 `python -m copilot download-runtime --in-process` 提前下载【厂商】（[Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)）。因此，第一次启动需要联网，或者事先把运行时打进镜像【推断】。

**仍未核实的：**
- **是否需要 GitHub 账号（主代理补查后更正）。** 认证页只说不需要订阅，没有提账号【厂商】（[认证方式](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate)）。主代理补查 README，其中写明 "With BYOK, you can use the SDK without GitHub authentication by configuring your own API keys from supported LLM providers"，认证方式列表里也写着 "BYOK - Use your own API keys (no GitHub auth required)"【厂商】（[README](https://raw.githubusercontent.com/microsoft/copilot-sdk/main/README.md)）。所以按厂商的说法，BYOK 不需要 GitHub 认证。但这还没有实际运行验证过，仍应在没有 GitHub 登录的环境里跑一遍示例来确认【推断】。
- 没有 GitHub 认证时会失去哪些功能（云端代理、GitHub MCP 服务器、代码搜索）：仅见摘要（[认证方式](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate)）。
- BYOK 本身的发布状态：一条搜索摘要称它是"public preview"，BYOK 文档页本身没有标注，两者矛盾，未解决。
- BYOK 是否只支持密钥：README 说不支持 Entra ID 和托管身份，但仓库里又有 `azure-managed-identity.md` 文档和一个令牌回调函数，.NET 博客把后者标为实验性【厂商】（[setup 目录](https://github.com/microsoft/copilot-sdk/tree/main/docs/setup)、[.NET 博客](https://devblogs.microsoft.com/dotnet/bring-your-own-model-to-the-github-copilot-sdk-with-csharp/)）。准确的限制范围不清楚。

**最小 Python 示例。** 来源：[docs/auth/byok.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md)，所在仓库的许可证是 MIT【厂商】。主代理在 2026-11-23 重新抓取了原始文件，这里用的就是那份完整文本。基础笔记末尾"无法核实"一节里还说示例"被工具压缩过"，那是复查之前写的，以复查结果为准。笔记提醒，代码在真正使用前仍应和原文再对一次。

```python
import asyncio
import os
from copilot import CopilotClient
from copilot.session import PermissionHandler

FOUNDRY_MODEL_URL = "https://<resource-name>.openai.azure.com/openai/v1/"
# Set FOUNDRY_API_KEY environment variable


async def main():
    client = CopilotClient(mode="coding-agent")
    await client.start()

    session = await client.create_session(
        model="gpt-5.2-codex",
        permissions={"on_request": PermissionHandler.approve_all},
        github={"capi": {"enabled": False}},
        inference={
            "default_provider": "byok",
            "providers": [
                {
                    "name": "byok",
                    "type": "openai",
                    "base_url": FOUNDRY_MODEL_URL,
                    "wire_api": "responses",  # Use "completions" for older models
                    "api_key": os.environ["FOUNDRY_API_KEY"],
                }
            ],
        },
    )

    done = asyncio.Event()

    def on_event(event):
        if event.type.value == "assistant.message":
            print(event.data.content)
        elif event.type.value == "session.idle":
            done.set()

    session.on(on_event)
    await session.send("What is 2+2?")
    await done.wait()

    await session.disconnect()
    await client.stop()


asyncio.run(main())
```

**逐行说明。** 先解释 `async`/`await`（异步）：程序在等待网络回应时不会卡住，可以先去做别的事；`await` 表示"在这里等结果回来"。这个 SDK 的 Python 版本身就是按异步方式设计的，要求 Python 3.11 及以上【厂商】（[Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)）。

| 代码 | 用大白话说 |
|---|---|
| `import ...` 四行 | 导入标准库 `asyncio`（异步）和 `os`（读环境变量），再导入 SDK 的客户端类和权限处理器。 |
| `FOUNDRY_MODEL_URL = ...` | 模型服务的网址，`<resource-name>` 处换成自己的资源名。下一行注释提醒：密钥放在环境变量 `FOUNDRY_API_KEY` 里，不写进代码。 |
| `CopilotClient(mode="coding-agent")` | 创建客户端，相当于 Java 里 `new` 一个对象。`mode` 在 2.0 里是必填。`coding-agent` 会打开读写文件、执行命令这类工具；厂商建议多用户服务器改用 `empty`【厂商】（[v2 破坏性变更](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)）。 |
| `await client.start()` | 启动运行时，类似先打开数据库连接。 |
| `create_session(model=...)` | 开一段新对话（会话，见第 4 节），并指定模型名。不指定模型会报 "Model not specified"【厂商】（[BYOK 文档](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md)）。 |
| `permissions={"on_request": PermissionHandler.approve_all}` | 模型想调用工具时，由谁来批准。`approve_all` 表示全部批准。示例这样写只是为了简单；笔记建议正式代码不要照抄，而是只放行一份明确的工具清单【推断】。 |
| `github={"capi": {"enabled": False}}` | 关掉 Copilot 自带的模型服务，只走我们自己的服务商。 |
| `inference={...}` | 定义模型服务商：起个名字 `byok`；`type` 是接口类型；`base_url` 是网址；`wire_api` 选接口风格（`responses`，旧模型用 `completions`）；`api_key` 从环境变量读取。 |
| `done = asyncio.Event()` | 一个"完成信号"，等回答结束时把它设为已完成。 |
| `def on_event(event)` | 事件处理函数（回调，callback：交给别人、由别人在事情发生时调用的函数）。收到 `assistant.message`（完整回答）就打印出来，收到 `session.idle`（本轮结束）就发出完成信号。 |
| `session.on(on_event)` | 把这个函数登记到会话上。 |
| `await session.send(...)` | 发送用户的问题。 |
| `await done.wait()` | 等到本轮结束。 |
| `disconnect()` / `stop()` | 断开会话（释放内存，磁盘上的数据保留），然后关闭客户端。 |
| `asyncio.run(main())` | 运行上面这个异步主函数。 |

## 4. 会话（session）

**会话是什么。** 一个会话就是运行时里保存的一段对话【厂商】（[session-persistence.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/features/session-persistence.md)）。用 SQL 打比方：会话 id 像主键（primary key），一个 id 对应一段对话。

- **id 由谁定：** 应用可以在 `create_session` 时自己传入 `session_id`；不传的话由运行时生成，应用必须自己把它存下来。文档推荐的格式是 `user-{userId}-{taskId}`【厂商】（[session-persistence.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/features/session-persistence.md)、[Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)）。
- **怎样恢复（resume）：** 调用 `await client.resume_session(session_id, ...)`；会话不存在时会抛出 `RuntimeError`。另外有 `list_sessions()`（列出会话）、`get_session_metadata()`（查元数据）、`delete_session()`（从磁盘彻底删除）。这些 Python 方法名来自源码文件 `client.py`，笔记只读了其中一部分【厂商】（[client.py](https://github.com/microsoft/copilot-sdk/blob/main/python/copilot/client.py)）。会话处理过至少一条消息后才可以恢复【厂商】（[session-persistence.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/features/session-persistence.md)）。
- **每次恢复都要重新提供：** BYOK 配置（包括密钥）和权限处理器【厂商】（同上）。

### 对话历史存在哪里

**结论：存在运行时所在机器的磁盘上，一段对话一个文件夹，路径是 `~/.copilot/session-state/{sessionId}/`。不在 SDK 的远程服务里，也不在我们的数据库里。**【厂商】（[session-persistence.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/features/session-persistence.md)、[multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)）

- 文件夹里有：`events.jsonl`（事件日志，也就是对话历史）、`workspace.yaml`（元数据）、`checkpoints/`（压缩后的摘要）、`plan.md`、`files/`（产出的文件），工具调用的结果也会保存【厂商】（同上）。用 SQL 的话说，`events.jsonl` 像一张只能追加、不能修改的日志表，每一行是一个事件；但它只是磁盘上的文本文件，没有数据库可以查询【推断】。
- 存储位置可以改：用 `COPILOT_HOME`、`--config-dir` 或 `baseDirectory` 指定目录；也可以接一个 `sessionFs` 提供者，把文件写到我们自己控制的存储里【厂商】（[multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)）。有没有现成的数据库版 `sessionFs`，没有找到。
- "云端会话"是另一个可选功能，笔记没有展开调研。
- **不保存的：** 服务商密钥（"从不写入磁盘"）和内存里的工具状态【厂商】（[session-persistence.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/features/session-persistence.md)）。

**重启后还剩什么。** 运行时重启、后端重启、容器迁移之后，只要存储还在，历史、工具结果、`plan.md` 和 `files/` 都还在。但如果机器或容器本身丢了，状态也跟着丢，除非那个文件夹放在持久卷（persistent volume，指容器删掉后仍然保留的磁盘）上【厂商】（[session-persistence.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/features/session-persistence.md)、[scaling.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/scaling.md)）。"只批准一次"的权限答复不会恢复【厂商】（同上）。日志文件损坏时，`allowTranscriptRecovery`（默认开启）会尝试修复【厂商】（同上）。

**长对话。** 模型一次能读的文字量有上限，叫上下文窗口（context window）。SDK 有"无限会话"功能：对话快装满时在后台做压缩（compaction，把较早的内容总结成摘要），阈值可以设置，例如 0.80 和 0.95，摘要写进 `checkpoints/`【厂商】（[Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)）。压缩之后，完整日志应该还留在磁盘上，这是根据文件布局推出来的，文档没有明说【推断】。

**给界面读回历史，目前不清楚。** Python README 写了 `get_events()` 用于"会话历史"，但它的参数和返回格式都没有核实；也没有找到 `get_messages` 这类方法。另一份文档说，可以通过 `sessionStatePath` 直接去读 `events.jsonl`【厂商】（[Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)、[session-management.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/session-management.md)）。哪种方式更适合聊天界面，未核实。文档也没有说应用该不该把消息另存一份到自己的数据库【厂商】。不过，一张记录会话 id、所属用户、标题和时间的小表，无论怎样都需要【推断】（[多用户笔记](../research_notes/第一版%20PoC%20技术调研/copilot_sdk_multi_user.md)）。

## 5. 多个用户

**SDK 本身不区分用户。** 它没有"用户"或"租户"（tenant，指共用同一系统的不同客户或用户群）的概念。厂商原话是："应用负责请求路由和权限判断，SDK 和运行时只提供每个会话各自的状态、各自的认证，以及显式登记的工具"；又说"你的应用必须规定哪个用户能访问哪个会话"【厂商】（[multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)、[scaling.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/scaling.md)）。

**应用必须自己做的两件事：**
1. **归属表。** 在自己的数据库里建一张表，至少包含会话 id 和所属用户 id 两列，类似 SQL 里的 `conversations(session_id PRIMARY KEY, owner_user_id, title, created_at, last_used_at)`【推断】（[多用户笔记](../research_notes/第一版%20PoC%20技术调研/copilot_sdk_multi_user.md)）。
2. **每次操作前先检查。** 在恢复、发送、删除，或者界面上任何指向某个会话的操作之前，先查这张表，确认当前用户就是这段对话的主人。厂商列出的常见错误里就有一条"信任客户端传来的会话 id 而不做归属检查"【厂商】（[multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)）。文档自己的示例是从会话 id 的前缀里解析出用户 id 来判断权限，文档也承认这种做法脆弱；更稳妥的是查数据库【厂商】+【推断】（[scaling.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/scaling.md)）。`list_sessions()` 返回的是服务器上的全部会话，必须先用归属表过滤，才能显示给用户【推断】。

**厂商的其他建议：**
- **模式：** 共享的服务器上用 `mode="empty"`，因为 `coding-agent` 会把服务器上的文件工具暴露给模型【厂商】（[multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)）。
- **工具权限：** 用 `available_tools` 列出允许的工具（白名单）；自己写一个权限处理器，只放行名单上的工具。2.0 里如果不设处理器，请求会一直挂起，既不批准也不拒绝【厂商】（[v2 破坏性变更](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)）。记住的权限答复文件（`permissions.json` 等）不按会话分开存放【厂商】（[multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)）。
- **没有内置锁：** 两个请求同时操作同一个会话，结果是未定义的（undefined，即文档不保证会发生什么）。需要自己加锁或排队，就像数据库里两个事务同时改同一行时需要锁【厂商】（[session-persistence.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/features/session-persistence.md)、[scaling.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/scaling.md)）。
- **其他：** 设置空闲超时，聊天类后端建议 15 到 30 分钟【厂商】（[multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)）。连接到独立运行时服务器时，空闲超时默认是关闭的；空闲会话会被移出内存，但不会从磁盘删除，后一点是从 issue 日志推出来的【推断】（[issue #2889](https://github.com/microsoft/copilot-sdk/issues/2889)）。不要让多个用户共用同一个 GitHub 令牌【厂商】。在 BYOK 下，项目密钥本来就是所有会话共用的【推断】。

## 6. 部署形态

| 形态 | 怎么运行 | 代价 | 证据 |
|---|---|---|---|
| 进程内（2.0 默认） | Rust 运行时直接加载进 FastAPI 的 Python 进程 | 最简单；但没有沙箱、没有崩溃隔离，运行时一崩溃，所有用户的对话一起中断；运行时版本要和操作系统、CPU、Linux C 库匹配 | 【厂商】[in-process-runtime.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/in-process-runtime.md) |
| 子进程 | SDK 自己启动并管理一个运行时进程（`for_spawned_stdio()` 或 `for_spawned_tcp()`） | 有崩溃隔离；多一个进程要管 | 【厂商】同上、[Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md) |
| 独立运行时服务器 | `copilot-runtime --server --port 4321`，多个后端通过 TCP（一种网络连接方式）连上来 | 可以单独重启，多个后端实例能共用；但它是单点故障；通信是明文 TCP、没有 TLS 加密；不监听本机时必须设置连接令牌；没有官方 Docker 镜像，要自己打包；会话文件夹必须放在持久存储上 | 【厂商】[backend-services.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/backend-services.md) |
| 每个用户一个运行时 | 每个用户单独一个运行时 | 隔离最强、成本最高；需要进程管理和空闲关闭逻辑；内存数字没有找到 | 【厂商】[scaling.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/scaling.md) |
| 临时会话加自存历史 | 每个请求新建一个会话，用完就断开，历史从自己的数据库回放 | 避开恢复相关的缺陷和磁盘文件夹；但要自己存历史，失去 SDK 的压缩和工具状态 | 【厂商】"ephemeral" 模式见 [scaling.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/scaling.md)；代价是【推断】 |

补充：后端要跑多个实例时，会话文件必须放在共享存储上，或者用"粘性会话"（sticky session，让同一个用户总是落到同一台服务器）。SDK 没有内置锁，也没有负载均衡【厂商】（[scaling.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/scaling.md)）。官方示例的会话管理器把活跃会话上限设为 50，但文档承认它的淘汰策略不是真正的 LRU（Least Recently Used，最久未用的先淘汰），也不检查正在处理中的请求【厂商】（同上）。厂商宣称 2.0 每轮额外开销从 5.25 秒降到 55.3 毫秒，10 个客户端的内存从 1,383 MB 降到 126 MB；这是厂商自己的测试，没有给出硬件条件，应视为未核实【厂商】（[AlphaSignal](https://alphasignal.ai/news/microsoft-s-copilot-sdk-2-0-runs-95x-faster-by-ditching-containers-for-rust)）。空闲运行时的内存和启动时间，没有找到任何独立数据。

## 7. 流式输出，从头到尾

流式输出（streaming）指模型一边生成，浏览器一边显示，不用等整段回答写完。整条链路分三段：

1. **后端从 SDK 拿事件。** 创建会话时加上 `events={"streaming": True}`，SDK 就会推送很多个 `assistant.message_delta` 事件，每个带一小段新文字 `delta_content`；最后推送一个完整的 `assistant.message`，再推送 `session.idle` 表示本轮结束【厂商】（[Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)、[getting-started.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/getting-started.md)）。这些是 Copilot 自己定义的事件，不是模型服务商的原始数据流，后端必须把它们翻译成浏览器能理解的格式【推断】。
2. **经过一种传输方式（transport）送到浏览器。** 三种选择见下表【厂商，FastAPI 文档】+【推断】（[开源组件笔记](../research_notes/第一版%20PoC%20技术调研/open_source_components.md)）。
3. **浏览器拼接显示。** 前端读取数据流，把每段文字依次追加到当前消息末尾。

| 传输方式 | 是什么 | FastAPI 不装额外包能做吗 | 代价 |
|---|---|---|---|
| SSE（Server-Sent Events，服务器推送事件） | 一个持续很久的 HTTP 响应，类型是 `text/event-stream`，每条消息以 `data:` 开头、以空行结束 | 能。0.135.0 起自带 `fastapi.sse`，每 15 秒发一次保活信号（keep-alive，防止连接因为太安静被中间设备断开），并自动设置 `Cache-Control: no-cache` 和 `X-Accel-Buffering: no`【厂商】（[FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/)，主代理已复查） | 浏览器自带的 `EventSource` 只能发 GET、不能带认证头，聊天要发 POST，所以得改用 `fetch` 读数据流【经验，仅见摘要】（[DEV 文章](https://dev.to/ohugonnot/sse-with-fetch-readablestream-authenticated-streaming-without-eventsource-604)）；断线重连不会补回漏掉的文字【厂商】（[Render](https://render.com/articles/sse-vs-websockets-llm-streaming)） |
| WebSocket | 把一条 HTTP 连接升级成双向通道，两边随时都能发消息 | 基本能，由 Starlette 支持，但需要装 `websockets` 包【厂商】（[FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)） | 只有回答过程中浏览器也要往服务器发数据时才需要；不能设置自定义请求头，没有自动重连；有些代理需要额外配置【厂商】（[Render](https://render.com/articles/sse-vs-websockets-llm-streaming)） |
| JSON Lines（NDJSON） | 普通响应，每行一个 JSON 对象，边生成边发 | 能。0.134.0 起支持，内容类型是 `application/jsonl`；也可以用 `StreamingResponse` 配合 `yield`【厂商】（[FastAPI JSON Lines](https://fastapi.tiangolo.com/tutorial/stream-json-lines/)、[stream data](https://fastapi.tiangolo.com/advanced/stream-data/)） | 最容易读懂和调试，可以用 POST、可以带任何请求头；没有内置的重连和事件编号【推断】 |

（`yield` 就是 Python 生成器里的那个关键字：函数每算出一段就交出去一段，而不是最后一次性 `return`。）

**已发布的消息格式**（传输方式之上，每条消息里装什么）：
- **Vercel AI SDK UI 消息流：** 基于 SSE，每条是 `data: {json}`，最后以 `data: [DONE]` 结束，响应头带 `x-vercel-ai-ui-message-stream: v1`，消息块类型有 `text-start`、`text-delta`、`text-end`、`finish` 等。文档说明 Python 这样的其他语言后端也可以按这个格式输出【厂商】（[stream protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol)，主代理已复查）。
- **AG-UI：** 事件类型有 RunStarted、TextMessageContent、RunFinished 等，走 HTTP+SSE，有 Python SDK，MIT 许可证【厂商】（[AG-UI 事件](https://docs.ag-ui.com/concepts/events)、[仓库](https://github.com/ag-ui-protocol/ag-ui)）。
- **assistant-ui 自己的格式：** SSE `data:` 行，或者更早的 `aui-state:` 行【厂商】（[assistant-transport](https://www.assistant-ui.com/docs/runtimes/custom/assistant-transport)）。
- **OpenAI chat-completions 分块：** `chat.completion.chunk`，以 `data: [DONE]` 结束【厂商】（[OpenAI 参考](https://developers.openai.com/api/reference/resources/chat)）。

**哪个前端库认哪种格式：** `useChat` 认 AI SDK UI 消息流，或者配上文本传输时认纯文本；assistant-ui 认 AI SDK UI 消息流或它自己的格式；CopilotKit 认 AG-UI；chatscope 和 react-markdown 不关心格式，网络部分要自己写。前四条是笔记读过文档的结论，最后一条（没有哪个组件直接认 OpenAI 分块格式）是推断（[开源组件笔记](../research_notes/第一版%20PoC%20技术调研/open_source_components.md)）。

## 8. 可以借用的开源组件

先解释许可证。MIT、Apache-2.0、BSD 是宽松许可证，基本上注明出处就可以使用；项目规则规定，其他许可证要先问 owner。"归档"（archived）指仓库被设为只读，不会再更新。

| 名称 | 用途 | 许可证 | 维护状态 | 适合度【推断】 | 来源 |
|---|---|---|---|---|---|
| create-vite（react-ts 模板） | 生成前端项目骨架 | MIT | 文档显示 v8.3.7，日期不明 | 好：小 | [Vite](https://vite.dev/guide/) |
| FastAPI | 后端框架 | MIT | 0.165.0，2026-11-18；仍是 0.x 版，发布频繁 | 好；自带 SSE 和 JSON Lines | [releases](https://github.com/fastapi/fastapi/releases.atom) |
| full-stack-fastapi-template | 官方全栈模板 | MIT | 2026-11-16 有提交 | 适合阅读、删减后使用；整套太大（登录、PostgreSQL、Docker、Traefik、邮件、端到端测试），没有聊天功能 | [仓库](https://github.com/fastapi/full-stack-fastapi-template) |
| sse-starlette | SSE 辅助库 | BSD-3-Clause | 3.7.1，2026-11-22，只有一位维护者 | FastAPI 0.135+ 已不需要 | [PyPI](https://pypi.org/project/sse-starlette/) |
| @azure/fetch-event-source | 浏览器端 SSE 客户端 | MIT（仅见仓库页面） | 日期不明，**维护情况未核实** | 可选；用普通 `fetch` 也行 | [仓库](https://github.com/Azure/fetch-event-source) |
| assistant-ui | 聊天界面加运行时 | MIT | 2026-11-22，几乎每天发布 | 界面好但重；绑定它支持的格式；Python 包 `assistant-stream` 的**许可证未核实** | [仓库](https://github.com/assistant-ui/assistant-ui) |
| Vercel AI SDK UI（`useChat`） | 聊天状态钩子（hook，React 里可复用的一段状态逻辑） | Apache-2.0 | 2026-11-23 | 前提是后端输出它的格式；大版本之间改动多 | [文档](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot) |
| Vercel AI Elements | 界面组件 | Apache-2.0 | **2026 年 11 月底弃用**，并入 shadcn/ui | 不要用 | [站点](https://elements.ai-sdk.dev/) |
| chatscope chat-ui-kit-react | 纯界面组件 | MIT（仅见页面徽标和 README） | v2.1.1，2025-05-15，**18 个月没有新版本** | 简单；流式部分要自己写 | [README](https://raw.githubusercontent.com/chatscope/chat-ui-kit-react/master/README.md) |
| CopilotKit / AG-UI | 代理界面加协议 | MIT / MIT（AG-UI 仅见页面） | 2026-11-23 / 日期不明 | 对纯聊天来说太多 | [仓库](https://github.com/CopilotKit/CopilotKit) |
| react-markdown / Streamdown | 渲染 Markdown | MIT / Apache-2.0 | 日期不明 | 好：小 | [react-markdown](https://github.com/remarkjs/react-markdown)、[Streamdown](https://github.com/vercel/streamdown) |
| LibreChat | 完整聊天应用 | MIT | v0.8.9，2026-11-17；已被 ClickHouse 收购（仅见摘要） | 只作参考；太大 | [仓库](https://github.com/danny-avila/LibreChat) |
| Vercel `chatbot` | 完整聊天应用 | Apache-2.0 | 日期不明 | 可参考它的结构；技术栈是 Next.js | 见[开源组件笔记](../research_notes/第一版%20PoC%20技术调研/open_source_components.md) |
| Open WebUI | 完整聊天应用 | **非宽松许可：Open WebUI License**（BSD 加品牌条款，项目自称"不是 OSI 认可的开源许可证"） | v0.13.4，2026-11-17 | 不要借用代码；要用须问 owner | [LICENSE](https://raw.githubusercontent.com/open-webui/open-webui/main/LICENSE)、[说明](https://docs.openwebui.com/license/) |
| LobeHub | 完整聊天应用 | **非宽松许可：LobeHub Community License**（分发衍生作品需要商业许可；README 徽标写的却是 Apache 2.0，两者矛盾） | 日期不明 | 不要借用；须问 owner | [LICENSE](https://raw.githubusercontent.com/lobehub/lobehub/canary/LICENSE) |
| Chainlit | Python 聊天框架 | Apache-2.0 | **已于 2026-10-15 归档，只读** | 不要在它上面搭建 | [仓库](https://github.com/Chainlit/chainlit) |
| ai-sdk-preview-python-streaming | 演示项目 | **许可证未核实**（LICENSE 文件返回 404） | 日期不明 | 只读，看 Python 怎样输出协议 | [仓库](https://github.com/vercel-labs/ai-sdk-preview-python-streaming) |
| copilot-sdk-server-sample | SDK 多用户示例 | MIT（仅见页面） | 日期不明 | 是 Express 加 React，不是 Python；它自己说明没有认证、没有会话权限检查 | [仓库](https://github.com/github/copilot-sdk-server-sample) |

表中维护数据（日期、版本）是笔记从发布订阅源和仓库页面读到的【实测】，用途说明出自各项目自己的介绍【厂商】。Chainlit、chatscope、AG-UI、react-markdown、fetch-event-source 的许可证只在仓库页面上看到，没有读原始 LICENSE 文件。没有找到 FastAPI 多用户的官方示例（仅见摘要：一次搜索没有结果）。

## 9. 风险与批评

| 风险 | 内容 | 证据强度 |
|---|---|---|
| 版本变化快 | 8 个月内接口大改三轮（0.x、1.0、2.0）；2.0.1 版只有 5 天；包改了名；v2.0.1 的发布说明写着"恢复旧的导入方式"，说明改名弄坏过一些用户的代码 | 【厂商】[Releases](https://github.com/microsoft/copilot-sdk/releases)；"需要固定版本"是【推断】 |
| 升级运行时后超时 | 一位用户用 Python SDK 1.0.18 加本地 BYOK 服务，运行时从 1.0.92 升到 1.0.94 后，`send_and_wait` 等了 60 秒仍没等到 `session.idle`；原因没有确认，最后退回旧版本 | 【经验】一人，[#2826](https://github.com/microsoft/copilot-sdk/issues/2826) |
| BYOK 参数不生效 | `maxOutputTokens` 没有传到上游（#2748，未关闭）；`maxContextWindowTokens` 被忽略（#2756，未关闭）；Anthropic 的 `max_tokens` 曾被写死为 8192，导致回答被悄悄截断（#955，已修复）；BYOK Anthropic 不触发压缩（#1072，已关闭） | 【经验】只读了标题和日期，[issue 搜索](https://github.com/microsoft/copilot-sdk/issues?q=is%3Aissue+python+byok) |
| BYOK 事件缺失 | Anthropic BYOK 缺少会话事件（#1064，已关闭）；输出达到 token 上限时部分事件不发出（#2546，已关闭） | 【经验】只读了标题，同上 |
| 恢复大会话时内存暴涨 | 恢复一个会话要占用约 3 倍于其 `events.jsonl` 大小的内存（250 MB 的日志多占约 750 MB）；有两个运行时分别涨到 12.8 GB 和 8.0 GB；15 MB 的小会话没有问题；环境是 macOS、SDK 1.0.27 测试版；另有一位 Windows 用户跟帖说两个长会话占了约 12 GB | 【实测】一人在自己环境里测得，[#2889](https://github.com/microsoft/copilot-sdk/issues/2889)，未关闭 |
| 进程内运行时崩溃 | .NET 在 Windows 上进程内运行出现非法访问（#2821，未关闭）；Rust 进程内有释放后使用的风险（#2793，已关闭） | 【经验】仅见摘要；与厂商"进程内没有崩溃隔离"的提醒一致 |
| 恢复后权限处理器不再被调用 | #2852（未关闭）；中止会话后工具调用一直失败（#2871，未关闭） | 【经验】仅见摘要 |
| 工具被执行两次 | 重复送达的 `external_tool.requested` 会让一个不能重复执行的工具处理函数跑两次（#2926，未关闭） | 【经验】只读了标题，[issue 列表](https://github.com/microsoft/copilot-sdk/issues) |
| 并发会话的成本 | 每个活跃会话都会启动全部扩展和整套 MCP（#2928）；跨会话的提示缓存失效（#2915）；推断这会增加大量并发对话时的开销和 token 费用 | 【经验】只读了标题；成本影响是【推断】 |
| 跨会话串数据 | Rust 路由可能把请求发到已被替换的会话（#2791，仅限 Rust，已修复）；账户级 "Copilot Memory" 是否会带进新会话（#2772，没有维护者回复；提问者说这只是文档问题，没有观察到实际泄漏；BYOK 下是否适用未核实） | 【经验】#2791 仅见摘要，#2772 读过原文 |
| 浏览器与服务器之间的链路 | 代理服务器缓冲、gzip 压缩、空闲超时会让文字成批到达或者断流：Starlette 的 gzip 问题已于 2025-02-16 修复；nginx 有时要关闭缓冲；Cloudflare 大约缓冲 100 KB 才转发；AWS ALB 和 nginx 默认约 60 秒空闲就断开 | 【实测】[Starlette PR](https://github.com/Kludex/starlette/pull/2753)；【经验】nginx 仅见摘要；【厂商】[sse-starlette](https://github.com/sysid/sse-starlette)、[Render](https://render.com/articles/sse-vs-websockets-llm-streaming) |
| 前端库的格式变动 | Vercel AI SDK 5 改了消息结构（`content` 变成 `parts`），传输格式也从 `TYPE_ID:JSON` 改成了 SSE JSON | 【厂商】+【经验】仅见摘要，[迁移指南](https://ai-sdk.dev/docs/migration-guides/migration-guide-5-0) |
| 许可证与维护 | Open WebUI 改许可证后反应大多负面，Nixpkgs 把它标为非自由软件（改许可证的日期，一处说 2025-04-19，另一处说 2025-05-05）；Chainlit 在最后一次发布约 5 个月后归档，没有说明原因 | 【经验】仅见摘要；Chainlit 是【实测】 |

整体上，SDK 问题列表里有 178 个未关闭的 issue【实测】（[issue 列表](https://github.com/microsoft/copilot-sdk/issues)）。没有找到独立的生产环境事故复盘，也没有找到"一个用户读到另一个用户会话"的报告。不过多用户笔记只看了 issue 搜索结果 8 页中的第 1 页，所以"没找到"只是很弱的证据。

## 10. 留给 owner 的设计选择

以下只列选项和代价，不替 owner 做决定。"证据倾向"一栏是推断。

**(a) 第一版 PoC 的代理层用什么。** 三份笔记都没有调研其他代理 SDK 或普通模型客户端，所以这里的比较**没有研究支撑**。
- 选项 1：直接用 Copilot SDK。代价：要跟上它的快速变化，固定 SDK 和运行时版本；要设置 `mode`、权限处理器和锁；对一个纯聊天应用来说，这个面向编程代理的引擎只用到很小一部分。好处是会话保存、恢复、压缩都是现成的。
- 选项 2：先用普通模型客户端，以后再换成 SDK。代价：历史、多轮对话要自己存；以后换成 SDK 时要重写代理层；这条路线的具体代价没有调研。
- 证据倾向【推断】：基础笔记认为普通客户端会"更简单"，但这只是一句判断，没有对比数据。

**(b) 运行时怎样托管。** 选项 1：进程内（最简单，没有崩溃隔离）。选项 2：子进程（有隔离，多一个进程要管）。选项 3：独立运行时服务器（可以单独重启，但要自己保护令牌和网络、自己做镜像）。代价详见第 6 节。证据倾向【推断】：在单机、学习用的 PoC 上，选项 1 或 2 的运维负担较小。

**(c) 对话历史放在哪里。** 选项 1：只放在 SDK 的会话文件里。代价：界面读回历史的方法未核实；数据丢失风险取决于磁盘是否持久；大会话可能导致内存暴涨。选项 2：只放在应用自己的数据库里（配合"临时会话"）。代价：要自己存消息和回放；失去压缩和工具状态。选项 3：两边都存。代价：同一份数据存两处，需要保持一致。无论选哪种，归属表都是必需的。

**(d) 流式传输方式和消息格式。** 传输方式：SSE（FastAPI 自带；浏览器端要用 `fetch`）、JSON Lines（最容易调试，没有重连）、WebSocket（双向，对一问一答的聊天来说多余）。消息格式：自定义的简单 JSON（不绑定任何库，但前端解析要自己写），或者 AI SDK UI 消息流（可以直接接 `useChat`，但要完全照抄协议，并跟着它的大版本更新）。

**(e) 前端有多少自己手写。** 选项 1：全部手写，加上 react-markdown。代价：几百行代码，全部要自己理解，但没有格式绑定。选项 2：用 chatscope 这类纯界面组件。代价：流式部分仍要自己写，而且库更新慢。选项 3：用 `useChat` 或 assistant-ui。代价：省下界面和状态代码，但多了一个必须理解的黑盒，也绑定了它的格式。

**(f) 从哪个脚手架起步。** 脚手架（scaffolding）指自动生成的项目骨架。选项 1：create-vite 加手写的 FastAPI 应用。代价：登录和数据库要自己搭。选项 2：官方 full-stack-fastapi-template 删减后使用。代价：要先读懂 SQLModel、JWT 登录、Docker 等一大堆内容，再决定删掉哪些。选项 3：选项 1 为主，只参考模板里的用户模型和令牌检查。代价：要在两份代码之间对照阅读。

## 11. 未能找到或核实的内容（按重要性排序）

1. 引擎（运行时）本身的许可证和使用条款、是否开源、从哪里下载、单独使用是否收费：主代理补查的四个官方页面都没有写明。BYOK 不需要 GitHub 认证是 README 的说法，还没有实际运行验证。
2. Python `get_events()` 的参数和返回格式，以及它是否适合给聊天界面读回历史；`client.py` 只读了约 300,000 / 349,000 个字符。
3. BYOK 的发布状态（公开预览还是正式发布）；PyPI 上 "Alpha" 标记是有意的还是没更新。
4. 运行时默认会不会向 GitHub 或 Microsoft 发送遥测数据（telemetry，自动上报的使用数据），以及怎样关闭。
5. SDK 专属的使用条款；GitHub 的预发布条款在正式发布后是否仍然适用。SUPPORT.md 主代理已补读：支持渠道只有 GitHub issues，没有保修或服务等级的说法。
6. 空闲运行时的内存和启动开销、实测的并发上限、Linux 容器要求（glibc、OpenSSL、基础镜像）。厂商"快 95 倍"的数字只有厂商一方的来源。
7. 没有 GitHub 认证时失去的完整功能清单（仅见摘要）；BYOK 文档 "Limitations" 一节的原文。
8. 共享运行时上，`list_sessions` 和 `delete_session` 会不会做任何按用户的检查（几乎肯定不会，未核实）；"每个会话一个运行时"是否算文档化的模式；会话文件能否加密；有没有现成的数据库版 `sessionFs`。
9. 大部分 issue 只读了标题，issue 搜索只看了第 1 页（共 8 页）；没有找到独立的生产经验报告或第三方多用户报告。
10. 完整的发布列表（v2.0.0 的日期、各个 v1.x 标签），因为 GitHub API 返回 403。
11. FastAPI 0.135.0（SSE）和 0.134.0（JSON Lines）的发布日期；没有在运行中的服务器上实际测试过任何传输格式。
12. 若干组件的许可证：`assistant-stream`、ai-sdk-preview-python-streaming（404）；chatscope、AG-UI 等只看了页面，没有读原始 LICENSE 文件。
13. 多数仓库的提交日期；fetch-event-source 的维护情况；chatscope 是否有对话列表组件（笔记凭记忆写的，未核实）；AI Elements 在 shadcn/ui 里的替代品没有调查。
14. Chainlit 归档的原因；Open WebUI 的 Reddit 和 Hacker News 讨论帖没有打开；"2026 年 v0.9.0 精简了许可证文本"的说法只来自一条搜索摘要，未核实。
15. assistant-ui、CopilotKit、官方模板、chatscope 的 issue 列表都没有读，所以对它们的批评证据很薄；Cloudflare 空闲超时那篇文章（403）没有读到。

## 12. 试跑结果（主代理，2026-11-23）

owner 同意后，主代理在会话的隔离环境里做了一次不需要模型密钥的试跑。完整记录和脚本在[试跑笔记](../research_notes/第一版%20PoC%20技术调研/sdk_trial_run.md)。以下都是【实测】，但只是一台机器上的一次运行，而且用的是本机的“假模型服务”，没有调用真实的模型。

- **不登录 GitHub 可以用。** 试跑进程里没有任何 GitHub 令牌。引擎报告“未认证”，但用自己的服务商配置照样能建会话、收到回答。
- **流式输出和文档说的一致。** 假模型分 10 段回答，后端就收到 10 个 `assistant.message_delta`，然后是完整的 `assistant.message` 和 `session.idle`。
- **读回历史有现成的方法。** `session.get_events()` 返回已保存的事件，其中有用户消息和助手消息的正文。第 4 节和第 11 节第 2 条的“未核实”可以划掉。
- **对话确实存在磁盘上，恢复时会重放。** 文件布局和文档一致。恢复会话后，发给模型服务的请求里带着上一轮的内容。
- **引擎从 Copilot CLI 的发布包下载。** 地址是 `github.com/github/copilot-cli` 的发布页，解压后 196 MB。包里没有引擎本身的许可证文件。
- **引擎会自带一段约 7,000 字符的系统提示词**，开头是“You are GitHub Copilot, an AI coding agent built by GitHub”，内容是写代码的规矩。即使用 `empty` 模式、不给任何工具也会带上。做聊天产品必须替换它。第二次试跑确认 SDK 的 `system_message` 选项可以做到：用 `replace` 模式时，发给模型服务的系统提示词就只有我们自己写的那一段；用 `append` 模式则是在原有那段后面追加。厂商提醒 `replace` 会连同 SDK 自带的防护规则一起去掉，需要的规则要自己写进去。
- **`empty` 模式有两个硬性要求：** 必须明确指定存放目录，每个会话必须明确列出允许的工具。
- **运行期间没有连接任何外部地址。** 这只覆盖约 5 秒的正常运行；引擎的状态里写着错误上报是开启的，出错时会不会回传没有试。
- **内存：** 后端进程启动引擎前 77 MB，启动后 129 MB，开一个会话后 163 MB。

没有试的：真实的模型服务、工具调用、权限请求、长对话压缩、同一会话的并发请求、另外两种托管方式。

