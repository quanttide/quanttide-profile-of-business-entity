这篇也是倒着补的。

我想记的是用 `qtcloud-data` CLI 复现它时，哪些地方最容易从需求变形。这个项目和实体匹配那个不一样，实体匹配主要卡在字段、匹配和性能；这个更像是变量口径管理，尤其是客户数据字典里的定义不能被我自己重新解释。

当时应该记录下来的 CLI 复现链路大概是这个形状：

```powershell
qtcloud-data clarify from-chat .\input\chat.md
qtcloud-data design contract .\.quanttide\data\drd\project.md
qtcloud-data design blueprint .\.quanttide\data\spec\project-contract.yaml
qtcloud-data spec compose project
qtcloud-data spec validate .\.quanttide\data\spec\project-spec.yaml
qtcloud-data implement .\.quanttide\data\spec\project-spec.yaml --lang python -o .\.quanttide\data\pipeline\project.py
```
跟黄健的代码字段一样，
这些命令只是形状，具体文件名可能和实际项目目录不完全一样。真正该记的是：不能因为 CLI 命令能串起来，就觉得复现已经成立。这个项目的复现重点不是"生成一个脚本"，而是生成出来的 spec 和脚本有没有守住变量定义。

我印象最深的是扩散类指标。它看起来只是数某个东西的数量，但其实口径很容易偏。这里的扩散不是样本内用户之间互相关联，而是全平台用户对样本用户新建内容的扩散。也就是说，扩散看的是样本外扩散，如果我按样本内关系理解，变量就完全变味了。活跃扩散也类似。档案里写得很清楚，判定要走某个特定数据通道，而不是用另一个会引入继承关系的通道。这个地方如果按自己习惯偷懒，很容易产生假阳性。它不是实现细节，而是变量口径的一部分。

合并拆分也是。某类合并行为要拆成自合并和外部合并，而且验收时应该能看到恒等式：拆分之和 = 总量。这种恒等式很重要，因为它比"我感觉逻辑对了"更可靠。

窗口边界也不能含糊。时间窗口要明确边界（如左闭右开），按 UTC 日历日算；数据有截止日期，所以窗口还要有右删失标记。这个地方听起来像细节，但如果不写进 contract 或 spec，生成脚本大概率会自己发挥。

我觉得这个项目很适合用来提醒自己：数据字典比我的直觉更重要。客户已经给了变量定义，那就应该让 CLI 围绕它生成契约和蓝图，而不是让模型按"活动面板"这个泛泛题目自由发挥。这里最怕的就是生成出来的字段名看着合理，但和客户真正要的变量不是一回事。

CLI 本身也有几个需要从这个项目里记下来的坑。`design` 和 `implement` 如果长时间没进度，很容易让人以为挂了；blueprint 有时没有复用 contract 里的契约，schema 会变空；spec 包装时还可能丢掉工作流字段；review 如果不带步骤正文，又会提示一些看似严重、实际是假阳性的问题。

所以每次生成之后，我都应该先做这类检查：

```powershell
python -m py_compile .\.quanttide\data\pipeline\project.py
python .\.quanttide\data\pipeline\project.py --help
qtcloud-data spec validate .\.quanttide\data\spec\project-spec.yaml
```

如果要验证数据口径，不能只看有没有导出文件，至少要有几类检查：拆分指标加总是否等于总量；活跃扩散是否小于等于总扩散；一年窗口是否小于等于全生命周期；右删失标记有没有被输出；时区是不是统一按 UTC。



给后面自己的提醒是：这类项目不要先追求代码完整，先追求变量定义不走样。clarify 阶段要把数据字典拆干净，contract 阶段要把窗口、删失、时区、恒等式写硬，blueprint 阶段要防止 schema 空掉，implement 阶段要有小样本和验证报告。只要这些没站稳，脚本跑出来也不能算复现成功。
