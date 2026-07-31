---
title: Privacy Policy
version: 1.0.0
effective_date: "[PLACEHOLDER: EFFECTIVE DATE]"
last_updated: "[PLACEHOLDER: LAST UPDATED DATE]"
---

# Privacy Policy

**Version 1.0.0** — Effective [PLACEHOLDER: EFFECTIVE DATE]

> **This document is a thorough draft, not legal advice.** Have qualified counsel
> review it before launch. Every bracketed `[PLACEHOLDER]` must be replaced with a
> real value, and every statement below must be re-verified against the deployment
> you actually run before you publish it.

This policy explains what personal data InfiChat ("the Service") collects, why,
who it is disclosed to, how long it is kept, and what you can do about it. It
forms part of our [Terms of Service](/legal/terms).

The controller of your personal data is [PLACEHOLDER: LEGAL ENTITY NAME],
[PLACEHOLDER: REGISTERED ADDRESS], [PLACEHOLDER: JURISDICTION OF INCORPORATION]
("we", "us", "our").

## The short version

- **Your prompts leave our infrastructure.** Every message you send is
  transmitted to a third-party model provider for inference. This is how the
  Service works, and it is the most important thing on this page. See
  [section 4](#4-who-we-disclose-data-to) and
  [Sub-processors](/legal/sub-processors).
- We store your conversations so you can return to them. You can delete them.
- We do not sell your personal data.
- Automated redaction of personal data in prompts is **available but off by
  default** — see [section 7.2](#72-pii-redaction).
- You can request access to, correction of, or deletion of your data at any time
  — see [section 8](#8-your-rights).

---

## 1. Scope, and what "self-hosted" changes

InfiChat is a self-hostable platform. This policy describes the instance operated
by us at [PLACEHOLDER: SERVICE URL].

**If you are using an instance operated by someone else, this policy is not the
one that governs you.** That operator is the controller of your data, they choose
which model and search providers to route your prompts to, and you should ask
them for their own privacy policy.

---

## 2. What personal data we collect

We collect the following categories of personal data:

### 2.1 Account and authentication data

- **Email address**, display name, and profile photo URL when you register or sign
  in with Google.
- **Password hash** when you register with email and password. We do not store
  passwords in plain text, and we never receive your Google password when you
  sign in with Google.
- **Account identifiers**, creation timestamps, and subscription status.

### 2.2 Payment and billing data

- **Billing name**, email address, billing address, and payment method details
  when you subscribe to a paid plan.
- **Transaction history** including dates, amounts, and subscription changes.

**Full card numbers are transmitted directly to our payment processor (Stripe)
and are never received or stored by us.** See
[Sub-processors](/legal/sub-processors) for Stripe's role.

### 2.3 Usage data — this is the most important category

- **Prompts, queries, and conversation history** — every message you send to the
  Service, including follow-up messages in a conversation.
- **Uploaded files** when you use document analysis or retrieval-augmented
  generation (RAG). This includes file names, file contents, and the text we
  extract from them for embedding.
- **Search queries** derived from your prompts when the Service automatically or
  at your request performs a web search for grounding.
- **Generated responses** — the text, code, and other content produced by the
  model in reply to your prompts.
- **Conversation metadata** — timestamps, session identifiers, feature usage
  (deep research, deep thinking, code generation), and model parameters.

**Every prompt you send is transmitted to a third-party AI provider for
inference.** This is how the Service works. See [section 4](#4-who-we-disclose-data-to)
and [Sub-processors](/legal/sub-processors) for detail.

### 2.4 Technical and diagnostic data

- **IP address**, browser user agent, and device type when you connect to the
  Service.
- **Session identifiers** and authentication tokens.
- **Error logs and diagnostic information** when something goes wrong, which may
  include snippets of your query or the system state at the time of the error.

[PLACEHOLDER: IF YOU USE ANALYTICS OR SESSION-RECORDING TOOLS, LIST THEM HERE AND
IN THE SUB-PROCESSORS PAGE. Examples: product analytics, error tracking, session
replay. Many of these tools are invasive and require consent before they load —
not merely disclosure after the fact.]

### 2.5 Data we do not collect

- **Full card numbers.** Your card is handled by Stripe and never passes through
  our systems.
- **OAuth passwords.** When you sign in with Google, we receive a token but never
  your Google password.

---

## 3. Why we collect it (lawful basis and purpose)

We process your personal data on the following lawful bases:

### 3.1 Contract performance

To provide the Service you registered for. This includes:

- Maintaining your account and authenticating you.
- Routing your prompts to model providers and returning responses.
- Storing your conversation history so you can return to it.
- Processing payments for paid subscriptions.

**Lawful basis:** performance of the contract between you and us (GDPR Art. 6(1)(b);
UK-GDPR Art. 6(1)(b); equivalent provisions under other frameworks).

### 3.2 Consent

For processing that requires your explicit agreement:

- **Disclosure of prompts to third-party AI providers.** The Service's core
  function is transmitting your prompts to external model providers for inference
  and returning their responses. This involves international transfer and
  disclosure to sub-processors. We collect your consent at registration and, where
  policies change materially, through a blocking re-consent mechanism.
- **Uploads containing third-party personal data.** If you upload documents
  containing other people's personal data, you are the controller and you instruct
  us to process it. You must have a lawful basis to give us that instruction.
- [PLACEHOLDER: IF YOU USE INVASIVE ANALYTICS OR SESSION RECORDING, STATE THAT
  CONSENT IS COLLECTED BEFORE THOSE TOOLS LOAD. Many jurisdictions require this.]

**Lawful basis:** consent (GDPR Art. 6(1)(a) and, for special-category data or
sensitive data under other frameworks, Art. 9(2)(a) or equivalent).

You may withdraw consent at any time by closing your account or contacting us.
Withdrawal does not affect the lawfulness of processing before withdrawal.

### 3.3 Legitimate interests

For operational, security, and improvement purposes that do not override your
rights:

- **Fraud prevention and security monitoring** — detecting credential stuffing,
  rate-limit abuse, and malicious activity.
- **Technical diagnostics** — investigating errors and service degradation.
- **Aggregate usage analytics** — understanding which features are used and how
  the Service performs, in a form that does not identify you.

**Lawful basis:** legitimate interests (GDPR Art. 6(1)(f); UK-GDPR Art. 6(1)(f);
equivalent provisions under other frameworks).

Where we rely on legitimate interests, you have the right to object — see
[section 8](#8-your-rights).

### 3.4 Legal obligations

To comply with laws that require us to retain or disclose data:

- Responding to valid legal process (court orders, subpoenas, warrants).
- Complying with tax, accounting, and financial-reporting obligations.
- Reporting child sexual abuse material to the authorities as required by law.

**Lawful basis:** legal obligation (GDPR Art. 6(1)(c); UK-GDPR Art. 6(1)(c);
equivalent provisions under other frameworks).

---

## 4. Who we disclose data to

### 4.1 Third-party model providers (the most important disclosure)

**Every prompt you send is transmitted to a third-party AI provider for
inference.** This is the core function of the Service and the single most
substantive disclosure we make.

The providers we currently use are:

- **NVIDIA** (`integrate.api.nvidia.com`) — receives every chat message, deep
  research query, deep thinking query, and code generation request you submit.
  Prompts, conversation context sent with the prompt, retrieved document excerpts
  used to ground an answer, and system instructions are disclosed.
- **Voyage AI** (`api.voyageai.com`) — receives text extracted from documents you
  upload, and the text of queries run against them, for embedding generation.

See [Sub-processors](/legal/sub-processors) for detail on what each provider
receives, where they process it, and — critically — whether they may train on
your data. [PLACEHOLDER: THAT LAST FACT MUST BE STATED PLAINLY IN THE
SUB-PROCESSORS PAGE. Do not leave it unresolved.]

### 4.2 Payment processor

**Stripe** processes subscription payments. We disclose your billing name, email
address, billing address, and payment method details to them. Full card numbers
are transmitted directly to Stripe and never pass through our systems.

Stripe acts as an independent controller for certain fraud-prevention and
regulatory purposes, not solely as our processor. Their privacy notice governs
that activity.

### 4.3 Authentication provider

**Google** receives an authentication request when you sign in with Google. They
learn that you authenticated to this Service, and we receive your email address,
display name, and profile photo URL from the token you present. We do not receive
your Google password.

### 4.4 Search and content providers

When you use web search or the Service automatically escalates a query to search
for grounding:

- **SearXNG** (a local container in the reference deployment) forwards your search
  query to upstream search engines. Those engines are independent controllers we
  do not control, and your query reaches them with the server's IP address, not
  yours. [PLACEHOLDER: LIST THE ENGINES YOUR SEARXNG INSTANCE ACTUALLY QUERIES.]
- The Service fetches publicly available content from sources including
  `arxiv.org`, `en.wikipedia.org`, and general web pages returned by search.
  These are ordinary outbound requests for public documents. The originating IP
  address is that of the server, not yours.

[PLACEHOLDER: VERIFY WHETHER `api.airforce` IS STILL IN USE. If so, describe what
it receives and link its terms. If it cannot be verified, remove the dependency
from the code rather than listing an unknown third party.]

### 4.5 Speech services

**Microsoft Edge TTS** receives the text of assistant responses when you use
read-aloud. Browser-native speech synthesis is available as a fallback and keeps
the text on your device.

Speech-to-text transcription (Whisper) runs on our own infrastructure in the
reference deployment. Audio is buffered to a temporary file for the duration of
transcription and then deleted. No third-party sub-processor is involved for
transcription.

### 4.6 Infrastructure providers

[PLACEHOLDER: NAME YOUR HOSTING PROVIDER AND REGION. Example: "We host the
Service on [PROVIDER] in [REGION]. All data processed by the Service passes
through that infrastructure."]

[PLACEHOLDER: NAME YOUR EMAIL DELIVERY PROVIDER. Example: "We use [PROVIDER] to
send transactional email (verification, password reset, security notices). They
receive your email address and message content."]

### 4.7 Service providers we do not use

We do not share your data with:

- Advertising networks or data brokers.
- Social media platforms except as required to implement single sign-on.
- Third parties for their own marketing purposes.

**We do not sell your personal data.**

### 4.8 Legal disclosures

We may disclose personal data when required by law or when necessary to:

- Comply with valid legal process (court orders, subpoenas, warrants).
- Enforce our [Terms of Service](/legal/terms) or
  [Acceptable Use Policy](/legal/acceptable-use).
- Protect the rights, property, or safety of the Service, our users, or the
  public.
- Report child sexual abuse material to the relevant authorities.

Where legally permitted, we will notify you before disclosing your data in
response to legal process, unless notification is prohibited or would be futile.

---

## 5. International transfers

The Service processes data globally. Personal data may be transferred to and
processed in countries that do not provide the same level of data protection as
your own.

### 5.1 Transfers from the EEA, UK, and Switzerland

When we transfer personal data from the European Economic Area, United Kingdom,
or Switzerland to countries not recognized as providing adequate protection, we
rely on:

- **Standard Contractual Clauses** (SCCs) approved by the European Commission or
  the UK Information Commissioner's Office, incorporated into our agreements with
  sub-processors.
- [PLACEHOLDER: IF YOU USE OTHER MECHANISMS — such as the UK Extension to the EU-US
  Data Privacy Framework, or adequacy decisions for specific providers — STATE
  THEM HERE.]

You may request a copy of the SCCs we use by contacting
[PLACEHOLDER: PRIVACY EMAIL].

### 5.2 Transfers from other jurisdictions

[PLACEHOLDER: IF YOU SERVE USERS IN INDIA (DPDP 2023), BRAZIL (LGPD), SOUTH AFRICA
(POPIA), CANADA (PIPEDA), AUSTRALIA (APP), OR OTHER JURISDICTIONS WITH
CROSS-BORDER TRANSFER RULES, DESCRIBE YOUR COMPLIANCE MECHANISM HERE. Common
approaches: explicit consent for transfer, adequacy whitelists, or contractual
protections.]

---

## 6. How long we keep it

We retain personal data for as long as necessary to provide the Service and to
comply with legal obligations. Specific retention periods:

### 6.1 Account and conversation data

- **Active accounts:** We retain your account data and conversation history while
  your account is active and for [PLACEHOLDER: PERIOD, e.g. 90 days] after you
  close it, to allow for account recovery and to comply with legal obligations.
- **Deleted conversations:** When you delete a conversation, it is removed from
  your view immediately and permanently deleted from our systems within
  [PLACEHOLDER: PERIOD, e.g. 30 days].

### 6.2 Automatic data retention sweeps

We run automatic retention sweeps based on the retention policy configured by the
operator. Data older than the configured retention period is scrubbed or deleted.
[PLACEHOLDER: STATE YOUR DEFAULT RETENTION PERIOD. The code default in
`data_retention.py` is `policy.retention_days`, which is operator-configurable.]

### 6.3 Backups

Deleted data may persist in backups for up to [PLACEHOLDER: BACKUP RETENTION
PERIOD, e.g. 90 days]. Backups are not accessible through the Service and are
deleted on their scheduled rotation.

### 6.4 Legal holds

We may retain data longer when required by law, to comply with legal process, or
to defend legal claims.

### 6.5 Third-party retention

Sub-processors have their own retention policies. We cannot control how long they
keep data once it is disclosed to them. See the
[Sub-processors](/legal/sub-processors) page and each provider's own privacy
policy for detail.

[PLACEHOLDER: CONFIRM NVIDIA'S RETENTION POSTURE FOR THE API TIER YOU USE. Does
NVIDIA retain prompts? For how long? Do they use them for training? State this
plainly in the Sub-processors page and reference it here.]

---

## 7. Security and privacy-enhancing features

### 7.1 How we protect data

We implement technical and organizational measures to protect personal data
against unauthorized access, loss, alteration, and disclosure, including:

- **Encryption at rest** for stored data, with key rotation available via the
  privacy settings endpoint.
- **Encryption in transit** (HTTPS/TLS) for data moving between your device and
  our servers, and between our servers and sub-processors.
- **Access controls** restricting who within our organization can access personal
  data.
- **Authentication** via JWT tokens with expiry, issuer, audience, and algorithm
  validation.
- **Rate limiting** on authentication and write-heavy endpoints to mitigate abuse.

**However, no system is perfectly secure.** You are responsible for safeguarding
your password and for all activity under your account.

### 7.2 PII redaction

The Service includes a PII redaction feature that can automatically redact email
addresses and phone numbers from your prompts before they are transmitted to
third-party model providers.

**This feature is available but OFF by default.** To enable it, contact
[PLACEHOLDER: PRIVACY EMAIL OR LINK TO SETTINGS PAGE].

**Important limitations:**

- Redaction is not perfect. It uses pattern matching and may miss personal data
  in unusual formats or fail to redact data it was not designed to recognize
  (names, addresses, national identifiers, health records, biometric data, and
  other sensitive categories are not redacted).
- Redaction applies only to the text of your prompt. It does not redact personal
  data embedded in uploaded files, images, or structured data.
- Redaction happens before transmission to model providers, but we cannot redact
  data from their logs once it has been sent.

**If you need strong protection for personal data, do not include it in your
prompts or uploads.** See our [Acceptable Use Policy](/legal/acceptable-use),
section 2, for guidance on uploading sensitive data.

---

## 8. Your rights

Depending on where you are, you may have rights over your personal data. This
section describes those rights and how to exercise them.

### 8.1 Rights under GDPR, UK-GDPR, and similar frameworks

If you are in the European Economic Area, United Kingdom, Switzerland, or another
jurisdiction that grants data subject rights, you have:

- **Right of access** (Art. 15) — request a copy of the personal data we hold
  about you.
- **Right to rectification** (Art. 16) — correct inaccurate or incomplete data.
- **Right to erasure** (Art. 17) — request deletion of your data, subject to
  exceptions for legal obligations or legitimate interests.
- **Right to restriction** (Art. 18) — ask us to stop processing your data
  temporarily while a dispute is resolved.
- **Right to data portability** (Art. 20) — receive your data in a structured,
  commonly used, machine-readable format, and transmit it to another controller.
- **Right to object** (Art. 21) — object to processing based on legitimate
  interests or for direct marketing.
- **Right to withdraw consent** (Art. 7(3)) — withdraw consent at any time where
  processing is based on consent. Withdrawal does not affect the lawfulness of
  processing before withdrawal.
- **Right not to be subject to automated decision-making** (Art. 22) — request
  human review of decisions made solely by automated means that significantly
  affect you. The Service does not make such decisions.

You also have the right to lodge a complaint with your local data protection
authority if you believe we have breached data protection law.

### 8.2 Rights under California law (CCPA / CPRA)

If you are a California resident, you have:

- **Right to know** what personal information we collect, use, disclose, and sell.
- **Right to access** the specific pieces of personal information we hold about
  you.
- **Right to delete** your personal information, subject to exceptions.
- **Right to correct** inaccurate personal information.
- **Right to opt out of sale or sharing** for cross-context behavioral
  advertising. **We do not sell or share personal information for these purposes.**
- **Right to limit use of sensitive personal information.** Sensitive personal
  information (precise geolocation, account credentials with passwords, contents
  of communications) is not used for purposes beyond providing the Service.
- **Right to non-discrimination** for exercising your rights.

### 8.3 Rights under India's DPDP Act 2023

If you are a data principal in India, you have:

- **Right to access** a summary of the personal data we process and how we use it.
- **Right to correction** of inaccurate or incomplete data.
- **Right to erasure** when the data is no longer necessary or consent is
  withdrawn.
- **Right to nominate** another individual to exercise your rights on your behalf
  in case of death or incapacity.
- **Right to grievance redressal** through the Grievance Officer listed below.

### 8.4 Rights under other frameworks

[PLACEHOLDER: IF YOU SERVE USERS IN BRAZIL (LGPD), SOUTH AFRICA (POPIA), CANADA
(PIPEDA), AUSTRALIA (APP), OR OTHER JURISDICTIONS WITH DATA-SUBJECT RIGHTS,
SUMMARIZE THOSE RIGHTS HERE OR REFERENCE A JURISDICTION-SPECIFIC ANNEX.]

### 8.5 How to exercise your rights

To exercise any of these rights, contact us at [PLACEHOLDER: PRIVACY EMAIL] with:

- Your account email address.
- A description of the right you wish to exercise and what you are asking us to
  do.
- Enough information for us to verify your identity (we will not process requests
  from unverified accounts).

We aim to respond within [PLACEHOLDER: PERIOD — 30 days for GDPR, 45 days for
CCPA] of receiving a valid request. If we need more time or cannot fulfill the
request, we will tell you why.

**Grievance Officer (India, DPDP Act 2023):** [PLACEHOLDER: NAME, CONTACT EMAIL,
RESPONSE TIME TARGET]

---

## 9. Cookies, local storage, and third-party resources

### 9.1 What we store on your device

The Service stores authentication tokens and session state on your device so you
stay signed in and so your preferences persist between visits. This storage is
strictly necessary to provide the Service and does not require consent.

[PLACEHOLDER: IF YOU SET ANY NON-ESSENTIAL COOKIES OR LOCAL STORAGE — analytics,
A/B testing, session replay, advertising — LIST THEM HERE AND STATE THAT CONSENT
IS COLLECTED BEFORE THEY ARE SET. Non-essential storage requires prior consent in
the EEA and UK under the ePrivacy Directive, independently of GDPR. A disclosure
here is not a substitute for a consent banner that actually gates the load.]

### 9.2 Third-party resources loaded by the interface

The web interface loads fonts and icons from third-party content delivery networks
(`fonts.googleapis.com`, `fonts.gstatic.com`, `img.icons8.com`). Your browser
connects to those providers directly, which discloses your IP address and user
agent to them. We do not control what they log.

[PLACEHOLDER: SELF-HOSTING THESE ASSETS WOULD REMOVE THE DISCLOSURE ENTIRELY. In
the EEA, embedding Google Fonts from Google's CDN has been found to be an unlawful
transfer of the visitor's IP address in at least one national court decision.
Consider bundling the fonts and icons locally and deleting this subsection.]

### 9.3 Automated decision-making

We do not make decisions about you by solely automated means that have legal
effects or similarly significantly affect you.

Automated processing that does occur is limited to enforcing plan entitlements,
usage quotas, and rate limits — for example, declining a request because your plan
does not include a feature or because you have exceeded a rate limit. These
decisions are mechanical, reversible by upgrading or waiting, and do not profile
you.

Abuse enforcement under the [Acceptable Use Policy](/legal/acceptable-use) may be
triggered by automated signals, but suspension and termination decisions are
reviewed by a human, and you may appeal them — see that policy, section 5.1.

---

## 10. Children

We do not knowingly collect personal data from children below the age specified
in our [Terms of Service](/legal/terms), section 2. If you believe we have
collected data from a child without proper consent, contact us at
[PLACEHOLDER: PRIVACY EMAIL] and we will delete it.

---

## 11. Changes to this policy

We may update this policy to reflect changes in our practices, legal requirements,
or Service features.

**We will notify you of material changes** by email to the address associated with
your account, or through a prominent notice in the Service, at least
[PLACEHOLDER: NOTICE PERIOD, e.g. 30 days] before the change takes effect.

**Where a change alters what you have consented to — particularly the sub-processors
we use or the purposes for which we process your data — we will collect your
consent again before the change applies to you.** If you do not consent to the
new policy, you may close your account. Closure for that reason entitles you to a
pro-rata refund of any prepaid subscription fees covering the period after
closure.

You can see the version number and effective date of this policy at the top of
the page. Previous versions are available on request.

---

## 12. Contact and complaints

### 12.1 General privacy inquiries

For questions about this policy or how we handle your data:

**Email:** [PLACEHOLDER: PRIVACY EMAIL]

### 12.2 Data Protection Officer

[PLACEHOLDER: IF YOU HAVE APPOINTED A DPO, PROVIDE NAME AND CONTACT HERE. GDPR
Art. 37 requires a DPO for public authorities, for controllers/processors whose
core activities involve large-scale regular and systematic monitoring, or whose
core activities involve large-scale processing of special-category data. Many
smaller organizations are not required to appoint one.]

### 12.3 EU and UK representative (Article 27)

If you are in the European Economic Area or United Kingdom and we do not have an
establishment there, GDPR and UK-GDPR require us to appoint a representative you
can contact directly.

**EU Representative:** [PLACEHOLDER: IF REQUIRED UNDER GDPR ART. 27, PROVIDE NAME,
ADDRESS, AND CONTACT]

**UK Representative:** [PLACEHOLDER: IF REQUIRED UNDER UK-GDPR ART. 27, PROVIDE
NAME, ADDRESS, AND CONTACT]

### 12.4 Grievance Officer (India, DPDP Act 2023)

**Name:** [PLACEHOLDER: NAME]  
**Email:** [PLACEHOLDER: EMAIL]  
**Response time:** [PLACEHOLDER: e.g. 72 hours for acknowledgment, resolution
within the period specified by the Act]

### 12.5 Complaints to regulators

You have the right to lodge a complaint with a data protection authority. Contact
details for EU/EEA data protection authorities are available at
[https://edpb.europa.eu/about-edpb/about-edpb/members_en](https://edpb.europa.eu/about-edpb/about-edpb/members_en).
For the UK, contact the Information Commissioner's Office at
[https://ico.org.uk/make-a-complaint/](https://ico.org.uk/make-a-complaint/).

[PLACEHOLDER: IF YOU SERVE USERS IN OTHER JURISDICTIONS WITH REGULATORY COMPLAINT
MECHANISMS, LIST THE RELEVANT AUTHORITY AND LINK.]

---

**Last updated:** [PLACEHOLDER: LAST UPDATED DATE]
