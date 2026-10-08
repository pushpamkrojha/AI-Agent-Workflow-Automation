# AI Agent Workflow Automation

Technical assignment implementation: a reusable AI agent that reads workflow definitions from Excel, selects the correct workflow for a user request, executes reusable tools, handles business conditions/errors, and prints the selected workflow, executed steps, and final result.

## 🎥 Project Demo

A complete working demonstration of the AI Agent Workflow Automation system:

[Loom Demo Video](https://www.loom.com/share/ad26eab344b14198aca836fca109ccbe)

The demo covers:
- Overall system architecture
- Excel-based workflow processing
- Workflow identification and routing
- Workflow execution and reusable tools
- Conditions and error handling
- Multiple workflow examples
- Performance reporting
- Dynamic support for adding an 11th workflow
- Automated testing

## Architecture

```text
User Request
     |
     v
LLM Router (tool calling)
     |
     v
Workflow Registry <--- Excel source
     |
     v
Workflow Executor
     |
     +--> Reusable tools (CSV/XLSX, calculator, similarity, JSON/API simulation)
     |
     +--> Conditions / validation / error handling
     |
     v
Final structured result + execution trace
```

### Why this is scalable
- Workflow definitions are loaded from the supplied Excel file at runtime.
- Routing is not a list of chatbots; the LLM selects a workflow ID through a tool call.
- Execution is centralized in one executor and reusable tools are shared across workflows.
- Real external APIs are represented by local mock data because the assignment permits API simulation.
- Adding workflow WF011 requires adding its Excel definition and a small executor handler/tool set; the router does not need a new chatbot.

## Requirements
- Python 3.10+
- VS Code
- Optional OpenAI API key for LLM routing/content generation

## Windows / VS Code setup

Open the project folder in VS Code, then open **Terminal > New Terminal**.

### 1. Create virtual environment

```powershell
python -m venv .venv
```

### 2. Activate it

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install packages

```powershell
pip install -r requirements.txt
```

### 4. Configure LLM

Copy `.env.example` to `.env`.

For no-API-key testing:

```env
MOCK_MODE=true
```

For actual LLM routing:

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
MOCK_MODE=false
```

## Run

Interactive mode:

```powershell
python main.py
```

Or directly:

```powershell
python main.py --request "Which products need restocking?"
```

Test a specific workflow:

```powershell
python main.py --workflow WF001
python main.py --workflow WF002
python main.py --workflow WF003
```

For WF003 with another vendor file:

```powershell
python main.py --workflow WF003 --file "C:\path\to\vendor.xlsx"
```

## What is implemented

- WF001 Inventory Restock Check
- WF002 Product Price Validation
- WF003 Vendor File Processing
- WF004 Product Description Generator
- WF005 Customer Order Status
- WF006 Duplicate Product Detection
- WF007 Marketing Campaign Brief
- WF008 SEO Keyword Classification
- WF009 Employee Task Assignment
- WF010 Workflow Performance Report

## Error handling examples

The system returns a failed status and records the failed step when:
- a workflow cannot be identified
- required WF003 file/columns are missing
- WF004 required product data is missing
- WF005 order is not found
- WF007 goal/dates are missing
- WF009 no suitable employee is available

## Interview explanation

**Q: Why Excel?**
A: The assignment explicitly provides Excel as the workflow source. I treat it as configuration/metadata and load it into a workflow registry instead of hard-coding the workflow descriptions.

**Q: Why an LLM router?**
A: Natural-language requests vary. The LLM maps the request to one of the known workflow IDs using structured tool calling. Execution remains deterministic in Python.

**Q: Why not let the LLM execute everything?**
A: Business-critical operations and decision rules should remain deterministic and testable. The LLM is used for routing and content-generation tasks where language reasoning is useful.

**Q: How would you add WF011?**
A: Add its workflow definition to Excel, implement/reuse the required tool operations in the executor, and register the handler. The router and overall architecture remain unchanged.

**Q: How do you handle unavailable APIs?**
A: The assignment permits API simulation, so this submission uses local JSON/CSV data as deterministic mock services. These tool boundaries can later be replaced with real API clients without changing the router.

## Test

```powershell
python -m pytest -q
```
