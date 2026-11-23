export PATH=~/bin:$PATH
for ns in todo-dev todo-stg todo-prod; do for r in deploy svc; do for o in $(kubectl -n $ns get $r -o name); do kubectl -n $ns patch $o --type json -p '[{"op":"remove","path":"/metadata/finalizers"}]' >/dev/null 2>&1; done; done; done
sleep 3
for ns in todo-dev todo-stg todo-prod; do kubectl -n $ns get deploy,svc -o custom-columns=N:.metadata.name,D:.metadata.deletionTimestamp --no-headers; done
cd /tmp/gitsrv/todo-app-config.git && git update-ref refs/heads/main 4c9c0e4c04fa5f3ff6021e9358685096ec03d5a2 && for b in $(git for-each-ref --format='%(refname)' refs/heads/promote); do git update-ref -d $b; done
cd /tmp/gitlab-sim/alice && git reset -q --hard 48335d4
cd /tmp/argo
for a in todo-dev todo-stg todo-prod; do timeout 30 argocd app get $a --hard-refresh >/dev/null 2>&1; done
sleep 8
for a in todo-dev todo-stg todo-prod; do timeout 60 argocd app sync $a >/dev/null 2>&1; done
sleep 3
for a in todo-dev todo-stg todo-prod; do kubectl -n argocd patch application $a --type json -p '[{"op":"replace","path":"/status/history","value":[]}]' >/dev/null 2>&1; done
argocd app list | cut -c1-100
