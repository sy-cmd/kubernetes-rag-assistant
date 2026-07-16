To forward Qdrant's ports execute one of the following commands:
  export POD_NAME=$(kubectl get pods --namespace rag-system -l "app.kubernetes.io/name=qdrant,app.kubernetes.io/instance=qdrant" -o jsonpath="{.items[0].metadata.name}")

If you want to use Qdrant via http execute the following commands
  kubectl --namespace rag-system port-forward $POD_NAME 6333:6333

If you want to use Qdrant via grpc execute the following commands
  kubectl --namespace rag-system port-forward $POD_NAME 6334:6334

If you want to use Qdrant via p2p execute the following commands
  kubectl --namespace rag-system port-forward $POD_NAME 6335:6335
