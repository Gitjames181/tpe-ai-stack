# Remaining work

The repositories now implement one Komodo Stack querying one Vast worker, with only tpe-ai-worker.yml added to Ansible.

Before claiming live operation:

1. Review the simplified infrastructure PR.
2. Build the native VPS images and Vast worker image; publish the worker image and record digests.
3. Select the actual rental and its operating/funding policy.
4. Run the worker playbook and confirm bootstrap completion and GPU availability.
5. Set the Stack's connection and secret variables in Komodo, then deploy.
6. Configure the first application/client endpoint and pass streaming plus a real coding tool/edit/test cycle.
7. Prove rental restart recovery and record model/image/source versions.

Source checks exercise nginx with a mock backend, credential startup behavior, model locks, SSH validation and Compose configuration. They do not prove image builds, native ARM64 execution, real SSH forwarding, GPU fit or agent quality.

Later work: independent rental lifecycle/cost control, application workload scheduling, monitoring and additional capacity if production needs availability beyond one rental. No automatic spend cap or high-availability claim is made.

The stated 269 pending PROJ15 tasks remain unchanged.
