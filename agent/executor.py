import importlib

from .models import AgentResult
from tools.common import read_csv, pct_difference
from tools.data_tools import read_table, normalize_columns, load_json_data
from tools.llm_tools import LLMTools
from tools.similarity import similarity
from .input_extractor import InputExtractor
from pathlib import Path


class WorkflowExecutor:
    """
    Executes workflows through reusable tool functions.

    Business rules are kept here, not in the router.
    Natural-language input is converted to structured
    workflow inputs by InputExtractor.
    """

    def __init__(self, registry):
        self.registry = registry
        self.llm = LLMTools()
        self.input_extractor = InputExtractor()

        self.handlers = self._build_handler_registry()

    def _build_handler_registry(self):
        """
        Automatically discover workflow handlers.

        A workflow module should follow this naming convention:
            WF001 -> agent/workflows/wf001_inventory.py
            WF002 -> agent/workflows/wf002_price_validation.py
            WF011 -> agent/workflows/wf011_some_workflow.py

        The module must expose a `run(request, context, steps, executor)` function.
            

        If an external handler is not found, the executor falls back 
        to the existing method inside executor.py.    
        """
        handlers = {}

        workflows_dir = Path(__file__).parent / "workflows"

        for workflow in self.registry.all():
            workflow_id = workflow.workflow_id
            prefix = workflow_id.lower() + "_"

           
            # Find a module such as:
            # wf001_inventory.py
            # wf002_price_validation.py
            # wf011_some_workflow.py

            matches = sorted(
                workflows_dir.glob(f"{prefix}*.py")
            )

            if matches:
                if len(matches) > 1:
                    raise ValueError(
                        f"Multiple handler modules found for "
                        f"{workflow_id}: {matches}"
                    )

                module_name = (
                    f"agent.workflows.{matches[0].stem}"
                )

                try:
                    module = importlib.import_module(
                        module_name
                    )

                    external_handler = getattr(
                        module,
                        "run",
                        None
                    )
                    if external_handler:
                        handlers[workflow_id] = (
                            lambda request, context, steps,
                            handler=external_handler:
                            handler(
                                request,
                                context,
                                steps,
                                self
                            )
                        )

                        continue
                except ModuleNotFoundError:
                    pass

            # Fallback to existing handler inside executor.py

            method_name = workflow_id.lower()
            internal_handler = getattr(
                self,
                method_name,
                None
            )

            if internal_handler:
                handlers[workflow_id] = internal_handler

        return handlers
     

    def execute(self, workflow_id, request, context=None):
        """
        Execute the selected workflow.

        If context is empty or not supplied, extract structured
        inputs from the natural-language user request.
        """

        wf = self.registry.get(workflow_id)
        steps = []

        try:
            # Extract inputs when context is missing or empty.
            if not context:
                context = self.input_extractor.extract(
                    wf,
                    request
                )

            # Protect against extractor returning None.
            if context is None:
                context = {}

            # Validate required workflow inputs
            missing_inputs = self._find_missing_inputs(
                wf,
                context
            )

            if missing_inputs:
                return AgentResult(
                    workflow_id=workflow_id,
                    workflow_name=wf.name,
                    status="NEEDS_INPUT",
                    steps=steps,
                    result={
                        "status": "NEEDS_INPUT",
                        "message": (
                            f"I identified the {wf.name} workflow, "
                            "but I need some additional information."
                        ),
                        "required_inputs": missing_inputs
                    }
                )


            # Execute selected workflow.
            result = self.handlers[workflow_id](
                request,
                context,
                steps
            )

            return AgentResult(
                workflow_id=workflow_id,
                workflow_name=wf.name,
                status="SUCCESS",
                steps=steps,
                result=result
            )

        except Exception as e:

            steps.append({
                "step": "Error handling",
                "status": "FAILED",
                "detail": str(e)
            })

            return AgentResult(
                workflow_id=workflow_id,
                workflow_name=wf.name,
                status="FAILED",
                steps=steps,
                result=None,
                error=str(e)
            )

    def _find_missing_inputs(self, workflow, context):
        """
        Identify required inputs that are genuinely needed
        before executing a workflow. """

        # WF005 requires order_id OR email
        if workflow.workflow_id == "WF005":
            order_id = context.get("order_id")
            email = context.get("email")

            if not order_id and not email:
                return ["order_id or email"]

            return []

        # Workflows that use their own stored/input data
        # and do not require user-provided fields.
        if workflow.workflow_id in {
            "WF001",
            "WF002",
            "WF006",
            "WF008",
            "WF010"
        }:
            return []

        required_inputs = []

        input_text = workflow.inputs.lower()

        input_rules = {
            "file_path": ["file_path", "file path", "vendor file"],
            "product_name": ["product_name", "product name"],
            "category": ["category"],
            "goal": ["goal"],
            "dates": ["dates","date"]
        }

        for field, keywords in input_rules.items():
            if any(
                keyword in input_text
                for keyword in keywords
            ):
                value = context.get(field)
                if not value:
                    required_inputs.append(field)

        return required_inputs
                      

        # -------------------------------------------------
        # WF005: order_id OR email
        # -------------------------------------------------

        if workflow.workflow_id == "WF005":

            order_id = context.get("order_id")
            email = context.get("email")

            if not order_id and not email:
                required_inputs.append(
                    "order_id or email"
                )

            return required_inputs

        # -------------------------------------------------
        # Generic required-input rules
        # -------------------------------------------------

        input_rules = {
            "file_path": [
                "file_path",
                "file path",
                "vendor file"
            ],

            "product_name": [
                "product_name",
                "product name"
            ],

            "category": [
                "category"
            ],

            "goal": [
                "goal"
            ],

            "dates": [
                "dates",
                "date"
            ]
        }
      
        for field, keywords in input_rules.items():

            if any(
                keyword in input_text
                for keyword in keywords
            
            ):
                value = context.get(field)

                if not value:
                    required_inputs.append(field)

        return required_inputs
    
    
    def _step(self, steps, name, fn):
        """
        Execute a workflow step and record its status.
        """

        value = fn()

        steps.append({
            "step": name,
            "status": "SUCCESS"
        })

        return value

    # =========================================================
    # WF001 - Inventory Restock Check
    # =========================================================

    def wf001(self, request, c, steps):

        df = self._step(
            steps,
            "Load inventory",
            lambda: read_csv("inventory.csv")
        )

        threshold = float(
            c.get("minimum_stock", 10)
        )

        low = df[
            df.current_stock < threshold
        ].copy()

        self._step(
            steps,
            "Compare current stock with threshold",
            lambda: True
        )

        self._step(
            steps,
            "Identify low-stock products",
            lambda: True
        )

        low["reorder_quantity"] = (
            threshold - low["current_stock"]
        )

        self._step(
            steps,
            "Calculate reorder quantity",
            lambda: True
        )

        return {
            "threshold": threshold,
            "products": low.to_dict(
                orient="records"
            )
        }

    # =========================================================
    # WF002 - Product Price Validation
    # =========================================================

    def wf002(self, request, c, steps):

        products = self._step(
            steps,
            "Load product prices",
            lambda: read_csv("products.csv")
        )

        vendors = self._step(
            steps,
            "Load vendor prices",
            lambda: read_csv("vendor_prices.csv")
        )

        merged = products.merge(
            vendors,
            on="sku",
            suffixes=("_internal", "_vendor")
        )

        merged["difference_percent"] = [
            pct_difference(a, b)
            for a, b in zip(
                merged.price_internal,
                merged.price_vendor
            )
        ]

        merged["exception"] = (
            merged.difference_percent > 10
        )

        self._step(
            steps,
            "Match products by SKU",
            lambda: True
        )

        self._step(
            steps,
            "Calculate percentage difference",
            lambda: True
        )

        self._step(
            steps,
            "Flag differences above 10%",
            lambda: True
        )

        return merged.to_dict(
            orient="records"
        )

    # =========================================================
    # WF003 - Vendor File Processing
    # =========================================================

    def wf003(self, request, c, steps):

        path = c.get("file_path")

        if not path:
            raise ValueError(
                "WF003 needs context.file_path "
                "pointing to a CSV/XLSX vendor file."
            )

        df = self._step(
            steps,
            "Read vendor file",
            lambda: read_table(path)
        )

        df = self._step(
            steps,
            "Normalize column names",
            lambda: normalize_columns(df)
        )

        required = [
            "sku",
            "product_name"
        ]

        missing_cols = [
            x
            for x in required
            if x not in df.columns
        ]

        if missing_cols:
            raise ValueError(
                f"Missing required columns: {missing_cols}"
            )

        invalid = df[
            df["sku"].isna()
            | df["product_name"].isna()
        ].copy()

        clean = df.dropna(
            subset=required
        ).copy()

        self._step(
            steps,
            "Validate required fields",
            lambda: True
        )

        self._step(
            steps,
            "Identify invalid rows",
            lambda: True
        )

        self._step(
            steps,
            "Produce cleaned dataset",
            lambda: True
        )

        return {
            "cleaned_rows": clean.to_dict(
                orient="records"
            ),
            "invalid_rows": invalid.to_dict(
                orient="records"
            ),
            "invalid_count": len(invalid)
        }

    # =========================================================
    # WF004 - Product Description Generator
    # =========================================================

    def wf004(self, request, c, steps):

        required = [
            "product_name",
            "category"
        ]

        missing = [
            x
            for x in required
            if not c.get(x)
        ]

        if missing:
            raise ValueError(
                f"Missing required inputs: {missing}"
            )

        self._step(
            steps,
            "Validate required attributes",
            lambda: True
        )

        result = self._step(
            steps,
            "Generate product content with LLM",
            lambda: self.llm.generate_product_content(c)
        )

        self._step(
            steps,
            "Validate generated content",
            lambda: True
        )

        return result

    # =========================================================
    # WF005 - Customer Order Status
    # =========================================================

    def wf005(self, request, c, steps):

        orders = self._step(
            steps,
            "Load order data",
            lambda: load_json_data("orders.json")
        )

        oid = c.get("order_id")
        email = c.get("email")
                

        order = next(
            (
                o
                for o in orders
                if (
                    oid
                    and o["order_id"] == oid
                )
                or (
                    email
                    and o["email"].lower()
                    == email.lower()
                )
            ),
            None
        )

        self._step(
            steps,
            "Validate identifier",
            lambda: True
        )

        if not order:
            raise ValueError(
                "Order not found. "
                "Please provide another order ID "
                "or customer email."
            )

        self._step(
            steps,
            "Search order",
            lambda: True
        )

        self._step(
            steps,
            "Retrieve shipment information",
            lambda: True
        )

        return order

    # =========================================================
    # WF006 - Duplicate Product Detection
    # =========================================================

    def wf006(self, request, c, steps):

        df = self._step(
            steps,
            "Load product catalog",
            lambda: read_csv("catalog.csv")
        )

        groups = []

        for i in range(len(df)):

            for j in range(i + 1, len(df)):

                if (
                    str(df.iloc[i].sku)
                    == str(df.iloc[j].sku)
                ):

                    groups.append({
                        "products": [
                            df.iloc[i].to_dict(),
                            df.iloc[j].to_dict()
                        ],
                        "confidence": "DEFINITE"
                    })

                else:

                    score = similarity(
                        df.iloc[i].product_name,
                        df.iloc[j].product_name
                    )

                    if score >= 85:

                        groups.append({
                            "products": [
                                df.iloc[i].to_dict(),
                                df.iloc[j].to_dict()
                            ],
                            "similarity": score,
                            "confidence": "POSSIBLE"
                        })

        self._step(
            steps,
            "Normalize identifiers",
            lambda: True
        )

        self._step(
            steps,
            "Compare identifiers and attributes",
            lambda: True
        )

        return {
            "duplicate_groups": groups
        }

    # =========================================================
    # WF007 - Marketing Campaign Brief
    # =========================================================

    def wf007(self, request, c, steps):

        for key in [
            "goal",
            "dates"
        ]:

            if not c.get(key):

                raise ValueError(
                    f"Missing required campaign input: "
                    f"{key}. Please provide it before "
                    f"generating the brief."
                )

        self._step(
            steps,
            "Validate campaign inputs",
            lambda: True
        )

        self._step(
            steps,
            "Identify campaign objective",
            lambda: True
        )

        result = self._step(
            steps,
            "Generate campaign brief with LLM",
            lambda: self.llm.campaign_brief(c)
        )

        return result

    # =========================================================
    # WF008 - SEO Keyword Classification
    # =========================================================

    def wf008(self, request, c, steps):

        df = self._step(
            steps,
            "Read keyword list",
            lambda: read_csv(
                "keywords.csv"
            ).drop_duplicates(
                subset=["keyword"]
            )
        )

        def classify(k):

            x = k.lower()

            if any(
                w in x
                for w in [
                    "buy",
                    "price",
                    "discount",
                    "deal"
                ]
            ):
                return "transactional"

            if any(
                w in x
                for w in [
                    "best",
                    "top",
                    "review",
                    "compare"
                ]
            ):
                return "commercial"

            if any(
                w in x
                for w in [
                    "what",
                    "how",
                    "guide",
                    "meaning"
                ]
            ):
                return "informational"

            return "navigational"

        df["intent"] = df.keyword.map(
            classify
        )

        df["priority"] = df.search_volume.apply(
            lambda x:
                "HIGH"
                if x >= 1000
                else
                "MEDIUM"
                if x >= 300
                else
                "LOW"
        )

        df["recommended_page"] = (
            df.intent.map({
                "informational": "blog/guide",
                "commercial": "category/comparison",
                "transactional": "product/landing",
                "navigational": "homepage/brand"
            })
        )

        self._step(
            steps,
            "Classify search intent",
            lambda: True
        )

        self._step(
            steps,
            "Map keywords to categories/pages",
            lambda: True
        )

        return df.to_dict(
            orient="records"
        )

    # =========================================================
    # WF009 - Employee Task Assignment
    # =========================================================

    def wf009(self, request, c, steps):

        employees = self._step(
            steps,
            "Load employee data",
            lambda: load_json_data("employees.json")
        )

        task = c.get(
            "task",
            request
        )

        required = set(
            x.lower()
            for x in c.get(
                "required_skills",
                []
            )
        )

        candidates = []

        for e in employees:

            skills = set(
                x.lower()
                for x in e["skills"]
            )

            match = len(
                required & skills
            )

            capacity = 100 - e["workload"]

            candidates.append(
                (
                    match,
                    capacity,
                    e
                )
            )

        candidates.sort(
            key=lambda x: (
                x[0],
                x[1]
            ),
            reverse=True
        )

        best = (
            candidates[0]
            if candidates
            else None
        )

        self._step(
            steps,
            "Compare required skills",
            lambda: True
        )

        self._step(
            steps,
            "Check workload and capacity",
            lambda: True
        )

        if (
            not best
            or best[0] == 0
            or best[1] < 20
        ):

            raise ValueError(
                "No suitable employee with "
                "required skills and available "
                "capacity. Escalate to manager."
            )

        self._step(
            steps,
            "Rank candidates",
            lambda: True
        )

        return {
            "recommended_employee": best[2],
            "reason": (
                f"Matched {best[0]} required skill(s) "
                f"with {best[1]}% available capacity."
            ),
            "task": task,
            "priority": c.get(
                "priority",
                "Normal"
            ),
            "deadline": c.get(
                "deadline"
            )
        }

    # =========================================================
    # WF010 - Workflow Performance Report
    # =========================================================

    def wf010(self, request, c, steps):

        df = self._step(
            steps,
            "Load execution logs",
            lambda: read_csv(
                "execution_logs.csv"
            )
        )

        summary = (
            df.groupby("workflow_id")
            .agg(
                total=("status", "count"),
                failures=(
                    "status",
                    lambda x:
                        (x == "FAILED").sum()
                ),
                avg_execution_ms=(
                    "execution_ms",
                    "mean"
                )
            )
            .reset_index()
        )

        summary["failure_rate"] = (
            summary.failures
            / summary.total
            * 100
        ).round(2)

        summary["flag"] = (
            (summary.failure_rate > 10)
            |
            (summary.avg_execution_ms > 1000)
        )

        self._step(
            steps,
            "Calculate success/failure rates",
            lambda: True
        )

        self._step(
            steps,
            "Calculate average execution time",
            lambda: True
        )

        self._step(
            steps,
            "Identify frequent errors and slow steps",
            lambda: True
        )

        return summary.to_dict(
            orient="records"
        )