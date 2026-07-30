import re
import uuid
from pathlib import Path
from urllib.parse import urlparse, quote
from xml.sax.saxutils import escape, quoteattr

from models.scenario_model import Assertion, Scenario, Transaction


class JmxGenerator:
    """Builds a valid Apache JMeter .jmx test plan from a Scenario object
    (thread config + business transactions + assertions) produced by the AI.
    """

    OUTPUT_DIR = Path("generated")

    def generate(self, scenario: Scenario, base_url: str, test_name: str = "AI Generated Test Plan") -> str:
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        print("BASE URL =", base_url)
       
        domain, protocol, port, base_path = self._split_url(base_url)

        samplers_xml = "\n".join(
            self._build_sampler_block(tx, domain, protocol, port, base_path, scenario.assertions)
            for tx in scenario.transactions
        )

        think_time_xml = self._build_think_time(
            scenario.configuration.thinkTimeMin,
            scenario.configuration.thinkTimeMax,
        )

        jmx = self._TEMPLATE.format(
            test_name=escape(test_name),
            threads=int(scenario.configuration.threads),
            ramp_up=int(scenario.configuration.rampUp),
            loops=int(scenario.configuration.loops),
            think_time=think_time_xml,
            samplers=samplers_xml,
        )

        filename = f"scenario_{uuid.uuid4().hex[:8]}.jmx"
        path = self.OUTPUT_DIR / filename
        path.write_text(jmx, encoding="utf-8")

        return str(path)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _split_url(base_url: str):
        parsed = urlparse(base_url or "")
        protocol = parsed.scheme or "http"
        domain = parsed.hostname or "localhost"
        
        # CORRECTION : utiliser le port réel de l'URL, ou déduire du protocole
        if parsed.port:
            port = parsed.port
        else:
            port = 443 if protocol == "https" else 80
            
        base_path = parsed.path.rstrip("/")
        return domain, protocol, port, base_path

    def _build_think_time(self, think_min: int, think_max: int) -> str:
        # UniformRandomTimer expects a base delay plus a random range added to it
        if think_min < 0:
            think_min = 0
        if think_max < think_min:
            think_max = think_min
        delay = think_min
        rng = think_max - think_min
        return f'''
      <UniformRandomTimer guiclass="UniformRandomTimerGui" testclass="UniformRandomTimer" testname="Think Time">
        <stringProp name="ConstantTimer.delay">{delay}</stringProp>
        <stringProp name="RandomTimer.range">{rng}</stringProp>
      </UniformRandomTimer>
      <hashTree/>'''

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path:
            return "/"
        normalized = re.sub(r"//+", "/", path)
        if not normalized.startswith("/"):
            normalized = "/" + normalized
        return normalized

    @staticmethod
    def _resolve_path_values(path: str, path_values) -> str:
        """
        Remplace les placeholders {paramName} du path par leurs valeurs
        concrètes issues de pathValues (ex: /pet/{petId} -> /pet/12).

        Les valeurs sont URL-encodées pour rester valides dans le chemin.
        """
        if not path:
            return path

        if not path_values:
            return path

        resolved = path

        for name, value in path_values.items():
            placeholder = "{" + str(name) + "}"
            if placeholder in resolved:
                resolved = resolved.replace(
                    placeholder,
                    quote(str(value), safe="")
                )

        return resolved

    def _build_sampler_block(
        self,
        tx: Transaction,
        domain: str,
        protocol: str,
        port: int,
        base_path: str,
        assertions,
    ) -> str:
        resolved_path = self._resolve_path_values(
            tx.path,
            getattr(tx, "pathValues", None)
        )

        if "{" in resolved_path or "}" in resolved_path:
            print(
                f"WARNING: unresolved path parameter(s) left in "
                f"'{resolved_path}' (missing pathValues from the AI/spec)."
            )

        full_path = self._normalize_path(
            f"{base_path}{resolved_path}" if base_path else resolved_path
        )
        body_xml, has_body = self._build_body(tx.body)
        headers_xml = self._build_headers(tx.headers)
        assertion_xml = self._build_assertions_for_path(tx.path, tx.method, assertions)

        return f'''
      <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname={quoteattr(tx.name)}>
        <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
          <collectionProp name="Arguments.arguments">
{body_xml}
          </collectionProp>
        </elementProp>
        <stringProp name="HTTPSampler.domain">{escape(domain)}</stringProp>
        <stringProp name="HTTPSampler.port">{port}</stringProp>
        <stringProp name="HTTPSampler.protocol">{escape(protocol)}</stringProp>
        <stringProp name="HTTPSampler.path">{escape(full_path)}</stringProp>
        <stringProp name="HTTPSampler.method">{escape(tx.method.upper())}</stringProp>
        <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
        <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
        <boolProp name="HTTPSampler.postBodyRaw">{"true" if has_body else "false"}</boolProp>
      </HTTPSamplerProxy>
      <hashTree>
{headers_xml}
{assertion_xml}
      </hashTree>'''

    @staticmethod
    def _build_headers(headers) -> str:
        if not headers:
            return ""

        entries = "\n".join(
            f'''            <elementProp name="" elementType="Header">
              <stringProp name="Header.name">{escape(str(k))}</stringProp>
              <stringProp name="Header.value">{escape(str(v))}</stringProp>
            </elementProp>'''
            for k, v in headers.items()
        )

        return f'''        <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager">
          <collectionProp name="HeaderManager.headers">
{entries}
          </collectionProp>
        </HeaderManager>
        <hashTree/>'''

    @staticmethod
    def _build_body(body):
        if not body:
            return "", False

        import json as _json
        payload = escape(_json.dumps(body))

        xml = f'''            <elementProp name="" elementType="HTTPArgument">
              <boolProp name="HTTPArgument.always_encode">false</boolProp>
              <stringProp name="Argument.value">{payload}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>'''
        return xml, True

    @staticmethod
    def _build_assertions_for_path(path: str, method: str, assertions) -> str:
        method = (method or "").upper()

        # Preferred: assertion explicitly tied to this transaction's method.
        matching = [
            a for a in assertions
            if a.path == path and (a.method or "").upper() == method
        ]

        if not matching:
            # Fallback for scenarios where the AI didn't specify a method
            # (older prompt/schema): match by path only, but never repeat
            # the same expected status twice within one sampler.
            seen_statuses = set()
            matching = []
            for a in assertions:
                if a.path == path and a.expectedStatus not in seen_statuses:
                    matching.append(a)
                    seen_statuses.add(a.expectedStatus)

        if not matching:
            return ""

        blocks = []
        for assertion in matching:
            blocks.append(f'''        <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="Response Code Assertion">
          <collectionProp name="Asserion.test_strings">
            <stringProp name="49586">{assertion.expectedStatus}</stringProp>
          </collectionProp>
          <stringProp name="Assertion.custom_message"></stringProp>
          <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
          <boolProp name="Assertion.assume_success">false</boolProp>
          <intProp name="Assertion.test_type">8</intProp>
        </ResponseAssertion>
        <hashTree/>''')

        return "\n".join(blocks)

    _TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{test_name}">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group">
        <intProp name="ThreadGroup.num_threads">{threads}</intProp>
        <intProp name="ThreadGroup.ramp_time">{ramp_up}</intProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller">
          <stringProp name="LoopController.loops">{loops}</stringProp>
          <boolProp name="LoopController.continue_forever">false</boolProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <stringProp name="filename"></stringProp>
        </ResultCollector>
        <hashTree/>
{think_time}
{samplers}
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
'''