from kubernetes import client, config
from kubernetes.client.rest import ApiException
from langchain_core.tools import tool


def _core_v1() -> client.CoreV1Api:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    return client.CoreV1Api()


def _pod_ready(pod) -> str:
    for condition in pod.status.conditions or []:
        if condition.type == "Ready":
            return condition.status
    return "Unknown"


@tool
def list_pods(namespace: str = "") -> str:
    """List pods in the cluster with their phase, readiness, restart count, and node.
    Pass an empty string for namespace to list pods across all namespaces, or a
    specific namespace name to filter."""
    v1 = _core_v1()
    try:
        if namespace:
            pods = v1.list_namespaced_pod(namespace).items
        else:
            pods = v1.list_pod_for_all_namespaces().items
    except ApiException as e:
        return f"Error listing pods: {e.reason}"

    if not pods:
        return "No pods found."

    lines = []
    for p in pods:
        restarts = sum(cs.restart_count for cs in (p.status.container_statuses or []))
        lines.append(
            f"{p.metadata.namespace}/{p.metadata.name}  phase={p.status.phase}  "
            f"ready={_pod_ready(p)}  restarts={restarts}  node={p.spec.node_name}"
        )
    return "\n".join(lines)


@tool
def describe_pod(name: str, namespace: str) -> str:
    """Get detailed status for a single pod: phase, conditions, container states
    (waiting/running/terminated reasons), and recent Kubernetes events for it.
    Use this to diagnose why a pod isn't starting or is crashing."""
    v1 = _core_v1()
    try:
        pod = v1.read_namespaced_pod(name=name, namespace=namespace)
    except ApiException as e:
        return f"Error describing pod: {e.reason}"

    lines = [f"Phase: {pod.status.phase}"]

    for c in pod.status.conditions or []:
        lines.append(f"Condition {c.type}={c.status} reason={c.reason}")

    for cs in pod.status.container_statuses or []:
        state = cs.state
        if state.waiting:
            lines.append(f"Container {cs.name}: WAITING - {state.waiting.reason}: {state.waiting.message}")
        elif state.terminated:
            lines.append(
                f"Container {cs.name}: TERMINATED - {state.terminated.reason} "
                f"(exit code {state.terminated.exit_code})"
            )
        elif state.running:
            lines.append(f"Container {cs.name}: RUNNING since {state.running.started_at}")

    try:
        events = v1.list_namespaced_event(
            namespace, field_selector=f"involvedObject.name={name}"
        ).items
        events.sort(key=lambda e: e.last_timestamp or e.event_time or e.metadata.creation_timestamp)
        for e in events[-10:]:
            lines.append(f"Event [{e.type}] {e.reason}: {e.message}")
    except ApiException as e:
        lines.append(f"(could not fetch events: {e.reason})")

    return "\n".join(lines)


@tool
def get_pod_logs(name: str, namespace: str, tail_lines: int = 100, previous: bool = False) -> str:
    """Fetch the most recent log lines for a pod's container. Set previous=true to
    read logs from the pod's last crashed/restarted instance instead of the current one."""
    v1 = _core_v1()
    try:
        return v1.read_namespaced_pod_log(
            name=name, namespace=namespace, tail_lines=tail_lines, previous=previous
        )
    except ApiException as e:
        return f"Error fetching logs: {e.reason}"
