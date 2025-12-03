import React, { useState } from 'react';
import { ArrowRight, ArrowDown, Search, Database, Brain, CheckCircle, Globe, FileText, Phone, Users, DollarSign, Target, MapPin, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';

const WorkflowVisual = () => {
  const [activePhase, setActivePhase] = useState(1);
  const [expandedProgram, setExpandedProgram] = useState(null);

  const phases = [
    {
      id: 1,
      name: "Discovery",
      color: "bg-blue-500",
      lightColor: "bg-blue-50",
      borderColor: "border-blue-500",
      icon: Search,
      description: "Navigate to health department pages and identify maternal health program links",
      steps: [
        "Load county URL from configuration",
        "Navigate: Main Site → Health Dept → Maternal/Child Health",
        "Collect all links matching maternal health keywords",
        "Store program URLs and navigation paths"
      ],
      output: "discovery_results.json with program URLs"
    },
    {
      id: 2,
      name: "Deep Extraction",
      color: "bg-green-500",
      lightColor: "bg-green-50",
      borderColor: "border-green-500",
      icon: Globe,
      description: "Scrape individual program pages for detailed content",
      steps: [
        "Fetch full HTML from each program URL",
        "Extract main content (remove nav/headers/footers)",
        "Identify contact info via regex patterns",
        "Collect PDF/form links for eligibility docs"
      ],
      output: "raw_content.json with full page text"
    },
    {
      id: 3,
      name: "LLM Structuring",
      color: "bg-purple-500",
      lightColor: "bg-purple-50",
      borderColor: "border-purple-500",
      icon: Brain,
      description: "Use LLM to extract structured fields from unstructured text",
      steps: [
        "Send content to GPT-4o-mini/Claude API",
        "Extract: program_name, type, eligibility, budget",
        "Identify funding sources and partners",
        "Classify program type (mental health, physical, etc.)"
      ],
      output: "structured_programs.csv with all fields"
    },
    {
      id: 4,
      name: "Validation",
      color: "bg-red-500",
      lightColor: "bg-red-50",
      borderColor: "border-red-500",
      icon: CheckCircle,
      description: "Quality scoring and human verification",
      steps: [
        "Calculate field completeness scores",
        "Measure actionability (eligibility + contact + application)",
        "Flag low-quality records for manual review",
        "Generate quality report with metrics"
      ],
      output: "Final dataset + quality_report.json"
    }
  ];

  const programTypes = [
    {
      type: "Maternal Mental Health",
      examples: ["PPD Screening", "Support Groups", "Perinatal Mood Disorders"],
      keywords: ["postpartum depression", "perinatal mood", "maternal mental health", "anxiety screening"],
      federalPrograms: ["Title V", "SAMHSA Block Grant"],
      color: "bg-pink-100 border-pink-400"
    },
    {
      type: "Physical Recovery",
      examples: ["Home Visits", "Pelvic Floor Therapy", "Maternal Mortality Reduction"],
      keywords: ["postpartum recovery", "home visiting", "maternal mortality", "childbirth follow-up"],
      federalPrograms: ["MIECHV", "Healthy Start"],
      color: "bg-orange-100 border-orange-400"
    },
    {
      type: "Lactation & OB/GYN Access",
      examples: ["Breastfeeding Support", "Prenatal Care", "OB-GYN Access"],
      keywords: ["lactation", "breastfeeding", "prenatal care", "OB-GYN", "WIC"],
      federalPrograms: ["WIC", "Title V"],
      color: "bg-yellow-100 border-yellow-400"
    },
    {
      type: "Family Planning",
      examples: ["Contraception", "Birth Spacing", "Reproductive Health"],
      keywords: ["family planning", "contraception", "reproductive health", "birth spacing"],
      federalPrograms: ["Title X", "Medicaid Family Planning"],
      color: "bg-green-100 border-green-400"
    },
    {
      type: "Case Management",
      examples: ["Healthy Start", "Black Infant Health", "High-Risk Pregnancy"],
      keywords: ["case management", "Healthy Start", "perinatal equity", "high-risk pregnancy"],
      federalPrograms: ["Healthy Start", "CA Black Infant Health"],
      color: "bg-purple-100 border-purple-400"
    },
    {
      type: "Home Visiting",
      examples: ["Nurse-Family Partnership", "Parents as Teachers", "Early Head Start"],
      keywords: ["home visiting", "nurse family", "parents as teachers", "early intervention"],
      federalPrograms: ["MIECHV", "Early Head Start"],
      color: "bg-blue-100 border-blue-400"
    }
  ];

  const navigationKeywords = {
    department: ["Health Department", "Health Services", "Public Health", "Health & Human Services", "HHS", "HHSA"],
    section: ["Maternal Health", "Women's Health", "Family Health", "Maternal Child Health", "MCH", "MCAH", "Perinatal"],
    program: ["Healthy Start", "WIC", "Home Visiting", "MIECHV", "Black Infant Health", "First 5", "Nurse-Family Partnership"]
  };

  const extractionSchema = [
    { category: "Program ID", fields: ["program_name", "program_type", "county", "target_population"], color: "bg-blue-100" },
    { category: "Resources", fields: ["budget", "funding_source", "partners", "performance_metrics"], color: "bg-green-100" },
    { category: "Actionability", fields: ["eligibility", "application_process", "contact_phone", "contact_email", "program_url"], color: "bg-yellow-100" }
  ];

  const pilotCounties = [
    { name: "San Diego", programs: 8, rationale: "Large county, comprehensive website, 8 programs in initial pilot", known: ["First 5", "Black Infant Health", "MCAH"] },
    { name: "Alameda", programs: 5, rationale: "Diverse population, strong public health infrastructure", known: ["Healthy Start", "WIC", "Home Visiting"] },
    { name: "Fresno", programs: 4, rationale: "Rural/urban mix, high maternal mortality focus", known: ["Perinatal Equity", "Title V"] },
    { name: "Sacramento", programs: 6, rationale: "State capital, well-documented programs", known: ["MCAH", "Nurse-Family Partnership"] },
    { name: "Kern", programs: 3, rationale: "Rural county, tests edge cases", known: ["WIC", "Home Visiting"] }
  ];

  const ActivePhaseIcon = phases[activePhase - 1].icon;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">iTREDS Maternal Health Workflow</h1>
          <p className="text-gray-600">Automated Data Collection for County-Level Maternal Health Programs</p>
        </div>

        {/* Provider & Budget Guardrails */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Globe className="w-5 h-5 text-blue-500" /> Provider Options
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">OpenAI (gpt-4o-mini)</span>
                <span className="text-gray-600">Best cost-efficiency for JSON extraction</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded">Anthropic</span>
                <span className="text-gray-600">Requires API access (Claude Pro UI alone is not enough)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">Ollama (Local)</span>
                <span className="text-gray-600">Free local model, slower initial downloads</span>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-emerald-500" /> $5 Budget Plan
            </h2>
            <ul className="list-disc ml-5 space-y-1 text-sm text-gray-700">
              <li>Disable deep subpage scraping for the first full run</li>
              <li>Limit input: ~10k–12k characters per county page</li>
              <li>Set model output max tokens ~1500</li>
              <li>Start with 5-county pilot; then scale to 58</li>
              <li>Set OpenAI monthly cap to $5 (optional daily cap)</li>
            </ul>
          </div>
        </div>

        {/* Why This Approach - Rationale Box */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-l-4 border-indigo-500 rounded-r-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-indigo-800 mb-3 flex items-center gap-2">
            <Target className="w-5 h-5" /> Why This Approach?
          </h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
              <div><strong>No existing database:</strong> County health program info is fragmented across thousands of sites</div>
            </div>
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
              <div><strong>Initial pilot failure:</strong> 14.7% actionability score - users couldn't find eligibility or how to apply</div>
            </div>
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
              <div><strong>LLM handles heterogeneity:</strong> Each county organizes info differently - rule-based scraping fails</div>
            </div>
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
              <div><strong>Workflow is the deliverable:</strong> Replicable methodology for future research on local gov data</div>
            </div>
          </div>
        </div>

        {/* Phase Navigation */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-2 bg-white rounded-xl p-2 shadow-lg">
            {phases.map((phase, index) => (
              <React.Fragment key={phase.id}>
                <button
                  onClick={() => setActivePhase(phase.id)}
                  className={`flex items-center gap-2 px-4 py-3 rounded-lg transition-all ${
                    activePhase === phase.id 
                      ? `${phase.color} text-white shadow-md` 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <phase.icon className="w-5 h-5" />
                  <span className="font-medium">{phase.name}</span>
                </button>
                {index < phases.length - 1 && (
                  <ArrowRight className="w-5 h-5 text-gray-400" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Active Phase Detail */}
        <div className={`${phases[activePhase - 1].lightColor} border-2 ${phases[activePhase - 1].borderColor} rounded-xl p-6 mb-8`}>
          <div className="flex items-start gap-4">
            <div className={`${phases[activePhase - 1].color} p-3 rounded-lg`}>
              <ActivePhaseIcon className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                Phase {activePhase}: {phases[activePhase - 1].name}
              </h3>
              <p className="text-gray-600 mb-4">{phases[activePhase - 1].description}</p>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-gray-700 mb-2">Process Steps:</h4>
                  <ol className="space-y-2">
                    {phases[activePhase - 1].steps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <span className={`${phases[activePhase - 1].color} text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0`}>
                          {idx + 1}
                        </span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <h4 className="font-semibold text-gray-700 mb-2">Output:</h4>
                  <div className="flex items-center gap-2 text-sm">
                    <FileText className="w-4 h-4 text-gray-500" />
                    <code className="bg-gray-100 px-2 py-1 rounded">{phases[activePhase - 1].output}</code>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Keywords */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Search className="w-5 h-5 text-blue-500" /> Navigation Keyword Hierarchy
          </h2>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {Object.entries(navigationKeywords).map(([level, keywords], idx) => (
              <React.Fragment key={level}>
                <div className="text-center">
                  <div className="text-xs font-semibold text-gray-500 uppercase mb-2">{level} Level</div>
                  <div className="flex flex-wrap gap-2 justify-center max-w-xs">
                    {keywords.map(kw => (
                      <span key={kw} className={`px-2 py-1 rounded text-xs ${
                        level === 'department' ? 'bg-blue-100 text-blue-700' :
                        level === 'section' ? 'bg-green-100 text-green-700' :
                        'bg-purple-100 text-purple-700'
                      }`}>
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
                {idx < 2 && <ArrowRight className="w-6 h-6 text-gray-400 hidden md:block" />}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Program Types Search Strategy */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-500" /> Maternal Health Program Search Strategy
          </h2>
          <p className="text-gray-600 mb-4 text-sm">Click each program type to see search keywords and federal program connections</p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {programTypes.map((prog, idx) => (
              <div 
                key={idx}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${prog.color} ${
                  expandedProgram === idx ? 'ring-2 ring-offset-2 ring-purple-400' : ''
                }`}
                onClick={() => setExpandedProgram(expandedProgram === idx ? null : idx)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-800">{prog.type}</h3>
                  {expandedProgram === idx ? 
                    <ChevronDown className="w-4 h-4 text-gray-500" /> : 
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  }
                </div>
                
                <div className="text-xs text-gray-600 mb-2">
                  Examples: {prog.examples.join(", ")}
                </div>
                
                {expandedProgram === idx && (
                  <div className="mt-3 pt-3 border-t border-gray-300 space-y-3">
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-1">Search Keywords:</div>
                      <div className="flex flex-wrap gap-1">
                        {prog.keywords.map(kw => (
                          <code key={kw} className="text-xs bg-white px-1.5 py-0.5 rounded">{kw}</code>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-1">Federal Programs:</div>
                      <div className="flex flex-wrap gap-1">
                        {prog.federalPrograms.map(fp => (
                          <span key={fp} className="text-xs bg-white px-1.5 py-0.5 rounded font-medium">{fp}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Search Heuristics & Link Scoring */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Search className="w-5 h-5 text-blue-500" /> Search Heuristics & Link Scoring
          </h2>
          <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-700">
            <div>
              <h3 className="font-semibold mb-2">Prioritized Link Patterns</h3>
              <ul className="list-disc ml-5 space-y-1">
                <li>URLs containing: <code>/mch</code>, <code>/mcah</code>, <code>/maternal</code>, <code>/perinatal</code>, <code>/family-health</code></li>
                <li>Program keywords in anchor text: WIC, Healthy Start, BIH, NFP, MIECHV</li>
                <li>Contact or Apply pages adjacent to program content</li>
                <li>PDFs titled “Eligibility”, “Application”, “Program Brochure”</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Filtering Rules</h3>
              <ul className="list-disc ml-5 space-y-1">
                <li>Ignore external social links; prefer county domains</li>
                <li>Prefer HTTPS and canonical (no tracking params)</li>
                <li>De-duplicate links by path and title</li>
                <li>Language variants: prefer English; follow “Español” if English lacks details</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Extraction Schema */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-green-500" /> Data Extraction Schema
          </h2>
          <div className="grid md:grid-cols-3 gap-4">
            {extractionSchema.map((cat, idx) => (
              <div key={idx} className={`${cat.color} rounded-lg p-4`}>
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  {cat.category === "Program ID" && <FileText className="w-4 h-4" />}
                  {cat.category === "Resources" && <DollarSign className="w-4 h-4" />}
                  {cat.category === "Actionability" && <Phone className="w-4 h-4" />}
                  {cat.category}
                </h3>
                <div className="space-y-2">
                  {cat.fields.map(field => (
                    <div key={field} className="bg-white rounded px-2 py-1 text-sm font-mono">
                      {field}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Pilot Counties */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-red-500" /> Pilot Counties (Phase 1)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100">
                  <th className="text-left p-3 rounded-tl-lg">County</th>
                  <th className="text-center p-3">Programs</th>
                  <th className="text-left p-3">Selection Rationale</th>
                  <th className="text-left p-3 rounded-tr-lg">Known Programs</th>
                </tr>
              </thead>
              <tbody>
                {pilotCounties.map((county, idx) => (
                  <tr key={idx} className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="p-3 font-medium">{county.name}</td>
                    <td className="p-3 text-center">
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs font-medium">
                        {county.programs}
                      </span>
                    </td>
                    <td className="p-3 text-gray-600">{county.rationale}</td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {county.known.map(prog => (
                          <span key={prog} className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs">
                            {prog}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quality Metrics */}
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" /> Quality Targets (vs. Pilot Results)
          </h2>
          <div className="grid md:grid-cols-4 gap-4">
            {[
              { metric: "Field Completeness", pilot: "47%", target: "70%", icon: FileText },
              { metric: "Contact Availability", pilot: "2.3%", target: "80%", icon: Phone },
              { metric: "Actionability Score", pilot: "14.7%", target: "60%", icon: Target },
              { metric: "Funding Info", pilot: "~0%", target: "50%", icon: DollarSign }
            ].map((m, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <m.icon className="w-4 h-4 text-gray-500" />
                  <span className="font-medium text-sm">{m.metric}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="text-center">
                    <div className="text-xs text-gray-500">Pilot</div>
                    <div className="text-lg font-bold text-red-500">{m.pilot}</div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                  <div className="text-center">
                    <div className="text-xs text-gray-500">Target</div>
                    <div className="text-lg font-bold text-green-500">{m.target}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Implementation Timeline */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Implementation Timeline</h2>
          <div className="flex items-center justify-between flex-wrap gap-4">
            {[
              { week: "1-2", task: "Develop scraper for 5 pilot counties", color: "bg-blue-500" },
              { week: "3-4", task: "Integrate LLM structuring", color: "bg-green-500" },
              { week: "5", task: "Quality validation & refinement", color: "bg-purple-500" },
              { week: "6", task: "Scale to remaining CA counties", color: "bg-red-500" }
            ].map((item, idx) => (
              <React.Fragment key={idx}>
                <div className="flex-1 min-w-48">
                  <div className={`${item.color} text-white text-center py-2 rounded-t-lg font-medium`}>
                    Week {item.week}
                  </div>
                  <div className="bg-gray-100 text-center py-3 px-2 rounded-b-lg text-sm">
                    {item.task}
                  </div>
                </div>
                {idx < 3 && <ArrowRight className="w-6 h-6 text-gray-400 hidden lg:block" />}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          iTREDS Maternal Health Workflow Documentation | December 2025
        </div>
      </div>
    </div>
  );
};

export default WorkflowVisual;