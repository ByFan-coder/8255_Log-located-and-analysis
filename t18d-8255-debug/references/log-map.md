# 日志目录与格式

默认分析根目录是当前目录，以下均为相对入口或文件名模式，不依赖历史工程位置。以本次枚举为准；同一个包可能重复嵌套 `logs_时间/logs_时间/`。优先检查 `qnxlog` 的 slog2 和 systeminfo，再用 QNXRunInfo 补充驱动信息。

**先核对时间和覆盖，再检索故障原因。**清点时对每个日志源记录实际时间段、boot/校时边界、分片连续性、文件内部疑似缺口、截断/解码状态，判断故障前、中、后是否覆盖。文件名、导出时间、仅有首末时间均不足以证明全程覆盖；快照需记录采样点。关键词示例仅在完成时间与覆盖检查后用于问题定位。

| 日志域 | 候选入口/文件 | 优先用途 |
|---|---|---|
| **首查：QNX 系统与服务** | **`qnxlog/` 中的 `slog2`、`slog2*`**，其他子目录的同类文件、编号文件、解码后的 slog | 按 bug 优先查 kgsl、smmu、openwfd、display、i2c、disp_svc、ads_service，再关联应用、VIDC、电源等 |
| **首查：QNX 系统快照** | **`qnxlog/` 中的 `systeminfo`、`systeminfo*`**，其他子目录的同类文件 | 与 slog2 联查全量 pid-tid、线程状态、CPU、/mm_dma、进程内存统计、服务存活 |
| QNX 驱动与运行信息包 | **`QNXRunInfo.tar.gz`**，可能位于当前目录的子目录 | 先列成员，按故障选择其中驱动相关信息、运行快照或配置；记录采集时间与 boot，不能把故障后快照当故障瞬间状态 |
| 屏端日志（先询问） | **`display_log/`** 或同名文件/压缩包 | 可能涉及屏端时先询问是否需要解析；用户同意后识别格式和屏型，结合主机时序验证。不能仅凭文件名假定明文或通用协议 |
| QNX 封装日志 | `qnx_tracking/*.txt.gz` 等 | 必须检查文件头；历史案例实际为 DSV_PKMS，不能因后缀当 gzip |
| Android 用户态 | `logcat/`、`android/logcat/`、嵌套 `logs_*/logs_*/logcat/`；`*.txt.gz`、`*_last_shutdown_*` | InputReader/InputDispatcher、ActivityManager、WindowManager、SurfaceFlinger、应用与图形库 |
| Android 内核 | `kernel/`、`android/kernel/`、`dmesg*`、`la_gvm*` | HGSL/HAB、hung task、workqueue、watchdog、panic 与提交超时 |
| Android 崩溃和 ANR | `anr/`、`android/anr/`、`tombstones/`、`tombstone_*` | Java/native 栈、主线程/RenderThread、abort、信号及内核等待点 |
| 历史内核现场 | `sys_fs_pstore_console-pstore_blk-0`、pstore/ramoops 类文件 | 前一启动现场；与当前启动和日志墙钟分开关联 |
| Linux PVM（适用构建） | **`linuxlog/soclog/svplog.*`**；另见 `linux/soclog/` | Host kernel 与 userspace 合并记录，GSL/KGSL、openwfd、disp_svc、qcrosvm、Gunyah、电源 |
| Linux Host 诊断包 | `linux/soclog/diag/*.tgz`、`qcrosvm_fail_*.tgz` | journal、服务配置、失败快照；检查是否为故障后重新启动现场 |
| QNX core/匹配符号 | `*.core.gz`、工程提供的可执行文件/库/符号 | 确认最终退出调用链，不能用另一个构建替代 |

## Windows 查找示例

以下从当前目录列举与粗筛，不自动解压二进制封装，也不读取 display_log 内容。

```powershell
$caseRoot = (Get-Location).Path
rg --files --hidden "$caseRoot" | rg -i '(qnxlog|slog2|systeminfo|QNXRunInfo\.tar\.gz|display_log|logcat|kernel|anr|tombstone|svplog|pstore|la_gvm|core|diag)'
# 无扩展名的编号文件也需要检查：
rg --files --hidden "$caseRoot" | rg '[/\\][0-9]+_'
# 已确认是文本的文件，命中后再读上下文：
rg -n -i -C 5 'kgsl|smmu|openwfd|display|i2c|disp_svc|ads_service' '本次已解码的slog2文件'
# 按当前发现的真实路径列出 QNX 运行信息包：
tar -tf './QNXRunInfo.tar.gz'
```

`rg` 默认不搜索 gzip 内容。先解压到独立目录或用 gzip 流式读取；搜索失败不能直接当作无命中。未知二进制不要默认 `rg -a` 当文本读完。

## 对外引用必须使用编辑器行号

搜索结果只用于找内容，不能直接将 `rg -n`、其他搜索器或旧摘录前缀的数字作为最终行号。混用 CRLF、LF、CR 时，它们的计行方式可能不同。

默认计数规则是：CRLF 只算一次换行，独立 LF、独立 CR 各算一次；从1开始，空行保留。只按文件物理行计数，编辑器自动折行不增加行号。不要用 Python `str.splitlines()` 代替该规则，它还识别其他 Unicode 分隔符；不要在未确认编码时按原始字节中的 `0a` 计数。

按当前编码解码原始文件，用搜索命中的原文片段（最好包含时间、PID/TID和唯一载荷）在编辑器计行模式下重新定位。随包的只读工具使用 Python 通用换行读取，流式处理 CRLF/LF/CR，并可自动识别普通 gzip：

```powershell
# 替换脚本位置为实际技能目录；文本文件默认 UTF-8，可显式指定编码。
python '技能目录/scripts/editor_line_locator.py' './qnxlog/slog2_1.log' --text '本次命中的唯一日志片段'
python '技能目录/scripts/editor_line_locator.py' './qnxlog/slog2_1.log' --line 12345
python '技能目录/scripts/editor_line_locator.py' './qnxlog/slog2_1.log' --text '唯一片段' --encoding gb18030
```

工具输出 `editor_line` 和对应原文。先按原文取得候选编辑器行号，再按 `--line` 读取目标和邻近几行，核实时间、进程和完整事件后写入链接。重复片段必须用更完整的内容区分，不能默认取第一条。截图行段的首尾也按同一规则复核。

工具不会修改原始文件，也不解析 DSV_PKMS。gzip输出的是解压后文本的编辑器行号；解码日志应链接实际解码文件并记录来源。解码失败先确认编码或工具，不用忽略错误的方式伪造文本。若编辑器实际规则不同，按用户使用的编辑器重新定位；无法核对时同时给原文、时间及计行规则，不能宣称行号已与编辑器一致。

## 文件头与解包处理

- gzip 头为十六进制 `1f 8b`；ZIP 常见为 `50 4b`；DSV_PKMS 为可见封装标记。需要检查实际字节，不能只依赖后缀。
- `tar -tf` 可先列 `.tgz/.tar` 成员。解包前确认成员没有绝对路径、盘符或 `..` 越界；仅提取到本次工作目录，避免覆盖原始证据。
- `.qmdl`、原始 journal、二进制 slog、core 需对应工具，不能把 strings 输出当完整日志。
- `Truncated tar archive` 意味部分提取。记录成功成员和失败边界；未提取部分的模块不能被排除。
- 对原文件解压时保留原始文本、换行与行序；不要排序、去重、删空行或改写换行后再把派生文件行号当作原文件行号。记录解码工具、参数及失败信息。需统一换行时仅生成独立副本，并说明链接指向哪个版本；原文件引用仍重新按编辑器规则定位。
