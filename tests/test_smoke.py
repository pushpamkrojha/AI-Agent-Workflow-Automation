import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["MOCK_MODE"] = "true"
from agent.registry import WorkflowRegistry
from agent.executor import WorkflowExecutor

BASE=os.path.dirname(os.path.dirname(__file__))
reg=WorkflowRegistry(os.path.join(BASE,"AI_Agent_Workflow_Assessment.xlsx"))
exe=WorkflowExecutor(reg)

def test_registry_has_all_workflows():
    assert len(reg.all()) == 10

def test_inventory():
    r=exe.execute("WF001","Which products need restocking?",{"minimum_stock":10})
    assert r.status=="SUCCESS"
    assert len(r.result["products"])==2

def test_order():
    r=exe.execute("WF005","Where is order ORD-1001?",{"order_id":"ORD-1001"})
    assert r.result["status"]=="Shipped"
