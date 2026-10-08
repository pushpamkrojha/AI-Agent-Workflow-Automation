import argparse, json, os
from dotenv import load_dotenv
from agent.registry import WorkflowRegistry
from agent.router import WorkflowRouter
from agent.executor import WorkflowExecutor

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))

EXAMPLES = {
    "WF001": ("Which products need restocking?", {"minimum_stock": 10}),
    "WF002": ("Find products where vendor price differs by more than 10%.", {}),
    "WF003": ("Process this vendor spreadsheet and show invalid rows.", {"file_path": os.path.join(BASE,"data","vendor_input.csv")}),
    "WF004": ("Generate SEO content for this product.", {"product_name":"Trail Runner Shoes", "category":"Footwear", "attributes":"Lightweight, running", "material":None, "color":"Black", "target_audience":"Runners"}),
    "WF005": ("Where is order ORD-1001?", {"order_id":"ORD-1001"}),
    "WF006": ("Find likely duplicate products in the catalog.", {}),
    "WF007": ("Create a campaign brief for the new collection.", {"goal":"Launch the new summer collection", "products":["Trail Runner Shoes","Urban Backpack"],"audience":"Young professionals", "promotion":"10% launch discount", "dates":"2026-10-15 to 2026-10-31"}),
    "WF008": ("Classify these keywords and map them to pages.", {}),
    "WF009": ("Assign this urgent task to the best available developer.", {"task":"Build a Python REST API", "required_skills":["Python","FastAPI"],"priority":"Urgent","deadline":"2026-10-15"}),
    "WF010": ("Which workflows are failing most often?", {}),
}

def pretty(result, reason=None, router_mode=None):
    print("\n" + "="*72)
    print("AI AGENT WORKFLOW AUTOMATION")
    print("="*72)
    print(f"Selected Workflow : {result.workflow_id} - {result.workflow_name}")
    if reason: print(f"Selection Reason  : {reason}")
    if router_mode: print(f"Router Mode       : {router_mode}")
    print("\nSteps Executed:")
    for i, s in enumerate(result.steps, 1):
        print(f"  {i}. {s['step']} -> {s['status']}")
    print("\nFinal Result:")
    print(json.dumps(result.result, indent=2, default=str) if result.result is not None else result.error)
    print(f"\nStatus: {result.status}")
    print("="*72)

def main():
    parser=argparse.ArgumentParser(description="Reusable Excel-driven AI workflow agent")
    parser.add_argument("--request", help="User request")
    parser.add_argument("--workflow", help="Run a specific workflow for testing, e.g. WF001")
    parser.add_argument("--file", help="Input CSV/XLSX for WF003")
    parser.add_argument("--minimum-stock", type=float, default=10)
    args=parser.parse_args()

    registry=WorkflowRegistry(os.path.join(BASE,"AI_Agent_Workflow_Assessment.xlsx"))
    router=WorkflowRouter(registry.all())
    executor=WorkflowExecutor(registry)

    if args.workflow:
        if args.workflow not in EXAMPLES: raise SystemExit("Unknown workflow ID")
        request, context = EXAMPLES[args.workflow]
        if args.file: context["file_path"]=args.file
        if args.workflow=="WF001": context["minimum_stock"]=args.minimum_stock
        result=executor.execute(args.workflow, request, context)
        pretty(result, "Manual workflow test", "Direct")
        return

    request=args.request or input("Enter your business request: ").strip()
    workflow_id, reason, mode=router.route(request)
    context={}
    if workflow_id=="WF001": context["minimum_stock"]=args.minimum_stock
    if workflow_id=="WF003": context["file_path"]=args.file or os.path.join(BASE,"data","vendor_input.csv")
    result=executor.execute(workflow_id, request, context)
    pretty(result, reason, mode)

if __name__ == "__main__": main()
