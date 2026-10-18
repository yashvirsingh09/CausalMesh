# CausalMesh: Demo Video Script & Walkthrough Guide

> **Hackathon Submission Requirement:**  
> *"Projects that cannot be deployed must include complete local setup instructions and a working demo video."*  
> **Official Demo Video:** [https://youtu.be/skAD7R8OXp8](https://youtu.be/skAD7R8OXp8)  

This guide provides a **minute-by-minute script** to record a polished **2 to 3-minute demo video** using Loom, OBS, or Screen Studio.

---

## Video Outline (Target Length: ~2:45)

| Timestamp | Segment | Visual on Screen | Key Talking Point |
|---|---|---|---|
| **0:00 - 0:30** | The Problem | Red dashboards / Slide or Architecture | Why flat vector RAG fails at 3 AM |
| **0:30 - 0:55** | CausalMesh Overview | CausalMesh Dashboard (`http://localhost:3001`) | FalkorDB as the primary context layer |
| **0:55 - 1:50** | Live Outage & Swarm Demo | Click "Trigger Incident", watch SSE feed & Cytoscape glow | Tri-Agent Swarm: Sentinel $\to$ Investigator $\to$ Mitigator |
| **1:50 - 2:25** | The 3 Tracks Deep Dive | Modals: Procedural, Episodic, Company Brain | Memory Mesh & "Who Knows What" directory |
| **2:25 - 2:45** | Conclusion | Automated Postmortem & GitHub Repo | 42 minutes down to 14.2 seconds MTTR |

---

## Word-for-Word Script

### [0:00 - 0:30] Introduction: The 3:14 AM Problem
**What to show:** Open the dashboard or show the architecture diagram from the README.  
**What to say:**  
> *"Hi everyone! This is CausalMesh—an autonomous SRE Swarm and Incident Memory Mesh powered by FalkorDB.*  
>  
> *If you've ever been on-call at 3:00 AM, you know this scene: an alert fires for a 504 Gateway Timeout. Fifteen dashboards turn red. Four groggy engineers jump on a war room and spend 45 minutes manually digging through Datadog, asking 'Who merged what?' on Slack, and hunting for outdated runbooks.*  
>  
> *Traditional AI agents using flat Vector RAG fail in production because vector similarity cannot traverse multi-hop dependency DAGs, hallucinates unverified commands, and has no organizational context. That's why we put the agent's context in a graph with FalkorDB."*

---

### [0:30 - 0:55] Meet CausalMesh & FalkorDB
**What to show:** Pan over the Cytoscape.js interactive topology map showing 25 microservices. Click a node to open the inspector drawer.  
**What to say:**  
> *"Here is the live CausalMesh dashboard. FalkorDB is not sitting on the side—it shapes every step of our agent swarm's reasoning loop.*  
>  
> *Using FalkorDB's GraphBLAS sparse matrix engine, multi-hop dependency traversals run in under 2 milliseconds. On top, we have isolated multigraph topologies—`causalmesh_prod` and `causalmesh_staging`—living inside a single instance without tenant contamination.*  
>  
> *Let's trigger a real cascade outage and watch the swarm resolve it autonomously."*

---

### [0:55 - 1:50] The Live Incident & Tri-Agent Swarm (The Core Demo)
**What to show:**
1. Under **Incident Trigger**, select scenario: `DB Pool Starvation (PR-88)`.
2. Mode: `Autonomous` | Engine: ` Fast Sim` (or ` Live LLM`).
3. Click **Trigger Incident**.
4. Watch the nodes turn **RED**, the glowing yellow traversal path, the live SSE streaming log on the right, and the nodes transition to **EMERALD GREEN**.

**What to say:**  
> *"Boom—PagerDuty fires an alert on `/checkout`. Notice how checkout-service and its dependencies turn red.*  
>  
> *First, our **Sentinel Agent** steps in. Calling FalkorDB's native `shortestPath` and bottleneck centrality tools, it computes the blast radius across 25 services in 1.4 milliseconds. It isolates that while checkout failed, inventory-service is the root bottleneck.*  
>  
> *Second, our **Investigator Agent** walks the Company Brain graph. It connects code to people, finding that Dave Kim merged PR-88 35 minutes ago, reducing database idle timeout from 30 seconds to 2 seconds.*  
>  
> *Third, our **Mitigator Agent** doesn't hallucinate a shell command. It queries FalkorDB's **Procedural Memory** for the verified `resolve_db_pool_starvation` playbook, executing safe Model Context Protocol (MCP) actions: patching pool limits, triggering a rolling restart, and verifying error rates.*  
>  
> *And look at that—all 25 services are back to emerald green! Mean Time to Resolution: just 14 seconds."*

---

### [1:50 - 2:25] Deep Dive into All 3 Hackathon Tracks
**What to show:**
1. Click **Procedural Memory** card in the top bar: Show the ordered DAG steps (`scale_db_pool` $\to$ `restart_pods` $\to$ `verify_error_rate`).
2. Click **Episodic Memories** card: Show past resolved incidents and MTTR fingerprints.
3. Click **Company Brain** card:
   - Tab 1: Show the **"Who Knows What"** directory for `inventory-service` (Dave Kim with 3 contributions).
   - Tab 2: Show connected Jira Tickets (`TICK-1042`).
   - Tab 3: Show Slack messages from `#deployments`.
   - Tab 4: Show connected Runbook Docs (`DOC-1`).
4. Close modal and click the environment switcher in the header (`Production` $\to$ `Staging`) to show **Multigraph Isolation**.

**What to say:**  
> *"Let's see how CausalMesh covers all three hackathon tracks:*  
>  
> *• **Track 01 (Connected Data):** We used FalkorDB's native graph algorithms like `shortestPath` and centrality as agent tools, with real-time explainability.*  
> *• **Track 02 (Agent Memory):** We built a complete 3-layer memory mesh: **Procedural Memory** with executable DAG playbooks, **Episodic Memory** to recall past incidents, and **Semantic Memory** for failure ontologies. Plus, agent handoffs are stored directly in FalkorDB!*  
> *• **Track 03 (Company Brain):** We implemented the sponsor's exact showcase query—'Who knows about this system?'—connecting Jira tickets, Slack chats, and PR diffs into one unified knowledge graph.*  
>  
> *And notice our multigraph toggle—switching between Staging and Production with zero cross-tenant contamination."*

---

### [2:25 - 2:45] Conclusion & Wrap-Up
**What to show:** Click **Latest Postmortem** button to display the auto-generated markdown postmortem report, then pan over the GitHub repository.  
**What to say:**  
> *"At the end of every incident, CausalMesh auto-generates a postmortem with full Cypher attribution and commits a new episode back to FalkorDB.*  
>  
> *CausalMesh turns 42 minutes of 3 AM panic into 14 seconds of deterministic graph reasoning. The codebase includes 37 passing automated tests, full Docker deployment, and is open-source on GitHub.*  
>  
> *Thank you, and happy graphing with FalkorDB!"*

---

## Quick Tips for Recording
- **Resolution:** 1080p (1920x1080) or 1440p.
- **Audio:** Use a clean microphone or headset; avoid background noise.
- **Speed:** Keep mouse movements smooth and intentional.
- **Host Link:** Upload your recording to YouTube (Unlisted), Loom, or Google Drive (public link) for the hackathon submission form.
