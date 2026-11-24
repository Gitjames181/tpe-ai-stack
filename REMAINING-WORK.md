# Remaining work and release gates

## Required before claiming live operation

- Review and apply the matching tpe-infrastructure change.
- Build both native VPS images and the Vast amd64 image; publish the latter privately and record exact digests.
- Choose the actual priced rental and funding settings. A server-only cost policy does not specify a dollar ceiling.
- Confirm live VPS resources and the exact Komodo Server resource.
- Supply dedicated SSH access, a verified host key, caller tokens and AI TLS material through SOPS.
- Deploy DNS/host prerequisites and the Komodo Stack.
- Measure model fit, context, latency and GPU use on the chosen hardware.
- Pass a real agent tool/edit/test cycle and rental restart/reconnection.
- Record deployment commits, image/model digests, instance ID and contract expiry.

## Validation limits

The initial automated checks cover source/configuration, actual nginx gateway behavior against a mocked inference backend, model-lock policy and SSH input validation. They do not replace a Docker image build, ARM64 container execution, provider SSH forwarding, a GPU inference run or a production Ansible check.

The host role is tested through a local check-mode harness with synthetic credentials. SOPS-backed production execution requires the estate's normal installed collections and operator key.

## Next improvements after the pilot

1. Independent provider lifecycle/cost reconciliation with explicit instance ownership, lease limits and no coupling to media-session teardown.
2. Application workload priority, queues and separate capacity before making production depend on one rental.
3. Tool-call streaming regression tests using the chosen pinned model/client.
4. External monitoring of readiness, errors, latency, GPU memory and contract expiry.
5. Multiple model routes/embedding model only when required; evaluate a native ARM64 routing gateway if needed.
6. Test destructive-loss recovery from externally retained model/image locks.
7. Check software/model licensing for any new capability.

The 269 pending PROJ15 tasks remain the user's stated backlog count. No master workbook completion status has been changed by this infrastructure work.
