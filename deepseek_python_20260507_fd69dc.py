"""
智能金融合规审查系统 - 多Agent协作原型
使用方法：将本文件保存为 compliance_agent.py，然后执行 python compliance_agent.py
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Tuple

# -------------------- 模拟外部服务 --------------------
class MockLLM:
    """模拟大模型接口"""
    @staticmethod
    def generate(prompt: str) -> str:
        return f"[LLM推理] 基于输入：{prompt[:50]}... 进行7步推导：\n" \
               "步骤1: 检查交易对手所在地 -> 高风险国家\n" \
               "步骤2: 分析交易金额模式 -> 偏离历史均值3倍\n" \
               "步骤3: 资金快速分散转出 -> 存在结构化迹象\n" \
               "步骤4: 调取客户负面新闻 -> 匹配到1条关联报道\n" \
               "步骤5: 构建关联网络 -> 与已知风险账户有2度间接连接\n" \
               "步骤6: 综合评分 -> 风险分数 0.87\n" \
               "步骤7: 结论 -> 高度可疑，建议上报"

class MockVectorDB:
    """模拟向量数据库 + 案例检索"""
    def __init__(self):
        self.cases = [
            {"id": "C001", "desc": "空壳公司洗钱案", "pattern": "高频小额转入，大额集中转出，公司注册地异常", "result": "已移交执法机关", "score": 0.92},
            {"id": "C002", "desc": "虚假贸易融资", "pattern": "关联企业间循环交易，无实际货权转移", "result": "行政处罚", "score": 0.88},
            {"id": "C003", "desc": "地下钱庄兑换", "pattern": "对侧交易，跨币种快速兑换", "result": "冻结账户", "score": 0.95},
        ]

    def search(self, query: str, top_k: int = 2) -> List[Dict]:
        matches = random.sample(self.cases, min(top_k, len(self.cases)))
        for c in matches:
            c["similarity"] = round(random.uniform(0.75, 0.98), 2)
        return matches

class MockOCRParser:
    """模拟多模态票据解析"""
    @staticmethod
    def analyze(image_path: str) -> Dict:
        return {
            "invoice_amount": 125000.00,
            "supplier_name": "XYZ贸易有限公司",
            "material_match": "合同标的物不一致（发票显示电子产品，合同为农产品）",
            "seal_authenticity": 0.65,
            "conclusion": "票据异常，疑似伪造"
        }

# -------------------- Agent 定义 --------------------
class RuleFilterAgent:
    def __init__(self, rules: List[callable]):
        self.rules = rules

    def filter(self, transaction: Dict) -> Tuple[bool, str]:
        for rule in self.rules:
            passed, reason = rule(transaction)
            if not passed:
                return False, reason
        return True, "所有规则通过"

class DeepReasoningAgent:
    def __init__(self, llm: MockLLM):
        self.llm = llm

    def reason(self, transaction: Dict) -> Dict:
        context = f"交易详情: {json.dumps(transaction, ensure_ascii=False)}"
        reasoning_output = self.llm.generate(context)
        return {
            "reasoning_trace": reasoning_output,
            "risk_score": 0.87,
            "conclusion": "高度可疑，建议上报"
        }

class CaseRetrievalRAGAgent:
    def __init__(self, vector_db: MockVectorDB):
        self.db = vector_db

    def retrieve(self, transaction: Dict) -> List[Dict]:
        query = f"{transaction['type']} {transaction['amount']} {transaction['counterparty']}"
        return self.db.search(query)

class MultimodalAnalyzerAgent:
    def __init__(self, ocr_parser: MockOCRParser):
        self.parser = ocr_parser

    def analyze(self, doc_paths: List[str]) -> List[Dict]:
        return [self.parser.analyze(path) for path in doc_paths]

class ReviewAgent:
    def synthesize(self, transaction: Dict, rule_result: Tuple, reason_result: Dict,
                   cases: List[Dict], multimodal_results: List[Dict]) -> Dict:
        passed, rule_reason = rule_result
        final_score = reason_result["risk_score"]
        case_support = len(cases) > 0 and any(c["similarity"] > 0.8 for c in cases)
        doc_anomalies = [r["conclusion"] for r in multimodal_results if "异常" in r["conclusion"]]

        if not passed:
            decision = "自动放行（规则过滤不通过）"
        elif final_score >= 0.85 and (case_support or doc_anomalies):
            decision = "确认上报反洗钱中心"
        elif final_score >= 0.7:
            decision = "加入人工复审队列"
        else:
            decision = "暂不处理"

        return {
            "timestamp": datetime.now().isoformat(),
            "transaction_id": transaction["id"],
            "rule_check": rule_reason,
            "deep_reasoning_summary": reason_result["conclusion"],
            "reasoning_trace": reason_result["reasoning_trace"],
            "risk_score": final_score,
            "matched_cases": cases,
            "document_analysis": multimodal_results,
            "final_decision": decision,
            "suggestion": "需补充客户尽职调查材料" if decision != "自动放行" else "无"
        }

# -------------------- 主流程 --------------------
def main():
    rules = [
        lambda tx: (tx["amount"] <= 500000, "单笔金额超限"),
        lambda tx: (tx["country"] not in ["北朝鲜", "伊朗"], "高风险国家/地区"),
        lambda tx: (tx["customer_type"] != "PEP" or tx["amount"] < 100000, "PEP客户大额交易"),
    ]

    rule_agent = RuleFilterAgent(rules)
    reason_agent = DeepReasoningAgent(MockLLM())
    case_agent = CaseRetrievalRAGAgent(MockVectorDB())
    multimodal_agent = MultimodalAnalyzerAgent(MockOCRParser())
    review_agent = ReviewAgent()

    # 测试交易数据
    transaction = {
        "id": "TXN202605071234",
        "time": "2026-05-07 15:20:00",
        "customer_id": "CUST-88992",
        "amount": 320000,
        "country": "叙利亚",
        "counterparty": "East-West Trading Co.",
        "type": "跨境电汇",
        "customer_type": "普通企业",
        "documents": ["invoice_001.png", "contract_002.pdf"]
    }

    print("="*60)
    print("智能合规审查系统 - 处理启动")
    print("="*60)

    filter_result = rule_agent.filter(transaction)
    print(f"[规则过滤] {'通过' if filter_result[0] else '拦截'}：{filter_result[1]}")

    print("\n[深度推理Agent] 启动多步长链推理...")
    reasoning_result = reason_agent.reason(transaction)
    print(f"[推理结论] {reasoning_result['conclusion']} (风险分数: {reasoning_result['risk_score']})")
    print(f"推理链展示:\n{reasoning_result['reasoning_trace']}")

    print("\n[案例检索RAG Agent] 搜索相似历史案例...")
    matched_cases = case_agent.retrieve(transaction)
    for idx, case in enumerate(matched_cases, 1):
        print(f"  案例{idx}: {case['desc']} (相似度 {case['similarity']})")

    print("\n[多模态Agent] 分析附带单据...")
    doc_analysis = multimodal_agent.analyze(transaction["documents"])
    for doc, res in zip(transaction["documents"], doc_analysis):
        print(f"  文件 {doc}: {res['conclusion']} (印章真实性: {res['seal_authenticity']})")

    # 修正：将 transaction 传入 synthesize
    final_report = review_agent.synthesize(
        transaction, filter_result, reasoning_result, matched_cases, doc_analysis
    )

    print("\n" + "="*60)
    print("最终审查报告（结构化输出）")
    print("="*60)
    print(json.dumps(final_report, indent=2, ensure_ascii=False))
    print("\n系统统计: 本次消耗Token约 12,500 (模拟)")

if __name__ == "__main__":
    main()