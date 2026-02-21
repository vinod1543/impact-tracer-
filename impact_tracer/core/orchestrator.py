"""Core orchestrator stub.

Layer: Orchestration (Layer 4)
Responsibility: Coordinate engine execution order.
Implements: PRD data flow contract baseline.
"""

from impact_tracer.core.analyzer.python.ast_parser import PythonAstParser
from impact_tracer.core.analyzer.python.call_graph_builder import build_call_edges
from impact_tracer.core.diff.diff_parser import map_diff_to_symbols, parse_unified_diff
from impact_tracer.core.graph.graph_builder import build_dependency_graph
from impact_tracer.core.graph.graph_builder import to_networkx
from impact_tracer.core.llm.explainer import LLMExplainer
from impact_tracer.core.propagation.propagator import propagate_changes
from impact_tracer.core.risk.config import load_risk_weights
from impact_tracer.core.risk.scorer import aggregate_overall_risk, score_affected_symbols
from impact_tracer.models.diff import ChangeType
from impact_tracer.models.graph import DependencyGraph
from impact_tracer.models.report import AnalysisMetadata, DiffSummary, ImpactReport


def build_graph(project_path: str) -> DependencyGraph:
    """Build a dependency graph for a project.

    Args:
        project_path: Path to target project.

    Returns:
        DependencyGraph: Built module and symbol dependency graph.
    """
    parser = PythonAstParser()
    symbol_table = parser.parse_project(project_path)
    call_graph = build_call_edges(symbol_table)
    return build_dependency_graph(symbol_table, call_graph)


def analyze(diff_str: str, project_path: str, enable_llm: bool = True) -> ImpactReport:
    """Run end-to-end impact analysis.

    Args:
        diff_str: Unified diff string.
        project_path: Project path.
        enable_llm: Whether to run LLM explanation stage.

    Returns:
        ImpactReport: Structured impact report.
    """
    parser = PythonAstParser()
    symbol_table = parser.parse_project(project_path)
    call_graph = build_call_edges(symbol_table)
    dependency_graph = build_dependency_graph(symbol_table, call_graph)

    diff_result = parse_unified_diff(diff_str)
    changed_symbols = map_diff_to_symbols(diff_result, symbol_table)
    diff_result.changed_symbols = changed_symbols

    symbol_index = {symbol.id: symbol for symbol in symbol_table.symbols}
    changed_symbol_ids = [item.symbol_id for item in changed_symbols if item.symbol_id in symbol_index]

    nx_graph = to_networkx(dependency_graph)
    affected_symbols, propagation_paths = propagate_changes(nx_graph, changed_symbol_ids, symbol_index)

    changed_type_map = {item.symbol_id: item.change_type for item in changed_symbols}
    weights = load_risk_weights()
    scored_affected = score_affected_symbols(nx_graph, affected_symbols, changed_type_map, weights)

    total_files = len(symbol_table.files)
    parse_successful = len([table for table in symbol_table.files if not table.parse_error])
    parse_success_rate = (parse_successful / total_files) if total_files else 1.0

    import_resolution_rate = 1.0
    call_resolution_rate = call_graph.call_resolution_rate

    overall_risk = aggregate_overall_risk(
        scored_affected,
        import_resolution_rate=import_resolution_rate,
        ast_parse_success_rate=parse_success_rate,
        call_resolution_rate=call_resolution_rate,
    )

    metadata = AnalysisMetadata(
        total_files=total_files,
        parse_success_rate=parse_success_rate,
        import_resolution_rate=import_resolution_rate,
        call_resolution_rate=call_resolution_rate,
    )

    diff_summary = DiffSummary(
        files_changed=len(diff_result.files_changed),
        hunks=len(diff_result.hunks),
        changed_symbols=len(changed_symbols),
    )

    report = ImpactReport(
        project_path=project_path,
        diff_result=diff_result,
        diff_summary=diff_summary,
        changed_symbols=changed_symbols,
        affected_symbols=scored_affected,
        propagation_paths=propagation_paths,
        overall_risk=overall_risk,
        confidence=overall_risk.confidence,
        explanation=None,
        metadata=metadata,
    )

    if enable_llm:
        explainer = LLMExplainer()
        report.explanation = explainer.explain(report)

    return report
