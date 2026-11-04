# 跨系统时间对齐

## 离线材料

为每个锚点记录原文件/行号、系统、boot、Guest实例、时钟类型、原始时间、共同事务内容及关联强度。

同一启动且连续时钟段内，以共同事件 A 建立偏移，再用事件 B 检验：

```text
offset_A = Host_A - Guest_A
Host_target ≈ Guest_target + offset_A
```

这里 Host 和 Guest 必须明确是墙钟、MONOTONIC、BOOTTIME 还是 printk 时间；不能直接混用单位及停表行为。消息接收有缓冲与调度延迟；仅凭相同进程 PID 的相邻打印，不应声称毫秒级精度。

对齐只连接已验证的两种记录。Guest UART 与 Android 显示墙钟连通后，仍需 Host 共同锚点。不要用“导出日期正常”“两边都16点”“文件编号相邻”代替关联。经过 suspend/resume、墙钟跳变、Host或Guest重新启动后重新分段。

偏移只知范围 `[Δmin, Δmax]` 时，Guest 候选窗口 `[A, B]` 对应 Host 候选窗口 `[A+Δmin, B+Δmax]`。没有偏移时，输出各自原始时间范围与待补锚点；不能编造唯一 Host 绝对时间。

## 下一次复现的采集设计

以下是补采方案，不属于默认离线分析操作。先核实当前平台配置、权限及现有采集链路。

EHV 历史 qcrosvm 配置曾见 `--console=/tmp/la_gvm_skt,label=41`。仅在本次服务配置确认后，才使用该入口。在现有 Guest console 采集器每行接收时附：

`Host boot_id | REALTIME_ns | MONOTONIC_ns | BOOTTIME_ns | 原始 Guest console 行`

保留 Guest 原始 `[seconds]` 与启动边界。接收时间是上界线索，包含传输/缓冲延迟。不要新开一个竞争读取相同 socket 的消费者。

可在获准的测试采集中，用现有 Guest 控制通道同步写唯一 `CLK_SYNC` 标记到 `/dev/kmsg`：Host 发送前记 H0，确认 Guest 写入完成的同步响应后记 H1，标记 printk 时间记 G0。处于同一连续时钟段且时钟速率可比较时：

```text
Host-Guest 偏移 ∈ [H0-G0, H1-G0]
Guest目标Gp 对应Host区间 ∈ [Gp+H0-G0, Gp+H1-G0]
```

控制台收到标记的 Hr 可能比 H1 晚。重复取短往返有效样本，检查区间相容性；休眠前后及重启后重新采样。当前启动采到的偏移不能反套历史故障。
