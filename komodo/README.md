# Komodo deployment contract

Resource Sync is disabled by the existing TPE operating policy. ai-stack.toml documents the intended settings; it is not evidence of a configured resource.

Create one Stack named **ai-stack**, selecting the existing Server resource for tpe-px1-rmt1 (verify its actual UI name). Use Gitjames181/tpe-ai-stack, main, run directory ".", and docker-compose.yml. Leave automatic updates disabled.

The host checkout is /opt/stacks/tpe-ai-stack. Ansible must first populate /etc/tpe-ai/stack.env and the SSH/gateway secret files. Set AI_CONFIG_DIR and AI_GATEWAY_PORT in the Komodo environment only if their defaults differ from the Ansible configuration.

Use the Git account/deploy-key mechanism already approved for the estate; never put a PAT in the repository URL. Select a deploy action that builds images and verify the image creation times and running source revision afterward.

Recreate both containers together following a tunnel endpoint/key change, because the gateway shares the tunnel's network namespace. Restarting only the gateway is not the intended lifecycle.

Enabling Resource Sync later is a separate policy change. Ensure secret/environment ownership is reconciled before doing so.
