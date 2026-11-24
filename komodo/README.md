# Komodo deployment

One Stack named ai-stack on the existing tpe-px1-rmt1 Server resource.

- Repository: Gitjames181/tpe-ai-stack
- Branch: main
- Checkout: /opt/stacks/tpe-ai-stack
- Compose file: docker-compose.yml
- Build the two local images on the target host.
- Keep Resource Sync disabled and auto_update=false, following tpe-support's current policy.

The TOML is intent only; configure the actual Stack in Komodo. The Stack environment owns the Vast endpoint and credentials listed in ../.env.example. Supply private values through Komodo secret variables. No host Ansible playbook or pre-created /etc/tpe-ai files are required.

Run tpe-ai-worker.yml against the prepared rental, then deploy this Stack. Recreate both local containers together after endpoint/key changes. See ../RUNBOOK.md.
