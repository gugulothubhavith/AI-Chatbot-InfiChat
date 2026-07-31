---
title: Sub-processors
version: 1.0.0
effective_date: "[PLACEHOLDER: EFFECTIVE DATE]"
last_updated: "[PLACEHOLDER: LAST UPDATED DATE]"
---

# Sub-processors

**Version 1.0.0** — Effective [PLACEHOLDER: EFFECTIVE DATE]

> **This document is a thorough draft, not legal advice.** Have qualified counsel
> review it before launch. Every bracketed `[PLACEHOLDER]` must be replaced with a
> real value, and every entry below must be re-verified against your actual
> deployment before you publish this list.

This page lists the third parties that may process personal data on our behalf
when you use InfiChat ("the Service"). We use the term "sub-processor" as defined
in GDPR Article 28.

InfiChat is a self-hostable platform. **Which sub-processors actually apply to you
depends on how the instance you use is deployed and configured.** An operator who
self-hosts with local models and no external search may involve none of the
inference or search providers below. If you are using an instance operated by
someone other than us, ask that operator for their own list.

## How to read this list

| Column | Meaning |
| --- | --- |
| Purpose | Why data reaches them |
| Data categories | What is disclosed to them |
| Location | Where processing takes place |
| Transfer mechanism | Safeguard relied on for cross-border transfer |
| Optional | Whether the operator can disable this dependency |

---

## 1. Model inference

### NVIDIA (NVIDIA NIM / `integrate.api.nvidia.com`)

| | |
| --- | --- |
| **Purpose** | Generating model responses. Every chat message, deep research query, deep thinking query, and code generation request is sent here for inference. |
| **Data categories** | Prompt content, conversation context sent with the prompt, retrieved document excerpts used to ground an answer, and system instructions. This is the single most substantive disclosure the Service makes. |
| **Location** | [PLACEHOLDER: CONFIRM PROCESSING REGION WITH NVIDIA] |
| **Transfer mechanism** | [PLACEHOLDER: SCC / DPA REFERENCE — obtain and cite NVIDIA's DPA] |
| **Optional** | No, for hosted use. Model inference is the core function of the Service. An operator may substitute a self-hosted model, in which case no prompt data leaves their infrastructure. |
| **Provider terms** | [PLACEHOLDER: LINK TO NVIDIA API TERMS AND PRIVACY POLICY] |

**Note on training:** whether a provider may train on your prompts is a material
privacy question. [PLACEHOLDER: CONFIRM NVIDIA'S TRAINING AND RETENTION POSTURE
FOR THE SPECIFIC API TIER YOU USE, AND STATE IT PLAINLY HERE.] Do not leave this
placeholder unresolved — users are entitled to a direct answer.

### Voyage AI (`api.voyageai.com`)

| | |
| --- | --- |
| **Purpose** | Generating vector embeddings for retrieval-augmented generation (RAG), so uploaded documents can be searched semantically. |
| **Data categories** | Text extracted from documents you upload, and the text of queries run against them. |
| **Location** | [PLACEHOLDER: CONFIRM PROCESSING REGION] |
| **Transfer mechanism** | [PLACEHOLDER: SCC / DPA REFERENCE] |
| **Optional** | Yes. An operator may configure a local embedding model instead. |
| **Provider terms** | [PLACEHOLDER: LINK TO VOYAGE AI TERMS AND PRIVACY POLICY] |

---

## 2. Authentication

### Google (Google Identity / OAuth "Sign in with Google")

| | |
| --- | --- |
| **Purpose** | Optional single sign-on. Used only if you choose to sign in with Google rather than with an email address and password. |
| **Data categories** | We receive your email address, display name, and profile photo URL from the Google ID token you present. We do not receive your Google password. Google independently learns that you authenticated to this Service. |
| **Location** | [PLACEHOLDER: CONFIRM — Google processes globally] |
| **Transfer mechanism** | [PLACEHOLDER: SCC / DPA REFERENCE — cite Google's Data Processing Terms] |
| **Optional** | Yes. Email-and-password registration is available and involves Google not at all. |
| **Provider terms** | [PLACEHOLDER: LINK TO GOOGLE PRIVACY POLICY] |

---

## 3. Payments

### Stripe

| | |
| --- | --- |
| **Purpose** | Processing subscription payments and maintaining billing records. |
| **Data categories** | Billing name, email address, payment method details, transaction history, and billing address. **Full card numbers are transmitted directly to Stripe and are never received or stored by us.** |
| **Location** | [PLACEHOLDER: CONFIRM PROCESSING REGION] |
| **Transfer mechanism** | [PLACEHOLDER: SCC / DPA REFERENCE — cite Stripe's DPA] |
| **Optional** | Yes, where the operator offers no paid plans. |
| **Provider terms** | [PLACEHOLDER: LINK TO STRIPE PRIVACY POLICY] |

Stripe acts as an independent controller for certain fraud-prevention and
regulatory purposes, not solely as our processor. Their own privacy notice
governs that activity.

---

## 4. Web search and content retrieval

### SearXNG (metasearch)

| | |
| --- | --- |
| **Purpose** | Executing web searches when you use web search, or when a query is automatically escalated to search for grounding. |
| **Data categories** | Search query text derived from your prompt. |
| **Location** | Depends on deployment. In the reference deployment SearXNG runs as a local container operated by the instance operator, **but it forwards queries onward to upstream search engines**, which are independent controllers we do not control. |
| **Transfer mechanism** | [PLACEHOLDER: NOT APPLICABLE FOR THE LOCAL CONTAINER; UPSTREAM ENGINES ARE INDEPENDENT CONTROLLERS] |
| **Optional** | Yes. Web search can be disabled. |

**Be aware:** a search query built from your prompt may reach upstream search
engines such as [PLACEHOLDER: LIST THE ENGINES YOUR SEARXNG INSTANCE ACTUALLY
QUERIES]. Their handling of that query is governed by their own policies.

### Public content sources

The Service fetches publicly available content from sources including
`arxiv.org`, `en.wikipedia.org`, and general web pages returned by search. These
are ordinary outbound requests for public documents. **The originating IP address
is that of the server, not yours**, and no account identifier is attached.

### `api.airforce`

| | |
| --- | --- |
| **Purpose** | [PLACEHOLDER: CONFIRM WHAT THIS ENDPOINT IS USED FOR — appears in image generation. Verify and describe accurately, or remove the dependency.] |
| **Data categories** | [PLACEHOLDER: CONFIRM] |
| **Location** | [PLACEHOLDER: CONFIRM] |
| **Transfer mechanism** | [PLACEHOLDER: CONFIRM] |
| **Optional** | [PLACEHOLDER: CONFIRM] |

> **Operator action required.** Do not publish this list with the entry above
> unresolved. If this endpoint's operator, terms, and data handling cannot be
> established, remove the dependency from the code rather than disclosing an
> unknown third party as a sub-processor.

---

## 5. Speech

### Microsoft Edge TTS

| | |
| --- | --- |
| **Purpose** | Converting assistant responses to speech when you use read-aloud. |
| **Data categories** | The text of the response to be spoken. |
| **Location** | [PLACEHOLDER: CONFIRM PROCESSING REGION] |
| **Transfer mechanism** | [PLACEHOLDER: SCC / DPA REFERENCE] |
| **Optional** | Yes. Browser-native speech synthesis is available as a fallback and keeps the text on your device. |

### Speech-to-text (Whisper)

Transcription runs **on the operator's own infrastructure**, not a third-party
API, in the reference deployment. Audio is buffered to a temporary file for the
duration of transcription and then deleted. No third-party sub-processor is
involved. See the Privacy Policy for retention detail.

---

## 6. Infrastructure

| Component | Role | Data | Location |
| --- | --- | --- | --- |
| PostgreSQL | Primary database — accounts, conversations, messages | All stored account and conversation data | Operator-controlled |
| Redis | Cache, rate limiting, session and queue state | Transient keys, cached classifications | Operator-controlled |
| ChromaDB | Vector store for RAG | Document embeddings and excerpts | Operator-controlled |
| Unstructured API | Parsing uploaded documents into text | Contents of uploaded files | Operator-controlled in the reference deployment. **If the operator configures the hosted Unstructured service instead of a local container, uploaded file contents are disclosed to a third party and this list must be updated accordingly.** |

### Hosting provider

| | |
| --- | --- |
| **Purpose** | Running the Service. |
| **Data categories** | All data processed by the Service passes through hosting infrastructure. |
| **Provider** | [PLACEHOLDER: NAME YOUR HOSTING PROVIDER] |
| **Location** | [PLACEHOLDER: HOSTING REGION] |
| **Transfer mechanism** | [PLACEHOLDER: SCC / DPA REFERENCE] |

### Email delivery

| | |
| --- | --- |
| **Purpose** | Transactional email — verification, password reset, security notices. |
| **Data categories** | Email address, message content. |
| **Provider** | [PLACEHOLDER: NAME YOUR EMAIL PROVIDER — check email_service.py configuration] |
| **Location** | [PLACEHOLDER] |
| **Transfer mechanism** | [PLACEHOLDER: SCC / DPA REFERENCE] |

---

## 7. Analytics and error tracking

[PLACEHOLDER: If you add analytics, error tracking such as Sentry, or session
recording, they must be listed here. Session recording and product analytics are
frequently the most privacy-invasive tools in a stack, and in several
jurisdictions they require consent before they load — not merely disclosure.
Confirm whether the deployment includes `opik` or any other telemetry that
transmits data externally, and list it if so.]

---

## Changes to this list

We will update this page before engaging a new sub-processor that processes
personal data, or when an existing engagement changes materially.

**Notice period:** [PLACEHOLDER: STATE YOUR ADVANCE NOTICE PERIOD — commonly 30
days for business customers, with a right to object.]

To be notified of changes, contact us at [PLACEHOLDER: SUB-PROCESSOR NOTICE
CONTACT].

## Objecting to a sub-processor

Business customers with a data processing agreement in place may object to a new
sub-processor on reasonable data-protection grounds. Contact
[PLACEHOLDER: DPO / PRIVACY CONTACT]. If we cannot accommodate an objection, you
may terminate the affected subscription — see the Terms of Service for the
consequences of termination.

## Contact

- **Privacy contact:** [PLACEHOLDER: PRIVACY EMAIL]
- **Data Protection Officer:** [PLACEHOLDER: DPO NAME AND CONTACT, IF APPOINTED]
- **EU / UK representative:** [PLACEHOLDER: ARTICLE 27 REPRESENTATIVE, IF REQUIRED]
- **Grievance Officer (India, DPDP Act 2023):** [PLACEHOLDER: NAME AND CONTACT]
