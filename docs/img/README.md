# Скриншоти для README

Сюди покладіть скриншоти кроків розгортання. README ([../../README.md](../../README.md))
посилається на ці файли за іменами нижче. Поки файл відсутній — посилання показує
«битий» прев'ю; додайте PNG із тим самим іменем, і він підхопиться.

| Файл | Що зафіксувати |
| --- | --- |
| `00-terraform-apply.png` | Хвіст `terraform apply`: `Apply complete!` + блок `Outputs`. |
| `00-kubectl-nodes.png` | `kubectl get nodes` — ноди у статусі `Ready`. |
| `01-github-actions.png` | Вкладка **Actions** → успішний (зелений) запуск `retrain-model`. |
| `01-ghcr-package.png` | Сторінка ghcr-пакета з тегами `latest` і `<MODEL_VERSION>`. |
| `02-secret-created.png` | Вивід `kubectl create secret … → created`. |
| `03-webhook-url.png` | Фрагмент `argocd/application.yaml` із заповненим `retrainWebhook.url`. |
| `04-argocd-apply.png` | `kubectl apply` 4 ArgoCD Application → `created`. |
| `05-argocd-healthy.png` | ArgoCD UI: усі Applications `Synced` / `Healthy`. |
| `05-pods-running.png` | `kubectl get pods -n application` — `aiops-quality-*` у `Running`. |
| `06-predict.png` | Відповідь `curl /predict` із `predicted_label` і `drift_detected`. |
| `06-drift-logs.png` | `kubectl logs … \| grep "Drift detected"` — подія дрейфу. |
| `06-grafana.png` | Дашборд **AIOps Quality** у Grafana (трафік + drift). |

> Рекомендація: PNG, ширина ~1200px, без чутливих даних (токени/паролі — затерти).
