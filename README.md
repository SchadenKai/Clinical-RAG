# Clinical-RAG: Verified Clinical Decision Support for CDC & WHO Guidelines

> [!IMPORTANT]
> **🚧 WORK IN PROGRESS:** This project is currently in active development. 
> APIs, documentation, and architecture are subject to frequent, breaking changes. 
> This repository is public for architectural demonstration and technical review purposes only.

![Status: Under Development](https://img.shields.io/badge/Status-Under_Active_Development-orange?style=for-the-badge&logo=github)
![Version: Pre-alpha](https://img.shields.io/badge/Version-0.1.0--alpha-blue?style=for-the-badge)
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-red.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)](https://github.com/langchain-ai/langgraph)

**Clinical-RAG** is a production-grade, citation-backed AI system designed to bridge the "Trust Gap" in medical information retrieval. It provides clinicians and public health professionals with a verifiable, real-time interface to interact with the latest technical guidelines from the **CDC (Centers for Disease Control and Prevention)** and **WHO (World Health Organization)**.

---

## 🏥 The Problem: Clinical Information Overload
In high-stakes environments, medical professionals face two critical issues:
* **The Search Cost:** Manually verifying contraindications in 200+ page PDF manuals is impossible in a fast-paced clinic.
* **The Trust Gap:** Generic AI hallucinations lack traceable evidence, making them a liability in healthcare.

## 🛡️ The Solution: Verifiable Evidence-Based AI
Clinical-RAG enforces **Domain-Specific Constraints**, prioritizing precision over creativity:
* **Strict Citation Reinforcement:** Programmatic enforcement of citations for every claim.
* **Hybrid Semantic Retrieval:** Combines vector search (Milvus) with keyword precision.
* **Safety-First Routing:** Built-in guardrails to intercept out-of-scope or harmful queries.

### Key Features for Clinical Users:
* **Strict Citation Reinforcement:** Every response is programmatically forced to cite specific chapters and sections of official CDC/WHO guidelines.
* **Hybrid Semantic Retrieval:** Combines vector search with keyword precision to ensure clinical terminology (e.g., specific ICD codes or drug names) is never missed.
* **Reference Phrase Highlighting:** Automatically identifies and highlights the exact sentences in the source documentation that justify the AI's response.
* **Safety-First Routing:** Built-in medical safety guardrails that detect and intercept out-of-scope queries or requests for unauthorized medical diagnoses.

---

## ⚙️ Technical Architecture
Designed as a high-performance microservice, this project demonstrates a "Production-First" approach to AI Engineering.

* **Orchestration:** LangGraph for stateful, multi-agent workflows and predictable AI execution.
* **Vector Infrastructure:** Milvus for high-concurrency, low-latency similarity search.
* **Cloud Operations:** Containerized via Docker and deployed on AWS (ECS Fargate/ALB) with automated CI/CD pipelines via GitHub Actions.
* **Quality Assurance:** Integrated Pytest suite for unit testing and an evaluation harness to benchmark citation accuracy and latency.

---

## 🚀 Use Cases
* **Point-of-Care Support:** Rapidly verify STI treatment protocols or opioid prescribing schedules.
* **Public Health Policy:** Quickly synthesize WHO "Best Buys" for non-communicable disease interventions.
* **Clinical Compliance:** Ensure hospital protocols remain aligned with the latest MMWR (Morbidity and Mortality Weekly Report) recommendations.

---

## 🏁 Roadmap
- V1: End-to-end RAG with CDC/WHO citation enforcement (Current).
- V2: Automated ingestion of MMWR weekly updates and document versioning.
- V3: A/B testing framework for different retrieval strategies (Top-K vs. MMR).

## 🛠 Current Progress (Iteration 1)
- [x] Initial Architecture Design
- [x] Vector Database Schema (Milvus)
- [x] CDC/WHO Document Ingestion Pipeline
- [x] Safety Router implementation
- [x] Evaluation Harness (DeepEval integration)
