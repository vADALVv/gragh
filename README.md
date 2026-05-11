# Multi-Agent Information Diffusion Simulator

## Overview

This project implements a multi-agent simulation framework for studying information diffusion, manipulative influence, emotional contagion, and adversarial communication in social networks.

The system models:

- ordinary users,
- adversarial/red-team actors,
- LLM-based autonomous agents,
- stochastic repost dynamics,
- cognitive state evolution,
- and transformer-based defensive moderation systems.

The simulator combines:

- graph theory,
- probabilistic diffusion,
- social influence modeling,
- emotional propagation,
- and neural NLP-based risk analysis.

The project is intended for:

- AI safety research,
- misinformation analysis,
- cyberpsychology,
- adversarial LLM behavior studies,
- information warfare simulation,
- and social network experimentation.

---

# Table of Contents

1. Project Goals
2. System Architecture
3. Mathematical Model
4. Agent Types
5. Cognitive State Model
6. Message Model
7. Diffusion Dynamics
8. Blue Agent
9. LLM Agents
10. Graph Generation
11. Visualization System
12. File Structure
13. Installation
14. Dependencies
15. Running the Simulation
16. Output Files
17. Visualization Guide
18. JSON Output Specification
19. Research Applications
20. Future Improvements

---

# 1. Project Goals

The main goal of the simulator is to reproduce realistic information propagation scenarios in heterogeneous social networks.

The system allows experimentation with:

- manipulative campaigns,
- coordinated influence operations,
- emotional amplification,
- moderation strategies,
- adversarial content generation,
- and defensive AI systems.

The framework can be used to study:

- cascade formation,
- polarization,
- emotional escalation,
- influence centrality,
- and dangerous content propagation.

---

# 2. System Architecture

The project consists of several interacting modules.

```text
                   ┌────────────────────┐
                   │   graph_structure  │
                   │  Social Graph Gen  │
                   └─────────┬──────────┘
                             │
                             ▼
                   ┌────────────────────┐
                   │    simulation.py   │
                   │ Diffusion Engine   │
                   └─────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
 ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
 │  Red Agents    │ │  User Agents   │ │   LLM Agents   │
 └────────────────┘ └────────────────┘ └────────────────┘
                             │
                             ▼
                   ┌────────────────────┐
                   │    Blue Agent      │
                   │ Risk Classification│
                   └─────────┬──────────┘
                             ▼
                   ┌────────────────────┐
                   │   visualization    │
                   │ Interactive HTML   │
                   └────────────────────┘
