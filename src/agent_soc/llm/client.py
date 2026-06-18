from __future__ import annotations

import json
from typing import Protocol

from openai import OpenAI

from agent_soc.config import AgentSOCSettings
from agent_soc.schemas import AttackHypothesis, Incident, NCEOutput


class NCEClient(Protocol):
    backend: str
    model: str

    def generate_hypotheses(self, incident: Incident) -> NCEOutput:
        ...


class MockNCEClient:
    backend = "mock"
    model = "mock-nce"

    def generate_hypotheses(self, incident: Incident) -> NCEOutput:
        alert = incident.source_alert
        hypotheses = [
            AttackHypothesis(
                hypothesis_id="H1",
                title="Credentialed lateral movement toward finance server",
                description=(
                    f"{alert.source_user} may be using valid Kerberos material from "
                    f"{alert.source_host} to reach {alert.target_host}."
                ),
                tactic="Lateral Movement",
                technique_id="T1021",
                technique_name="Remote Services",
                confidence=0.82,
                required_entities=[alert.source_user, alert.source_host, alert.target_host or ""],
                supporting_evidence=[
                    "Kerberos TGT request succeeded",
                    "Source workstation can reach finance server",
                    "Target host is high criticality",
                ],
                llm_backend=self.backend,
                model=self.model,
            ),
            AttackHypothesis(
                hypothesis_id="H2",
                title="Compromised user account with abnormal Kerberos access",
                description=(
                    f"{alert.source_user} may be compromised and requesting authentication "
                    "outside the expected finance baseline."
                ),
                tactic="Credential Access",
                technique_id="T1550",
                technique_name="Use Alternate Authentication Material",
                confidence=0.68,
                required_entities=[alert.source_user, "baseline-auth-finance"],
                supporting_evidence=["Successful authentication", "Finance baseline has partial coverage"],
                missing_context=["recent_user_authentication_baseline"],
                llm_backend=self.backend,
                model=self.model,
            ),
            AttackHypothesis(
                hypothesis_id="H3",
                title="External brute force against domain controller",
                description="An external source may be brute forcing domain authentication.",
                tactic="Credential Access",
                technique_id="T1110",
                technique_name="Brute Force",
                confidence=0.31,
                required_entities=["external_ip", "domain-controller-01"],
                supporting_evidence=["Authentication event observed"],
                missing_context=["external_source_ip"],
                llm_backend=self.backend,
                model=self.model,
            ),
        ]
        return NCEOutput(hypotheses=hypotheses, backend=self.backend, model=self.model)


class OpenAINCEClient:
    backend = "openai"

    def __init__(self, settings: AgentSOCSettings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAINCEClient")
        self.model = settings.llm_model
        self._client = OpenAI(api_key=settings.openai_api_key)

    def generate_hypotheses(self, incident: Incident) -> NCEOutput:
        system = (
            "You are the Narrative Construction Engine for an AgentSOC POC. "
            "Return exactly 3 cyber-defense hypotheses. Use only the sanitized incident data. "
            "Do not propose offensive steps. Anchor hypotheses to MITRE ATT&CK technique IDs."
        )
        user = json.dumps(incident.model_dump(mode="json"), indent=2, sort_keys=True)
        response = self._client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=NCEOutput,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("OpenAI response could not be parsed as NCEOutput")
        for hypothesis in parsed.hypotheses:
            hypothesis.llm_backend = self.backend
            hypothesis.model = self.model
        parsed.backend = self.backend
        parsed.model = self.model
        return parsed


class BudgetedNCEClient:
    def __init__(
        self,
        primary: NCEClient,
        *,
        max_calls: int,
        fallback: NCEClient | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback or MockNCEClient()
        self.max_calls = max_calls
        self.calls = 0
        self.fallbacks = 0

    @property
    def backend(self) -> str:
        return self.primary.backend

    @property
    def model(self) -> str:
        return self.primary.model

    def generate_hypotheses(self, incident: Incident) -> NCEOutput:
        if self.primary.backend == "openai":
            if self.calls >= self.max_calls:
                self.fallbacks += 1
                return self.fallback.generate_hypotheses(incident)
            self.calls += 1
        return self.primary.generate_hypotheses(incident)

    def usage(self) -> dict[str, int | str]:
        return {
            "backend": self.primary.backend,
            "model": self.primary.model,
            "calls": self.calls,
            "fallbacks": self.fallbacks,
            "max_calls": self.max_calls,
        }


def create_nce_client(settings: AgentSOCSettings) -> BudgetedNCEClient:
    if settings.llm_mode == "mock":
        primary: NCEClient = MockNCEClient()
    elif settings.llm_mode == "openai":
        primary = OpenAINCEClient(settings)
    elif settings.has_openai_key:
        primary = OpenAINCEClient(settings)
    else:
        primary = MockNCEClient()
    return BudgetedNCEClient(primary, max_calls=settings.max_llm_calls)
