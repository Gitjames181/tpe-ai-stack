# Runbook

## Before deployment

1. Publish the private source repository and review the tpe-infrastructure changes. Do not treat local files or a draft PR as deployed.
2. Confirm live VPS CPU architecture, spare RAM/disk, Docker/Compose, nginx and existing Komodo Server registration. Repository metadata records ARM64 but is not a live hardware probe.
3. Select a specific Vast on-demand offer and record its compute, storage, bandwidth, contract expiry and payment settings. No numeric spending cap has been supplied in this task.
4. Use a dedicated rental SSH key. Verify its server host key through an independent trusted provider/operator channel. ssh-keyscan alone is discovery, not verification.
5. Prepare a certificate that explicitly includes DNS:ai.tpe, with a chain trusted by the actual clients. The host role deliberately uses a dedicated certificate rather than rotating the estate's shared certificate.

No broad tailnet enrollment or production application credentials are needed on the rental.

## Build the images

On a trusted machine with Docker, from the stack checkout:

~~~sh
docker compose --env-file .env.example build
docker build --platform linux/amd64 -f vast/Dockerfile -t ghcr.io/gitjames181/tpe-ai-worker:0.1.0 .
~~~

The first command builds the VPS images for the builder's native architecture. Build them on the ARM64 VPS, or use an explicit ARM64 builder if preparing elsewhere. Never run an amd64 gateway through emulation by accident.

Publish the Vast image to an approved private registry and record its immutable digest. Use only a dedicated, read-only image-pull credential for the provider. Building/pushing an image is a distinct step from committing this repository. Registry access and publication are not assumed completed.

Initial base versions: nginx 1.30.8-alpine, Alpine 3.24.4 and Ollama 0.40.18. These are explicit tags; packages installed during image build can still change. Use the recorded resulting image digest for repeat deployment.

## Vast template

| Field | Value |
|---|---|
| Image | The published tpe-ai-worker image, preferably by digest |
| Launch mode | SSH, without Jupyter |
| On-start command | /opt/tpe-ai/start.sh |
| Raw inference bind | 127.0.0.1:11434 inside the rental |
| Disk | Selected once, sized for weights and image headroom |
| GPU | One allocated NVIDIA GPU with a driver compatible with the built image |

Do not publish Ollama's port as an application endpoint. The base image may declare EXPOSE; loopback binding must be verified regardless of provider port metadata. The SSH service is injected by Vast's SSH launch mode. Test that it permits local forwarding; do not disable SSH host verification to make a tunnel work.

Do not run the existing enrichment tpe-gpu-worker.yml on this ordinary container. Do not install host NVIDIA drivers or a Docker daemon inside it.

After launch, record the instance ID, current public endpoint, mapped SSH port and confirmed host key. Verify nvidia-smi works. Configure the container via tpe-infrastructure's ai_workers inventory:

~~~sh
cd /path/to/tpe-infrastructure/ansible
ANSIBLE_HOST_KEY_CHECKING=True ansible-playbook -i /secure/ai-workers.yml playbooks/tpe-ai-worker.yml --check --diff
ANSIBLE_HOST_KEY_CHECKING=True ansible-playbook -i /secure/ai-workers.yml playbooks/tpe-ai-worker.yml
~~~

The worker image starts its default model automatically. The playbook reconciles non-secret model settings only. Inspect the bootstrap process until it finishes successfully:

~~~sh
supervisorctl -c /opt/tpe-ai/supervisord.conf status
tail -n 40 /var/log/tpe-ai/bootstrap.log
cat /workspace/tpe-ai/model-lock.json
ollama ps
nvidia-smi
~~~

The bootstrap process is a one-shot job, so EXITED after a successful completion is normal. Check its exit status/log and lock rather than treating any EXITED state as success. Capture the full resolved model digest in tpe_ai_expected_digest before recreating or moving the worker. A mutable source tag is not a portable lock.

## Configure the gateway host through Ansible

The tpe_ai_host role requires these non-secret values in inventory/host vars:

~~~yaml
tpe_ai_enabled: true
tpe_ai_vast_ssh_host: SELECTED_PUBLIC_HOST
tpe_ai_vast_ssh_port: SELECTED_MAPPED_PORT
tpe_ai_vast_ssh_user: root
tpe_ai_vast_known_hosts: VERIFIED_KNOWN_HOSTS_RECORD
~~~

Store the following in the existing infrastructure SOPS vault, never in chat, Git plaintext or command-line extra vars:

- vault_tpe_ai_vast_ssh_private_key
- vault_tpe_ai_api_tokens, a mapping such as development and tpe_stack to separate tokens
- vault_tpe_ai_tls_certificate_pem
- vault_tpe_ai_tls_private_key_pem

Caller labels must match lowercase letters/digits/underscores; tokens must contain 32-128 URL-safe characters. The host role writes UID-owned read-only secret mounts for the containers. It does not deploy the application.

~~~sh
cd /path/to/tpe-infrastructure/ansible
ansible-playbook playbooks/tpe-ai-host.yml --check --diff
ansible-playbook playbooks/tpe-ai-host.yml
~~~

Run the existing Technitium role through its normal control-host deployment procedure after enabling the gateway. Its record list now includes ai.tpe only when the AI host is enabled. The standard compute playbook also includes the host role, disabled by default.

Distributing trust to clients is a separate acceptance step: configure the certificate issuer in the laptop, container and language runtime trust stores. Do not use curl -k or disable Node/Python TLS verification.

## Deploy ai-stack in Komodo

Configure the Stack as described in komodo/README.md. Keep Resource Sync and automatic updates disabled. Check the correct Git account, target server, main branch and Compose file, then deploy with image building enabled.

For a corresponding operator-run Compose deployment:

~~~sh
cd /opt/stacks/tpe-ai-stack
docker compose -p ai-stack up -d --build --force-recreate
docker compose -p ai-stack ps
~~~

The explicit project name prevents accidental parallel stacks. The host's /etc/tpe-ai/stack.env supplies the SSH target; this is an env_file for the tunnel, not a file containing gateway tokens.

Both containers must be recreated after tunnel network-namespace replacement. Secret files are bind mounts: atomic replacement on the host can leave the old inode mounted until the container is recreated. A successful Ansible secret write therefore does not prove the running credential was rotated.

## Validate the complete path

Set TPE_AI_API_KEY through the normal secret injection mechanism and run:

~~~sh
python3 scripts/smoke.py --base-url https://ai.tpe --ca-file /path/to/trusted-ai-ca.pem
~~~

For a laptop SSH tunnel to the gateway's host-loopback port, use an HTTP localhost base URL. The script refuses plain HTTP to a remote hostname and refuses redirects, preventing a misconfigured endpoint from forwarding the token to another service.

The smoke test proves authentication rejection, management-API isolation, model alias discovery and a completed streaming response. It does not prove tool-call quality, desired model-release reconciliation or GPU residency.

Then complete all of the following:

- Check the worker's bootstrap exit status and compare worker.json with model-lock.json.
- Observe ollama ps and nvidia-smi during inference. Record context, GPU memory and whether any layers are on CPU.
- Connect the coding client and complete a function call, return the tool result, edit a scoped file and run the repository's relevant test/lint check.
- Confirm a failed tool/test result can be handled by the next model turn.
- Stop/start the same Vast instance and verify the on-start script, model state, tunnel recovery and streamed completion.
- Prove the GPU's raw inference endpoint is inaccessible externally, and wrong/no gateway credentials fail.

The existing Claude Code client can be evaluated against the local model:

~~~sh
export ANTHROPIC_BASE_URL=https://ai.tpe
export ANTHROPIC_AUTH_TOKEN="$TPE_AI_API_KEY"
export ANTHROPIC_API_KEY=""
export ANTHROPIC_DEFAULT_SONNET_MODEL=tpe-code:latest
export ANTHROPIC_DEFAULT_HAIKU_MODEL=tpe-code:latest
export ANTHROPIC_DEFAULT_OPUS_MODEL=tpe-code:latest
claude --model tpe-code:latest
~~~

Configure Node's additional CA trust if needed. Check the client's status/settings for a conflicting endpoint or provider. Claude Code is the interface here; inference is performed by the open model, not Claude Sonnet. Ollama's Anthropic compatibility is partial and 16K may be too small for that client's prompts. If so, use a configured OpenAI-compatible Qwen Code/Cline session for the bounded pilot or increase GPU capacity after measurement.

For OpenAI-compatible clients, use https://ai.tpe/v1, the model tpe-code:latest, a dedicated gateway key and a context budget matching the server. Configure all auxiliary models explicitly; no hosted fallback.

## Recovery and changes

- **GPU temporarily offline:** the gateway returns 503 for transport failures. The tunnel reconnects after SSH connectivity returns. After an endpoint change, update inventory and verified host keys through Ansible, then recreate both containers.
- **Host key changed:** fail closed. Independently verify the new key; do not remove StrictHostKeyChecking.
- **Model digest mismatch:** bootstrap refuses to replace the alias silently. Investigate the source, set a reviewed exact expected_digest and rerun the worker playbook. Compare the lock before accepting the new release.
- **TLS change:** apply the host role, inspect nginx validation, and ensure clients trust the current issuer.
- **Rollback:** redeploy the previous known source/image versions and corresponding host configuration. Stop ai-stack in Komodo to remove service access. Setting tpe_ai_enabled=false only skips future provisioning; it does not remove existing containers, DNS or host files.
- **Rental destruction:** export the model lock and any required results first. Confirm the correct instance ID and provider termination state. Stopped storage can still be billed; destroy retained storage separately if applicable.

Do not enable an unattended rental until an independent lease/cost controller is implemented or a deliberate funded always-on operating policy is recorded. There is no claimed automatic cost cap in this first version.
