type WorkflowIllustrationProps = {
  stage: string;
};

function SenseIllustration() {
  return (
    <svg className="workflow-illustration" viewBox="0 0 440 300" role="img" aria-labelledby="workflow-sense-title workflow-sense-desc">
      <title id="workflow-sense-title">Signal sensing workflow</title>
      <desc id="workflow-sense-desc">Attributable sources feed a reviewed signal cluster and strategic watchlist.</desc>
      <defs>
        <linearGradient id="sense-panel" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f8fbf9" />
          <stop offset="1" stopColor="#e9f4ed" />
        </linearGradient>
        <filter id="sense-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="10" stdDeviation="12" floodColor="#17382a" floodOpacity="0.12" />
        </filter>
      </defs>
      <rect x="22" y="26" width="396" height="248" rx="22" fill="url(#sense-panel)" stroke="#c9dacf" />
      <g filter="url(#sense-shadow)">
        <rect x="48" y="64" width="112" height="58" rx="13" fill="#ffffff" stroke="#cad8cf" />
        <circle cx="68" cy="83" r="7" fill="#62a97e" />
        <rect x="82" y="76" width="54" height="7" rx="3.5" fill="#b8c9be" />
        <rect x="64" y="96" width="72" height="6" rx="3" fill="#d5dfd8" />
        <rect x="48" y="138" width="112" height="58" rx="13" fill="#ffffff" stroke="#cad8cf" />
        <circle cx="68" cy="157" r="7" fill="#d99f5a" />
        <rect x="82" y="150" width="54" height="7" rx="3.5" fill="#b8c9be" />
        <rect x="64" y="170" width="72" height="6" rx="3" fill="#d5dfd8" />
      </g>
      <path d="M167 92 C205 92 198 130 232 130" fill="none" stroke="#71a789" strokeWidth="3" strokeLinecap="round" />
      <path d="M167 167 C205 167 198 142 232 142" fill="none" stroke="#71a789" strokeWidth="3" strokeLinecap="round" />
      <circle cx="246" cy="136" r="42" fill="#173f2e" />
      <circle cx="246" cy="136" r="25" fill="none" stroke="#9fd2b2" strokeWidth="2" strokeDasharray="4 5" />
      <circle cx="246" cy="136" r="7" fill="#b9e5c8" />
      <circle cx="228" cy="121" r="5" fill="#75b28d" />
      <circle cx="265" cy="119" r="5" fill="#d6a162" />
      <circle cx="265" cy="154" r="5" fill="#82c39d" />
      <path d="M289 136 H320" stroke="#71a789" strokeWidth="3" strokeLinecap="round" />
      <path d="M314 129 L322 136 L314 143" fill="none" stroke="#71a789" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <g filter="url(#sense-shadow)">
        <rect x="326" y="78" width="68" height="116" rx="16" fill="#ffffff" stroke="#cad8cf" />
        <text x="360" y="101" textAnchor="middle" className="workflow-svg__kicker">WATCHLIST</text>
        <rect x="340" y="116" width="40" height="8" rx="4" fill="#86b89a" />
        <rect x="340" y="133" width="32" height="7" rx="3.5" fill="#d5dfd8" />
        <rect x="340" y="150" width="37" height="7" rx="3.5" fill="#d5dfd8" />
        <rect x="340" y="167" width="25" height="7" rx="3.5" fill="#d5dfd8" />
      </g>
      <text x="104" y="221" textAnchor="middle" className="workflow-svg__label">Attributable sources</text>
      <text x="246" y="205" textAnchor="middle" className="workflow-svg__label">Reviewed signals</text>
      <text x="360" y="218" textAnchor="middle" className="workflow-svg__label">Strategic attention</text>
      <g transform="translate(48 238)">
        <circle cx="7" cy="7" r="7" fill="#dff1e5" />
        <path d="M4 7.2 6.2 9.3 10.5 4.8" fill="none" stroke="#2f7e50" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        <text x="22" y="11" className="workflow-svg__meta">Human review before promotion</text>
      </g>
    </svg>
  );
}

function InterpretIllustration() {
  return (
    <svg className="workflow-illustration" viewBox="0 0 440 300" role="img" aria-labelledby="workflow-interpret-title workflow-interpret-desc">
      <title id="workflow-interpret-title">Systems and scenario interpretation</title>
      <desc id="workflow-interpret-desc">Signals connect to drivers, stakeholder relationships, and four scenario worlds.</desc>
      <rect x="22" y="26" width="396" height="248" rx="22" fill="#f6faf7" stroke="#c9dacf" />
      <g className="workflow-svg__connections" fill="none" stroke="#9db9a8" strokeWidth="2.4">
        <path d="M92 92 C145 64 184 68 219 104" />
        <path d="M92 92 C128 123 160 148 216 148" />
        <path d="M98 191 C145 188 172 170 216 148" />
        <path d="M219 104 C264 76 299 84 338 110" />
        <path d="M216 148 C271 146 300 151 338 176" />
        <path d="M219 104 C260 118 290 138 338 176" />
      </g>
      <g>
        <circle cx="90" cy="92" r="27" fill="#17402e" />
        <text x="90" y="97" textAnchor="middle" className="workflow-svg__node workflow-svg__node--light">Signal</text>
        <circle cx="98" cy="191" r="27" fill="#e8f1eb" stroke="#a8bdae" />
        <text x="98" y="196" textAnchor="middle" className="workflow-svg__node">Stakeholder</text>
        <circle cx="219" cy="104" r="31" fill="#dcecdf" stroke="#8eb399" />
        <text x="219" y="109" textAnchor="middle" className="workflow-svg__node">Driver</text>
        <circle cx="216" cy="148" r="31" fill="#f3e7d7" stroke="#d6aa75" />
        <text x="216" y="153" textAnchor="middle" className="workflow-svg__node">Uncertainty</text>
      </g>
      <g transform="translate(302 74)">
        <rect width="83" height="125" rx="14" fill="#ffffff" stroke="#c9dacf" />
        <path d="M41.5 21 V103 M14 62 H69" stroke="#b8cbbf" strokeWidth="2" />
        <rect x="18" y="29" width="17" height="17" rx="4" fill="#dcecdf" />
        <rect x="48" y="29" width="17" height="17" rx="4" fill="#f0e2ce" />
        <rect x="18" y="76" width="17" height="17" rx="4" fill="#e7eef5" />
        <rect x="48" y="76" width="17" height="17" rx="4" fill="#d8e9dd" />
        <text x="41.5" y="116" textAnchor="middle" className="workflow-svg__kicker">4 WORLDS</text>
      </g>
      <text x="220" y="232" textAnchor="middle" className="workflow-svg__label">Competing interpretations remain visible</text>
      <g transform="translate(87 244)">
        <rect width="266" height="18" rx="9" fill="#eaf3ed" />
        <circle cx="12" cy="9" r="4" fill="#4d9a6b" />
        <text x="24" y="12" className="workflow-svg__meta">Cross-impact and implications stay traceable</text>
      </g>
    </svg>
  );
}

function DecideIllustration() {
  return (
    <svg className="workflow-illustration" viewBox="0 0 440 300" role="img" aria-labelledby="workflow-decide-title workflow-decide-desc">
      <title id="workflow-decide-title">Integrated option comparison</title>
      <desc id="workflow-decide-desc">Three options are compared across evidence, risk, stakeholder support, and scenario robustness.</desc>
      <rect x="22" y="26" width="396" height="248" rx="22" fill="#f7faf8" stroke="#c9dacf" />
      <g transform="translate(50 57)">
        <rect width="340" height="172" rx="16" fill="#ffffff" stroke="#c9dacf" />
        <rect width="340" height="38" rx="16" fill="#173d2c" />
        <path d="M0 22 Q0 38 16 38 H324 Q340 38 340 22" fill="#173d2c" />
        <text x="18" y="24" className="workflow-svg__header-label">OPTION COMPARISON</text>
        <text x="223" y="24" className="workflow-svg__header-label">EVIDENCE</text>
        <text x="286" y="24" className="workflow-svg__header-label">ROBUST</text>
        <g transform="translate(14 52)">
          <rect width="312" height="31" rx="8" fill="#e8f3eb" />
          <circle cx="15" cy="15.5" r="7" fill="#39845a" />
          <text x="31" y="20" className="workflow-svg__row-label">Controlled pilot</text>
          <rect x="178" y="10" width="55" height="10" rx="5" fill="#8bbba0" />
          <text x="280" y="20" textAnchor="middle" className="workflow-svg__score">8.2</text>
        </g>
        <g transform="translate(14 91)">
          <rect width="312" height="31" rx="8" fill="#f5f7f5" />
          <circle cx="15" cy="15.5" r="7" fill="#d49b5d" />
          <text x="31" y="20" className="workflow-svg__row-label">Enterprise rollout</text>
          <rect x="178" y="10" width="41" height="10" rx="5" fill="#c3d1c8" />
          <text x="280" y="20" textAnchor="middle" className="workflow-svg__score">6.4</text>
        </g>
        <g transform="translate(14 130)">
          <rect width="312" height="31" rx="8" fill="#f5f7f5" />
          <circle cx="15" cy="15.5" r="7" fill="#8ca5bd" />
          <text x="31" y="20" className="workflow-svg__row-label">Hold and monitor</text>
          <rect x="178" y="10" width="31" height="10" rx="5" fill="#c3d1c8" />
          <text x="280" y="20" textAnchor="middle" className="workflow-svg__score">5.8</text>
        </g>
      </g>
      <g transform="translate(60 239)">
        <circle cx="8" cy="8" r="8" fill="#f6e6d2" />
        <path d="M8 4.5V9" stroke="#a86c31" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="8" cy="12" r="1" fill="#a86c31" />
        <text x="24" y="12" className="workflow-svg__meta">3 unresolved issues remain visible to the authority</text>
      </g>
    </svg>
  );
}

function ActIllustration() {
  return (
    <svg className="workflow-illustration" viewBox="0 0 440 300" role="img" aria-labelledby="workflow-act-title workflow-act-desc">
      <title id="workflow-act-title">Accountable action roadmap</title>
      <desc id="workflow-act-desc">A decision becomes owned actions, milestones, and an adaptive signpost.</desc>
      <rect x="22" y="26" width="396" height="248" rx="22" fill="#f7faf8" stroke="#c9dacf" />
      <path d="M68 168 H367" stroke="#b8cbbf" strokeWidth="5" strokeLinecap="round" />
      <g>
        <circle cx="92" cy="168" r="15" fill="#17402e" />
        <path d="M86 168 90 172 98 163" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="190" cy="168" r="15" fill="#5c9f75" />
        <circle cx="288" cy="168" r="15" fill="#e0b171" />
        <circle cx="367" cy="168" r="15" fill="#ffffff" stroke="#a8bdae" strokeWidth="3" />
      </g>
      <g className="workflow-svg__milestone">
        <rect x="57" y="69" width="108" height="65" rx="13" fill="#ffffff" stroke="#cad8cf" />
        <text x="72" y="91" className="workflow-svg__kicker">OWNER</text>
        <circle cx="77" cy="111" r="9" fill="#dcecdf" />
        <rect x="93" y="104" width="52" height="8" rx="4" fill="#b8c9be" />
        <rect x="93" y="117" width="37" height="6" rx="3" fill="#d5dfd8" />
      </g>
      <g>
        <rect x="171" y="83" width="106" height="51" rx="13" fill="#ffffff" stroke="#cad8cf" />
        <text x="187" y="104" className="workflow-svg__kicker">MILESTONE</text>
        <rect x="187" y="113" width="72" height="8" rx="4" fill="#83b796" />
      </g>
      <g>
        <rect x="294" y="66" width="94" height="69" rx="13" fill="#173d2c" />
        <text x="309" y="88" className="workflow-svg__kicker workflow-svg__kicker--light">SIGNPOST</text>
        <path d="M313 115 C328 97 339 121 353 102 C362 91 371 101 378 93" fill="none" stroke="#a8d7b8" strokeWidth="2.6" strokeLinecap="round" />
      </g>
      <g transform="translate(64 211)">
        <rect width="305" height="33" rx="10" fill="#edf4ef" />
        <text x="16" y="21" className="workflow-svg__row-label">Review condition</text>
        <text x="134" y="21" className="workflow-svg__meta">Reassess when adoption exceeds threshold</text>
      </g>
      <text x="92" y="198" textAnchor="middle" className="workflow-svg__label">Commit</text>
      <text x="190" y="198" textAnchor="middle" className="workflow-svg__label">Implement</text>
      <text x="288" y="198" textAnchor="middle" className="workflow-svg__label">Monitor</text>
      <text x="367" y="198" textAnchor="middle" className="workflow-svg__label">Review</text>
    </svg>
  );
}

function LearnIllustration() {
  return (
    <svg className="workflow-illustration" viewBox="0 0 440 300" role="img" aria-labelledby="workflow-learn-title workflow-learn-desc">
      <title id="workflow-learn-title">Organisational learning loop</title>
      <desc id="workflow-learn-desc">Expected and actual outcomes are compared, converted into lessons, and fed into future sensing.</desc>
      <rect x="22" y="26" width="396" height="248" rx="22" fill="#f7faf8" stroke="#c9dacf" />
      <g transform="translate(52 61)">
        <rect width="146" height="105" rx="15" fill="#ffffff" stroke="#cad8cf" />
        <text x="17" y="25" className="workflow-svg__kicker">OUTCOME REVIEW</text>
        <path d="M22 79 L52 58 L78 67 L106 39 L127 48" fill="none" stroke="#c7d2ca" strokeWidth="3" strokeLinecap="round" />
        <path d="M22 87 L52 72 L78 75 L106 57 L127 62" fill="none" stroke="#4b9668" strokeWidth="3" strokeLinecap="round" />
        <circle cx="106" cy="57" r="5" fill="#4b9668" />
        <text x="17" y="98" className="workflow-svg__meta">Expected vs actual</text>
      </g>
      <path d="M204 112 H234" stroke="#71a789" strokeWidth="3" strokeLinecap="round" />
      <path d="M228 105 L236 112 L228 119" fill="none" stroke="#71a789" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <g transform="translate(242 61)">
        <rect width="146" height="105" rx="15" fill="#173d2c" />
        <text x="17" y="25" className="workflow-svg__kicker workflow-svg__kicker--light">LESSON</text>
        <rect x="17" y="41" width="110" height="8" rx="4" fill="#8bc3a0" />
        <rect x="17" y="58" width="96" height="7" rx="3.5" fill="#759d84" />
        <rect x="17" y="74" width="77" height="7" rx="3.5" fill="#759d84" />
        <circle cx="120" cy="84" r="11" fill="#b8e0c6" />
        <path d="M115 84 119 88 126 79" fill="none" stroke="#17402e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </g>
      <path d="M319 176 C319 242 112 247 112 182" fill="none" stroke="#8db39a" strokeWidth="3" strokeDasharray="6 7" strokeLinecap="round" />
      <path d="M104 190 L112 180 L120 190" fill="none" stroke="#8db39a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <g transform="translate(122 207)">
        <rect width="197" height="38" rx="12" fill="#e8f2eb" />
        <circle cx="21" cy="19" r="9" fill="#4b9668" />
        <path d="M17 19 20 22 25 16" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        <text x="39" y="16" className="workflow-svg__row-label">Reusable memory</text>
        <text x="39" y="29" className="workflow-svg__meta">Feeds the next strategic decision</text>
      </g>
    </svg>
  );
}

export function WorkflowIllustration({ stage }: WorkflowIllustrationProps) {
  switch (stage) {
    case "interpret":
      return <InterpretIllustration />;
    case "decide":
      return <DecideIllustration />;
    case "act":
      return <ActIllustration />;
    case "learn":
      return <LearnIllustration />;
    case "sense":
    default:
      return <SenseIllustration />;
  }
}

export function ForesightDecisionTrace() {
  return (
    <svg className="capability-trace-illustration" viewBox="0 0 620 260" role="img" aria-labelledby="foresight-trace-title foresight-trace-desc">
      <title id="foresight-trace-title">Foresight-to-decision trace</title>
      <desc id="foresight-trace-desc">A signal is interpreted through a system and scenarios before informing a governed decision.</desc>
      <defs>
        <linearGradient id="trace-line" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#8cd3a5" />
          <stop offset="1" stopColor="#d2b06e" />
        </linearGradient>
      </defs>
      <path d="M88 130 H532" stroke="url(#trace-line)" strokeWidth="4" strokeLinecap="round" />
      <g className="capability-trace__stage" transform="translate(44 80)">
        <rect width="92" height="100" rx="18" fill="#285c44" stroke="#4b7a61" />
        <circle cx="46" cy="31" r="15" fill="#92cfaa" />
        <circle cx="46" cy="31" r="6" fill="#17382a" />
        <text x="46" y="65" textAnchor="middle">SIGNAL</text>
        <text x="46" y="82" textAnchor="middle" className="capability-trace__sub">Attributable</text>
      </g>
      <g className="capability-trace__stage" transform="translate(190 80)">
        <rect width="92" height="100" rx="18" fill="#285c44" stroke="#4b7a61" />
        <circle cx="34" cy="28" r="7" fill="#92cfaa" />
        <circle cx="58" cy="27" r="7" fill="#c4a36a" />
        <circle cx="46" cy="45" r="7" fill="#86aebf" />
        <path d="M38 31 43 40 M54 32 49 40" stroke="#d9ecdf" strokeWidth="2" />
        <text x="46" y="65" textAnchor="middle">SYSTEM</text>
        <text x="46" y="82" textAnchor="middle" className="capability-trace__sub">Relationships</text>
      </g>
      <g className="capability-trace__stage" transform="translate(336 80)">
        <rect width="92" height="100" rx="18" fill="#285c44" stroke="#4b7a61" />
        <path d="M46 17 V49 M27 33 H65" stroke="#d9ecdf" strokeWidth="2" />
        <rect x="28" y="18" width="13" height="11" rx="3" fill="#92cfaa" />
        <rect x="51" y="18" width="13" height="11" rx="3" fill="#c4a36a" />
        <rect x="28" y="38" width="13" height="11" rx="3" fill="#86aebf" />
        <rect x="51" y="38" width="13" height="11" rx="3" fill="#76b88f" />
        <text x="46" y="65" textAnchor="middle">SCENARIO</text>
        <text x="46" y="82" textAnchor="middle" className="capability-trace__sub">Uncertainty</text>
      </g>
      <g className="capability-trace__stage capability-trace__stage--decision" transform="translate(482 70)">
        <rect width="100" height="120" rx="20" fill="#f2f8f4" />
        <circle cx="50" cy="33" r="17" fill="#17382a" />
        <path d="M42 33 48 39 59 25" fill="none" stroke="#a9dbbd" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <text x="50" y="73" textAnchor="middle">DECISION</text>
        <text x="50" y="91" textAnchor="middle" className="capability-trace__sub">Human authority</text>
      </g>
      <g fill="#d7eadf">
        <circle cx="159" cy="130" r="6" />
        <circle cx="305" cy="130" r="6" />
        <circle cx="451" cy="130" r="6" />
      </g>
      <text x="310" y="228" textAnchor="middle" className="capability-trace__caption">Every link remains inspectable, attributable, and exportable</text>
    </svg>
  );
}
