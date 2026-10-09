package blueprints

#Contract: {
	schema:  string
	format?: string
	rules?:  [...string]
}

#Step: {
	name!:    string
	command?: string
	desc?:    string
}

#Pipeline: {
	steps!: [...#Step]
}

#Blueprint: {
	name!:        string
	description?: string
	contract: {
		input!:  #Contract
		output!: #Contract & { rules!: [...string] }
	}
	pipeline!: #Pipeline
}

secCredit: #Blueprint & {
	name: "sec-credit"
	description: "SEC 信贷协议识别：从 8-K 附件中分类筛选 Credit Agreement"

	contract: {
		input: {
			schema: "8-K Filing → Exhibit Index → Exhibit metadata + text_head"
			format: "html / xml"
		}
		output: {
			schema: """
				{
				  document_type: "credit_agreement_original" |
				                  "credit_agreement_amendment" |
				                  "credit_agreement_extension" |
				                  "credit_agreement_related_letter" |
				                  "indenture_or_notes" |
				                  "eight_k_summary" |
				                  "other"
				  is_target:    bool
				  confidence:   float
				  positive_evidence: [...string]
				  negative_evidence: [...string]
				}
				"""
			format: "json"
			rules: [
				"eight_k_summary 不进入合同字段抽取",
				"indenture_or_notes 被排除（Issuer/Trustee/The Notes）",
				"输出包含 positive_evidence 和 negative_evidence",
				"Amendment/Extension 不因缺少 Article I/II 被误删",
				"规则与 LLM 冲突的样本被记录",
			]
		}
	}

	pipeline: {
		steps: [
			{ name: "parse-exhibit",  desc: "解析 Exhibit Index / links → metadata + text_head" },
			{ name: "extract-evidence", desc: "抽取 title_evidence / role_evidence / section_topic_evidence" },
			{ name: "llm-classify",   desc: "LLM 判断 document_type + 规则引擎验收" },
			{ name: "review-conflict", desc: "仅冲突样本人工复核" },
		]
	}
}
