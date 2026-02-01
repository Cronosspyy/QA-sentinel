from qa_engine.process_rules import run_process_rules
from qa_engine.compliance_rules import run_compliance_rules
from qa_engine.quality_rules import run_quality_rules
from qa_engine.sop_rules import run_sop_rules

def run_rule_engine(structured_call: dict):
    """
    Master rule engine.
    Input: structured_call
    Output: rule evaluation results
    """

    result = {
        "call_id": structured_call.get("call_id"),
        "process_rules": {},
        "compliance": {},
        "quality_signals": {},
        "sop_alignment": {}
    }

    # 1. Compliance (short-circuit)
    compliance_result = run_compliance_rules(structured_call)
    result["compliance"] = compliance_result

    if compliance_result["critical_fail"]:
        result["terminated_early"] = True
        return result

    # 2. Process rules
    result["process_rules"] = run_process_rules(structured_call)

    # 3. Quality signals
    result["quality_signals"] = run_quality_rules(structured_call)

    # 4. SOP alignment
    result["sop_alignment"] = run_sop_rules(structured_call)

    return result
