// ── 基础类型 ──

#Timestamp: =~"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}[+-]\\d{2}:\\d{2}$"

#Step: {
	name: string
	from: string
	to:   string
	desc: string
	depends?: [...string]
}

#Pipeline: {
	name: string
	steps: [...#Step]
}

#TimelineEntry: {
	action:    "submit" | "confirm" | "reject" | "resubmit"
	actor:     string
	timestamp: #Timestamp
	note?:     string
}

#Status: "draft" | "submitted" | "confirmed" | "rejected"

#SourceTable: {
	table:   string
	format:  string
	content: string
}

#UserFilter: {
	file:   string
	fields: [...string]
	count:  int
}

#ColumnDef: {
	variable:    string
	description: string
}

#PanelSpec: {
	format:        "CSV"
	primary_key:   [...string]
	columns:       [...#ColumnDef]
	strict_columns: true
	column_count:   int
}

#DataSources: {
	mysql_dump: #SourceTable
	id_list:    #UserFilter
	tables: [string]: #SourceTable
}

#CloudServer: {
	instance_type: string
	vcpu:          int
	memory_gb:     int
	data_disk_gb:  int
	region:        string
	provider:      string
}

#ChunkedUpload: {
	chunk_size_gb: int
	method:        string
}

#CloudPlan: {
	server:    #CloudServer
	advantages: [...string]
	upload:    #ChunkedUpload
}

#Deliverable: {
	description: string
	supplement?: string
}

#Blueprint: {
	metadata: {
		responsible: string
		reviewer:    string
		repo:        string
	}
	original_requirements: {
		background: string
		sources:    #DataSources
		output:     #PanelSpec
	}
	pipeline:    #Pipeline
	cloud:       #CloudPlan
	deliverables: {
		data: #Deliverable
		doc:  #Deliverable
	}
	status:     #Status
	timeline?:  [...#TimelineEntry]
	created_at: #Timestamp
	updated_at: #Timestamp
}

// ── 版本输出列定义（已脱敏，实际变量选择属于客户计量建模核心资产）──

// V2: N 列（基础版）
#V2Columns: [
	{variable: "col_01", description: "去标识化的数字标识符"},
	{variable: "col_02", description: "账户标识名"},
	{variable: "col_03", description: "活动观察日期"},
	{variable: "col_04", description: "维度 A 的日计数"},
	{variable: "col_05", description: "维度 B 的日计数"},
	{variable: "col_06", description: "维度 C 的日计数"},
	{variable: "col_07", description: "维度 C 子类型的日计数"},
	{variable: "col_08", description: "维度 D 的日计数"},
	{variable: "col_09", description: "维度 D 活跃子类型的日计数"},
	{variable: "col_10", description: "控制变量（二进制指示器）"},
]

// V3: M 列（基于 V2 迭代，扩充维度细分）
#V3Columns: [
	{variable: "col_01", description: "去标识化的数字标识符"},
	{variable: "col_02", description: "账户标识名"},
	{variable: "col_03", description: "活动观察日期"},
	{variable: "col_04", description: "维度 A 的日计数"},
	{variable: "col_05", description: "维度 B 的日计数"},
	{variable: "col_06", description: "维度 C 的日计数"},
	{variable: "col_07", description: "控制变量（二进制指示器）"},
	{variable: "col_08", description: "维度 D 子口径一的日计数"},
	{variable: "col_09", description: "维度 D 子口径二的日计数"},
	{variable: "col_10", description: "维度 D 活跃子口径一的日计数"},
	{variable: "col_11", description: "维度 D 活跃子口径二的日计数"},
	{variable: "col_12", description: "维度 C 子类型一的日计数"},
	{variable: "col_13", description: "维度 C 子类型二的日计数"},
]

// ── V2 实例（基础版）──

v2: #Blueprint & {
	metadata: {
		responsible: "@负责人"
		reviewer:    ""
		repo:        "{{repo_url}}"
	}

	original_requirements: {
		background: "基于数万级样本，衔接公开数据源，匹配第三方平台信息，最终产出每日活动面板。"

		sources: {
			mysql_dump: {
				table:   "{{mysql_dump}}"
				format:  "数据库转储文件"
				content: "公开数据项目抓取的全量数据"
			}
			id_list: {
				file:   "{{user_list}}"
				fields: ["{{id_field}}"]
				count:  0	// 已脱敏
			}
			tables: {
				"table_users": {
					table:   "{{table_users}}"
					format:  "CSV"
					content: "用户基本信息表"
				}
				"table_entities": {
					table:   "{{table_entities}}"
					format:  "CSV"
					content: "实体信息表"
				}
				"table_events_a": {
					table:   "{{table_events_a}}"
					format:  "CSV"
					content: "事件记录表 A"
				}
				"table_events_b": {
					table:   "{{table_events_b}}"
					format:  "CSV"
					content: "事件记录表 B"
				}
				"table_events_c": {
					table:   "{{table_events_c}}"
					format:  "CSV"
					content: "事件记录表 C"
				}
			}
		}

		output: {
			format:        "CSV"
			primary_key:   ["col_01", "col_03"]
			columns:       #V2Columns
			strict_columns: true
			column_count:   10
		}
	}

	pipeline: {
		name: "数据精炼管道 V2"
		steps: [
			{
				name: "环境搭建与数据下载"
				from: "云服务器实例"
				to:   "{{mysql_dump}}"
				desc: "申请云服务器实例，下载数据 dump。"
			},
			{
				name: "数据解压与提取"
				from: "{{mysql_dump}}"
				to:   "提取的 CSV 表"
				desc: "解压并提取关键表为 CSV。"
				depends: ["环境搭建与数据下载"]
			},
			{
				name: "用户匹配"
				from: "{{user_list}} + 用户表"
				to:   "目标用户 ID 列表"
				desc: "用标识列表匹配用户表，提取目标用户，将全量用户缩减至目标范围。"
				depends: ["数据解压与提取"]
			},
			{
				name: "实体筛选"
				from: "用户 ID 列表 + 实体表"
				to:   "筛选后的实体记录"
				desc: "筛选目标用户相关的实体记录。"
				depends: ["用户匹配"]
			},
			{
				name: "关联筛选"
				from: "筛选后的实体记录 + 实体表"
				to:   "关联记录"
				desc: "筛选源自目标用户实体的关联记录。"
				depends: ["实体筛选"]
			},
			{
				name: "事件筛选 A"
				from: "用户 ID 列表 + 事件表 A"
				to:   "筛选后的事件记录 A"
				desc: "筛选目标用户的事件记录。"
				depends: ["用户匹配"]
			},
			{
				name: "事件筛选 B"
				from: "用户 ID 列表 + 事件表 B"
				to:   "筛选后的事件记录 B"
				desc: "筛选目标用户的事件记录。"
				depends: ["用户匹配"]
			},
			{
				name: "活跃判定"
				from: "关联记录 + 筛选后的事件记录 A"
				to:   "活跃关联记录"
				desc: "筛选满足活跃条件的关联记录，识别实质性关注。"
				depends: ["关联筛选", "事件筛选 A"]
			},
			{
				name: "维度 A 日聚合"
				from: "筛选后的实体记录"
				to:   "维度 A 日计数表"
				desc: "按主键和日期分组聚合。"
				depends: ["实体筛选"]
			},
			{
				name: "维度 D 日聚合"
				from: "关联记录"
				to:   "维度 D 日计数表"
				desc: "按主键和日期分组聚合。"
				depends: ["关联筛选"]
			},
			{
				name: "维度 D 活跃日聚合"
				from: "活跃关联记录"
				to:   "维度 D 活跃日计数表"
				desc: "按主键和日期分组聚合活跃记录。"
				depends: ["活跃判定"]
			},
			{
				name: "维度 C 日聚合"
				from: "筛选后的事件记录 B + 事件表 C"
				to:   "维度 C 日计数表"
				desc: "统计每日事件数及事件结果归因计数。"
				depends: ["事件筛选 B"]
			},
			{
				name: "面板合并"
				from: "各维度日计数表"
				to:   "最终面板数据"
				desc: "合并所有每日指标，生成平衡面板和非平衡面板，添加控制变量。"
				depends: ["维度 A 日聚合", "维度 D 日聚合", "维度 D 活跃日聚合", "维度 C 日聚合"]
			},
			{
				name: "数据验证与交付"
				from: "最终面板数据"
				to:   "CSV 数据文件 + 文档"
				desc: "完整性检查（全覆盖验证）、逻辑抽样核对、分块压缩上传。"
				depends: ["面板合并"]
			},
		]
	}

	cloud: {
		server: {
			instance_type: "{{instance_type}}"
			vcpu:          {{vcpu}}
			memory_gb:     {{memory_gb}}
			data_disk_gb:  {{data_disk_gb}}
			region:        "{{region}}"
			provider:      "{{provider}}"
		}
		advantages: [
			"与数据源地理位置接近，下载速度快",
			"到目标区域的网络连接稳定",
		]
		upload: {
			chunk_size_gb: 5
			method:        "分块压缩后并行上传"
		}
	}

	deliverables: {
		data: {
			description: "CSV 格式面板数据，按主键排序，严格 N 列"
		}
		doc: {
			description: "配套数据处理说明文档"
			supplement:  "记录：日期范围、筛选规则、判定定义、缺失值处理方式"
		}
	}

	status:     "draft"
	created_at: "{{created_at}}"
	updated_at: "{{updated_at}}"
}

// ── V3 实例（基于 V2 迭代）──

v3: #Blueprint & {
	metadata:     v2.metadata
	cloud:        v2.cloud
	deliverables:  v2.deliverables

	pipeline: {
		name: "数据精炼管道 V3"
		steps: [
			v2.pipeline.steps[0],
			v2.pipeline.steps[1],
			v2.pipeline.steps[2],
			v2.pipeline.steps[3],
			v2.pipeline.steps[4],
			v2.pipeline.steps[5],
			v2.pipeline.steps[6],
			v2.pipeline.steps[7],
			v2.pipeline.steps[8],
			{
				name: "维度 D 子口径一 日聚合"
				from: v2.pipeline.steps[9].from
				to:   "维度 D 子口径一日计数表"
				desc: "按子口径一聚合。"
				depends: ["关联筛选"]
			},
			{
				name: "维度 D 子口径二 日聚合"
				from: v2.pipeline.steps[9].from
				to:   "维度 D 子口径二日计数表"
				desc: "按子口径二聚合。"
				depends: ["关联筛选"]
			},
			{
				name: "维度 D 活跃子口径一 日聚合"
				from: v2.pipeline.steps[10].from
				to:   "维度 D 活跃子口径一日计数表"
				desc: "按活跃子口径一聚合。"
				depends: ["活跃判定"]
			},
			{
				name: "维度 D 活跃子口径二 日聚合"
				from: v2.pipeline.steps[10].from
				to:   "维度 D 活跃子口径二日计数表"
				desc: "按活跃子口径二聚合。"
				depends: ["活跃判定"]
			},
			{
				name: "维度 C 子类型拆分聚合"
				from: v2.pipeline.steps[11].from
				to:   "维度 C 子类型日计数表"
				desc: "按子类型拆分聚合。"
				depends: ["事件筛选 B"]
			},
			{
				name: "面板合并"
				from: "各维度日计数表（含子维度）"
				to:   "最终面板数据 V3"
				desc: "合并所有每日指标，生成 V3 面板（M 列）。"
				depends: ["维度 A 日聚合", "维度 D 子口径一 日聚合", "维度 D 子口径二 日聚合", "维度 D 活跃子口径一 日聚合", "维度 D 活跃子口径二 日聚合", "维度 C 子类型拆分聚合"]
			},
			v2.pipeline.steps[13],
		]
	}

	original_requirements: {
		background: v2.original_requirements.background
		sources: {
			mysql_dump: v2.original_requirements.sources.mysql_dump
			tables:    v2.original_requirements.sources.tables
			id_list: {
				file:   "{{user_list_v2}}"
				fields: ["{{id_field}}"]
				count:  0	// 已脱敏
			}
		}
		output: {
			format:        "CSV"
			primary_key:   ["col_01", "col_03"]
			columns:       #V3Columns
			strict_columns: true
			column_count:   13
		}
	}

	status:     "draft"
	created_at: v2.created_at
	updated_at: "{{updated_at_v3}}"
}
