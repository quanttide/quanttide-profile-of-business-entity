这篇算是倒着补的一段记忆。正常应该是 journal 里先有过程，index 和 requirement 再从里面长出来；但是前几天跑的时候没有记日志，所以就靠着仅存的记忆了。

我想记的核心是用 `qtcloud-data` CLI 复现它时暴露出来的东西。流程大概是从客户聊天进来，走 `clarify`，再到 contract、blueprint、spec，最后 `implement` 生成脚本。这个链条看起来很完整，但一接真实数据，就会发现每一步都需要更硬的约束。

当时真正有用的命令大概是这一组：

```powershell
qtcloud-data clarify from-chat .\input\chat.md
qtcloud-data design contract .\.quanttide\data\drd\project.md
qtcloud-data design blueprint .\.quanttide\data\spec\project-contract.yaml
qtcloud-data spec compose project
qtcloud-data spec validate .\.quanttide\data\spec\project-spec.yaml
qtcloud-data implement .\.quanttide\data\spec\project-spec.yaml --lang python -o .\.quanttide\data\pipeline\project.py
```

这些命令本身不复杂，真正麻烦的是每次生成出来的脚本参数可能会变，所以生成后得先看一眼：

```powershell
python -m py_compile .\.quanttide\data\pipeline\project.py
python .\.quanttide\data\pipeline\project.py --help
```

下面有几个我卡住的点：

最容易卡住的是那些看着很小的地方。压缩包里文件叫什么，脚本要求 `--zip-path` 还是位置参数，输出参数叫 `--output-path` 还是 `--output-file`，映射表传的是 `--map-file`、`--mapping-file` 还是 `--mapping-source`。这些东西如果不检查 `--help`，很容易照着上一版命令继续跑，然后报一个很不像业务问题的错。

字段口径也是一个很明显的坑。真实数据里的字段名和生成脚本自己想象的字段名往往不一致，映射表字段名也是。这不是简单改个列名的问题，因为一旦字段口径没写进 spec，下一次重新生成脚本还会漂。

标准化验证也让我印象很深。公开数据里同一个实体名出现很多行是正常的，不能当重复错误。真正需要唯一的是我自己生成的行键，而不是源数据里的某个字段，更不是实体名本身。这个判断如果没有写清楚，脚本就会在很正常的数据结构上把流程拦死。

匹配算法这块更能看出 CLI 产物和真实项目之间的距离。最早生成出来的逻辑太像演示代码，只做等值 merge，结果少得离谱，但它又不一定报错。后面才把要求写硬：不能只做等值合并，要做模糊匹配；不能逐行扫全量候选，要先按标准化名去重；匹配完还要回填到原始行。

性能问题差不多就是这样冒出来的。脚本在小数据上看起来能跑，放大之后就会很慢，甚至像卡住一样。这个经验挺朴素：不要一上来跑全量，要先做 smoke；smoke 也不能只看有没有文件导出，还要看匹配行数、类型分布、AI 审核是不是正常。

AI 审核这块也应该被写进经验里。它不能只是"调用一个 AI"，而是要把 OpenAI-compatible 的接口形式写清楚：base url、model、api key、`/chat/completions`，还要有 `--skip-ai` 和 `--ai-review-limit`。不然真实跑的时候，要么接口不通，要么一下子审太多，要么 key 和环境变量的问题把流程卡住。

给后面自己的经验是：不要只相信生成出来的脚本，也不要只相信流程图。先把 spec 写硬，生成后先看 `--help` 和关键函数，再用小样本跑通，问题全部记到一个 bug log 里。等这些都稳定了，再谈全量和交付。这个顺序比"我把 CLI 命令都敲了一遍"更重要。
