import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import {
  Cpu, Play, CheckCircle, AlertCircle, FileCode,
  Terminal, Zap, Code2, ListTree, ChevronRight, Eye, Download, Upload,
  Moon, Sun, Keyboard, BarChart3, Clock, TrendingUp, Users,
  Info, Globe, Shield, Server, X, MessageCircle, Send
} from 'lucide-react';
// Temporarily disabled to prevent crashes
// import MonacoAetherEditor from './components/MonacoAetherEditor';
import FlowVisualization from './components/FlowVisualization';
import ProfileViewer from './components/ProfileViewer';
import DebuggerPanel from './components/DebuggerPanel';
import CollaborationPanel from './components/CollaborationPanel';

// Simple code editor fallback
const SimpleCodeEditor = ({ value, onChange }) => (
  <textarea
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="w-full h-[400px] p-4 bg-slate-900 text-green-400 font-mono text-sm
               resize-none focus:outline-none focus:ring-2 focus:ring-cyan-500
               rounded-lg border border-slate-700"
    spellCheck={false}
  />
);

// Use proxy for all requests - bypasses Cloudflare cache
const API_BASE = 'https://api.neurodoc.app';
const ADMIN_KEY = 'NEURODOC-ADMIN-2025-MASTER';
// Example translations
const exampleTranslations = {
  'Εισαγωγικό Flow': 'Introductory Flow',
  'Βασικό flow με Guard -> Plan -> LLM': 'Basic flow with Guard -> Plan -> LLM',
  'AI Chef - Συνταγή': 'AI Chef - Recipe',
  'Culinary flow: Guard -> Plan -> Chef -> Summarize': 'Culinary flow: Guard -> Plan -> Chef -> Summarize',
  'Ασφαλής Συνομιλία': 'Safe Chat',
  'Απλό flow με Guard και LLM για safe chat': 'Simple flow with Guard and LLM for safe chat',
      'Molecular Lab - APEIRON': 'Molecular Lab - APEIRON',
      'Molecular gastronomy with scientific precision': 'Molecular gastronomy with scientific precision',
      'APEX Business Strategy': 'APEX Business Strategy',
      'Nobel-level strategic analysis with ROI projections': 'Nobel-level strategic analysis with ROI projections',
      'Oracle - Predictions': 'Oracle - Predictions',
      'OMNI-COMPUTE adversarial forecasting engine': 'OMNI-COMPUTE adversarial forecasting engine',
      'GAIA Brain - Assembly': 'GAIA Brain - Assembly',
      'Multi-agent panel with 12 neural archetypes': 'Multi-agent panel with 12 neural archetypes',
      'Full Consulting Pipeline': 'Full Consulting Pipeline',
      'Research -> Consult -> Market -> APEX pipeline': 'Research -> Consult -> Market -> APEX pipeline',
  'AI Chef - Συνταγή': 'AI Chef - Recipe',
  'Culinary flow: Guard -> Plan -> Chef -> Summarize': 'Culinary flow: Guard -> Plan -> Chef -> Summarize',
  'Ασφαλής Συνομιλία': 'Safe Chat',
  'Απλό flow με Guard και LLM για safe chat': 'Simple flow with Guard and LLM for safe chat',
      'Molecular Lab - APEIRON': 'Molecular Lab - APEIRON',
      'Molecular gastronomy with scientific precision': 'Molecular gastronomy with scientific precision',
      'APEX Business Strategy': 'APEX Business Strategy',
      'Nobel-level strategic analysis with ROI projections': 'Nobel-level strategic analysis with ROI projections',
      'Oracle - Predictions': 'Oracle - Predictions',
      'OMNI-COMPUTE adversarial forecasting engine': 'OMNI-COMPUTE adversarial forecasting engine',
      'GAIA Brain - Assembly': 'GAIA Brain - Assembly',
      'Multi-agent panel with 12 neural archetypes': 'Multi-agent panel with 12 neural archetypes',
      'Full Consulting Pipeline': 'Full Consulting Pipeline',
      'Research -> Consult -> Market -> APEX pipeline': 'Research -> Consult -> Market -> APEX pipeline',
  'Ερευνητικό Flow': 'Research Flow',
  'Πολύπλοκο flow με πολλαπλά στάδια': 'Complex flow with multiple stages',
  'Ελληνικό Εκπαιδευτικό Flow': 'Greek Educational Flow',
  'Ειδικό flow για ελληνικό εκπαιδευτικό υλικό': 'Specialized flow for Greek educational content',
  'Εξαγωγή Δεδομένων': 'Data Extraction',
  'Flow για structured data extraction': 'Flow for structured data extraction',
  'Πλήρης Ανάλυση': 'Full Analysis',
  'Flow με ανάλυση και περίληψη': 'Flow with analysis and summary',
  'Εξαγωγή Δεδομένων': 'Data Extraction',
  'Flow για structured data extraction': 'Flow for structured data extraction',
  'Ερευνητικό Flow': 'Research Flow',
  'Πολύπλοκο flow με πολλαπλά στάδια': 'Complex flow with multiple stages',
  'Ελληνικό Εκπαιδευτικό Flow': 'Greek Education Flow',
  'Ειδικό flow για ελληνικό εκπαιδευτικό υλικό': 'Specialized flow for Greek educational content',
  'Enterprise Document Processing': 'Enterprise Document Processing',
  'Flow για επεξεργασία εταιρικών εγγράφων': 'Flow for enterprise document processing',
};
const t = (text, lang) => lang === 'en' ? (exampleTranslations[text] || text) : text;


// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('FlowVisualization Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-red-50 border border-red-300 rounded-lg p-4">
          <p className="text-red-700 text-sm">
            Flow visualization temporarily unavailable. The flow will still execute normally.
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}

// Diff Modal component
const DiffModal = ({ isOpen, onClose, diffData, onAccept }) => {
  if (!isOpen || !diffData) return null;

  // Safe destructuring with defaults
  const diff = diffData.diff || {};
  const optimizations_applied = diffData.optimizations_applied || {};
  const changes = diff.changes || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-2xl border border-purple-500 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-purple-400 flex items-center gap-2">
                <CheckCircle className="w-6 h-6" />
                Optimization Preview
              </h2>
              <p className="text-slate-400 text-sm mt-1">
                Review changes before applying to your code
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="p-4 bg-slate-700 border-b border-slate-600 grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-green-400 font-bold text-2xl">+{diff.lines_added || 0}</div>
            <div className="text-slate-400 text-xs">Lines Added</div>
          </div>
          <div className="text-center">
            <div className="text-red-400 font-bold text-2xl">-{diff.lines_removed || 0}</div>
            <div className="text-slate-400 text-xs">Lines Removed</div>
          </div>
          <div className="text-center">
            <div className="text-cyan-400 font-bold text-2xl">{(optimizations_applied.caching || 0) + (optimizations_applied.model_downgrades || 0) + (optimizations_applied.parallelization || 0)}</div>
            <div className="text-slate-400 text-xs">Optimizations</div>
          </div>
        </div>

        {/* Diff Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="space-y-4">
            {/* Changes List */}
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-bold text-cyan-400 mb-3">Changes:</h3>
              {changes.length > 0 ? (
                <div className="space-y-2 font-mono text-sm">
                  {changes.slice(0, 20).map((change, i) => (
                    <div
                      key={i}
                      className={`p-2 rounded ${
                        change.type === 'added'
                          ? 'bg-green-900/30 text-green-300'
                          : 'bg-red-900/30 text-red-300'
                      }`}
                    >
                      <span className="font-bold mr-2">
                        {change.type === 'added' ? '+' : '-'}
                      </span>
                      {change.content || 'No content'}
                    </div>
                  ))}
                  {changes.length > 20 && (
                    <div className="text-slate-400 text-center text-xs py-2">
                      ... and {changes.length - 20} more changes
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-slate-400 text-sm">No changes detected</div>
              )}
            </div>

            {/* Optimizations Applied */}
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-bold text-purple-400 mb-3">Optimizations Applied:</h3>
              <div className="space-y-2 text-sm">
                {(optimizations_applied.caching || 0) > 0 && (
                  <div className="flex items-center gap-2 text-cyan-300">
                    <Clock className="w-4 h-4" />
                    <span>{optimizations_applied.caching} cache node(s) added</span>
                  </div>
                )}
                {(optimizations_applied.model_downgrades || 0) > 0 && (
                  <div className="flex items-center gap-2 text-green-300">
                    <TrendingUp className="w-4 h-4" />
                    <span>{optimizations_applied.model_downgrades} model(s) downgraded for cost savings</span>
                  </div>
                )}
                {(optimizations_applied.parallelization || 0) > 0 && (
                  <div className="flex items-center gap-2 text-purple-300">
                    <Zap className="w-4 h-4" />
                    <span>Parallelization enabled</span>
                  </div>
                )}
                {(optimizations_applied.caching || 0) === 0 &&
                 (optimizations_applied.model_downgrades || 0) === 0 &&
                 (optimizations_applied.parallelization || 0) === 0 && (
                  <div className="text-slate-400 text-sm">No optimizations applied</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-slate-700 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onAccept}
            className="flex-1 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <CheckCircle className="w-5 h-5" />
            Apply Changes
          </button>
        </div>
      </div>
    </div>
  );
};

// AI Insights Panel component
const AIInsightsPanel = ({ analysis }) => {
  if (!analysis) return null;

  // Safe access with null checks
  const current = analysis.current_performance || {};
  const predicted = analysis.predicted_performance || {};
  const improvement = predicted.improvement || {};
  const issues = analysis.issues || {};

  // Ensure arrays exist
  const bottlenecks = issues.bottlenecks || [];
  const cachingOps = issues.caching_opportunities || [];
  const costOpts = issues.cost_optimizations || [];
  const aiSuggestions = analysis.ai_suggestions || [];

  return (
    <div className="space-y-6">
      {/* Performance Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Current Performance */}
        <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
          <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Current Performance
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400 text-sm">Duration:</span>
              <span className="text-white font-bold">{(current.duration || 0).toFixed(2)}s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 text-sm">Cost:</span>
              <span className="text-white font-bold">${(current.cost || 0).toFixed(4)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 text-sm">Efficiency:</span>
              <span className="text-white font-bold">{current.efficiency_score || 0}%</span>
            </div>
          </div>
        </div>

        {/* Predicted Performance */}
        <div className="bg-gradient-to-br from-green-700 to-emerald-700 rounded-lg p-4 border border-green-600">
          <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            After Optimization
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-green-100 text-sm">Duration:</span>
              <span className="text-white font-bold">{(predicted.duration || 0).toFixed(2)}s {improvement.time_saved && <span className="text-green-200 text-xs">({improvement.time_saved})</span>}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-100 text-sm">Cost:</span>
              <span className="text-white font-bold">${(predicted.cost || 0).toFixed(4)} {improvement.cost_saved && <span className="text-green-200 text-xs">({improvement.cost_saved})</span>}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-100 text-sm">Efficiency:</span>
              <span className="text-white font-bold">{predicted.efficiency_score || 0}% {improvement.efficiency_gain && <span className="text-green-200 text-xs">({improvement.efficiency_gain})</span>}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottlenecks */}
      {bottlenecks.length > 0 && (
        <div className="bg-slate-700 rounded-lg p-4 border border-orange-500">
          <h4 className="text-lg font-bold text-orange-400 mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Bottlenecks Detected ({bottlenecks.length})
          </h4>
          <div className="space-y-3">
            {bottlenecks.map((b, i) => {
              const severityColors = {
                critical: 'text-red-400 bg-red-900/30 border-red-500',
                high: 'text-orange-400 bg-orange-900/30 border-orange-500',
                medium: 'text-yellow-400 bg-yellow-900/30 border-yellow-500',
                low: 'text-green-400 bg-green-900/30 border-green-500'
              };
              const color = severityColors[b.severity] || severityColors.medium;

              return (
                <div key={i} className={`p-3 rounded border ${color}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold">{b.node || 'Unknown Node'}</span>
                    <span className="text-xs font-semibold uppercase">{b.severity || 'medium'}</span>
                  </div>
                  <div className="text-sm text-slate-300 mb-1">
                    ⏱️ Takes {(b.percentage || 0).toFixed(0)}% of total time ({(b.duration || 0).toFixed(2)}s)
                  </div>
                  <div className="text-sm text-slate-300 mb-1">
                    💡 {b.suggestion || 'No suggestion available'}
                  </div>
                  <div className="text-sm text-green-300">
                    📊 Impact: {b.impact || 'Unknown'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Caching Opportunities */}
      {cachingOps.length > 0 && (
        <div className="bg-slate-700 rounded-lg p-4 border border-cyan-500">
          <h4 className="text-lg font-bold text-cyan-400 mb-3 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Caching Opportunities ({cachingOps.length})
          </h4>
          <div className="space-y-3">
            {cachingOps.map((c, i) => (
              <div key={i} className="p-3 rounded bg-cyan-900/30 border border-cyan-700">
                <div className="font-bold text-cyan-300 mb-2">{c.node || 'Unknown'} ({c.node_type || 'N/A'})</div>
                <div className="text-sm text-slate-300 mb-1">📝 {c.reason || 'No reason provided'}</div>
                <div className="text-sm text-slate-300 mb-1">🎯 Hit Rate: {((c.hit_rate || 0) * 100).toFixed(0)}%</div>
                <div className="text-sm text-green-300">💰 Savings: {c.savings || 'Unknown'}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Optimizations */}
      {costOpts.length > 0 && (
        <div className="bg-slate-700 rounded-lg p-4 border border-purple-500">
          <h4 className="text-lg font-bold text-purple-400 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Cost Optimizations ({costOpts.length})
          </h4>
          <div className="space-y-3">
            {costOpts.map((co, i) => (
              <div key={i} className="p-3 rounded bg-purple-900/30 border border-purple-700">
                <div className="font-bold text-purple-300 mb-2">{co.node || 'Unknown Node'}</div>
                <div className="text-sm text-slate-300 mb-1">
                  Current: <span className="text-red-300">{co.current_model || 'N/A'}</span> →
                  Suggested: <span className="text-green-300"> {co.suggested_model || 'N/A'}</span>
                </div>
                <div className="text-sm text-slate-300 mb-1">📝 {co.reason || 'No reason provided'}</div>
                <div className="text-sm text-green-300 mb-1">💰 Savings: {co.savings || 'Unknown'}</div>
                <div className="text-sm text-yellow-300">⚠️ Quality: {co.quality_impact || 'Unknown'}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Suggestions */}
      {aiSuggestions.length > 0 && (
        <div className="bg-gradient-to-br from-purple-800 to-pink-800 rounded-lg p-4 border border-purple-500">
          <h4 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5" />
            AI Suggestions {analysis.suggestions_generated_by && `(Generated by: ${analysis.suggestions_generated_by})`}
          </h4>
          <div className="space-y-4">
            {aiSuggestions.map((s, i) => {
              const priorityColors = {
                critical: 'border-red-500 bg-red-900/40',
                high: 'border-orange-500 bg-orange-900/40',
                medium: 'border-yellow-500 bg-yellow-900/40',
                low: 'border-green-500 bg-green-900/40'
              };
              const color = priorityColors[s.priority] || priorityColors.medium;

              return (
                <div key={i} className={`p-4 rounded border ${color}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-bold text-white text-lg">{i + 1}. {s.title || 'Untitled Suggestion'}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold uppercase text-slate-300">{s.priority || 'medium'}</span>
                      <span className="text-xs text-slate-400">({s.difficulty || 'N/A'})</span>
                    </div>
                  </div>

                  <div className="space-y-2 text-sm">
                    {s.problem && (
                      <div>
                        <span className="text-red-300 font-semibold">⚠️ Problem:</span>
                        <p className="text-slate-200 mt-1">{s.problem}</p>
                      </div>
                    )}

                    {s.solution && (
                      <div>
                        <span className="text-green-300 font-semibold">💡 Solution:</span>
                        <p className="text-slate-200 mt-1">{s.solution}</p>
                      </div>
                    )}

                    {s.impact && (
                      <div>
                        <span className="text-cyan-300 font-semibold">📊 Impact:</span>
                        <p className="text-slate-200 mt-1">{s.impact}</p>
                      </div>
                    )}

                    {s.code_fix && (
                      <div>
                        <span className="text-purple-300 font-semibold">🔧 Code Fix:</span>
                        <pre className="mt-2 p-3 bg-slate-900 rounded text-green-400 text-xs overflow-x-auto">
                          {s.code_fix}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// Result panel component
const ResultPanel = ({ result }) => {
  if (!result) return null;

  const isError = result.status === 'error' || result.status === 'parse_error' || result.status === 'validation_error';

  return (
    <div className={`mt-4 p-4 rounded-lg border ${
      isError ? 'bg-red-50 border-red-300' : 'bg-green-50 border-green-300'
    }`}>
      <div className="flex items-center gap-2 mb-3">
        {isError ? (
          <AlertCircle className="w-5 h-5 text-red-600" />
        ) : (
          <CheckCircle className="w-5 h-5 text-green-600" />
        )}
        <h3 className="font-bold text-lg">
          {isError ? 'Σφάλμα Εκτέλεσης' : 'Επιτυχής Εκτέλεση'}
        </h3>
      </div>

      {result.status === 'parse_error' && (
        <div className="space-y-2">
          <p className="font-semibold text-red-700">Σφάλματα Parsing:</p>
          {result.errors.map((err, i) => (
            <div key={i} className="text-sm text-red-600 bg-red-100 p-2 rounded">
              {err}
            </div>
          ))}
        </div>
      )}

      {result.status === 'validation_error' && (
        <div className="space-y-2">
          <p className="font-semibold text-red-700">Σφάλματα Validation:</p>
          <pre className="text-sm text-red-600 bg-red-100 p-3 rounded overflow-auto">
            {result.report}
          </pre>
        </div>
      )}

      {result.status === 'success' && result.result && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-green-700">
            <Zap className="w-4 h-4" />
            <span>Flow: <strong>{result.flow_name}</strong></span>
            <span className="mx-2">•</span>
            <span>Duration: <strong>{result.result.duration_seconds.toFixed(2)}s</strong></span>
          </div>

          {result.result.outputs && (
            <div className="mt-3">
              <p className="font-semibold text-green-800 mb-2">Outputs:</p>
              <div className="space-y-2">
                {Object.entries(result.result.outputs).map(([key, value]) => (
                  <div key={key} className="bg-white p-3 rounded border border-green-200">
                    <div className="text-sm font-bold text-green-700 mb-1">{key}:</div>
                    <div className="text-sm text-gray-800 whitespace-pre-wrap">
                      {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.result.execution_log && (
            <details className="mt-3">
              <summary className="cursor-pointer font-semibold text-green-700 hover:text-green-800">
                Execution Log ({result.result.execution_log.length} events)
              </summary>
              <div className="mt-2 space-y-1 max-h-60 overflow-y-auto">
                {result.result.execution_log.map((log, i) => (
                  <div key={i} className="text-xs bg-slate-800 text-green-300 p-2 rounded font-mono">
                    <span className="text-cyan-400">[{log.timestamp}]</span>{' '}
                    <span className={
                      log.status === 'ERROR' ? 'text-red-400' :
                      log.status === 'SUCCESS' ? 'text-green-400' :
                      log.status === 'START' ? 'text-yellow-400' :
                      'text-blue-400'
                    }>{log.status}</span>{' '}
                    <span className="text-purple-300">[{log.node}]</span>{' '}
                    <span>{log.message}</span>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
};

// Main component
export default function AetherLangOmega() {
  const [code, setCode] = useState('');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [examples, setExamples] = useState([]);
  const [selectedExample, setSelectedExample] = useState(null);
  const [parsedFlow, setParsedFlow] = useState(null);
  const [executionStatus, setExecutionStatus] = useState({});
  const [showVisualization, setShowVisualization] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [executionProgress, setExecutionProgress] = useState(0);
  const [isValidating, setIsValidating] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAiInsights, setShowAiInsights] = useState(false);
  const [optimizedCode, setOptimizedCode] = useState(null);
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [enableProfiling, setEnableProfiling] = useState(false);
  const [profileData, setProfileData] = useState(null);
  const [showProfileViewer, setShowProfileViewer] = useState(false);
  const [enableDebugging, setEnableDebugging] = useState(false);
  const [debugSessionId, setDebugSessionId] = useState(null);
  const [showDebugger, setShowDebugger] = useState(false);
  const [selectedLayout, setSelectedLayout] = useState('auto');
  const [isApplyingLayout, setIsApplyingLayout] = useState(false);
  const [layoutPositions, setLayoutPositions] = useState(null);
  const [showCollaboration, setShowCollaboration] = useState(false);
  const [collaborationSessionId, setCollaborationSessionId] = useState(null);
  const [currentUserId] = useState(() => 'user_' + Math.random().toString(36).substr(2, 9));
  const [currentUserName, setCurrentUserName] = useState('Anonymous');

  // Legal compliance and UI state
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [language, setLanguage] = useState('en'); // 'en' or 'el'

  // BYOK (Bring Your Own Key) System
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [userTier, setUserTier] = useState('free'); // 'free' or 'unlimited'
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [usageStats, setUsageStats] = useState({ remaining: 10, reset_in_seconds: 3600, limit: 10 });

  // Export flow as JSON
  const exportFlow = () => {
    const flowData = {
      code,
      query,
      parsedFlow,
      timestamp: new Date().toISOString(),
      version: '0.2.0'
    };
    const blob = new Blob([JSON.stringify(flowData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aether-flow-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Flow exported successfully');
  };

  // Import flow from JSON
  const importFlow = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const flowData = JSON.parse(e.target.result);
        setCode(flowData.code || '');
        setQuery(flowData.query || '');
        setParsedFlow(flowData.parsedFlow || null);
        toast.success('Flow imported successfully');
      } catch (error) {
        toast.error('Failed to import flow: Invalid JSON');
      }
    };
    reader.readAsText(file);
  };

  // Fetch user usage stats on mount and after executions
  useEffect(() => {
    fetchUsageStats();
  }, []);

  const fetchUsageStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/aetherlang/usage/current`, {
        withCredentials: true
      });
      setUserTier(response.data.tier);
      setUsageStats(response.data.rate_limit);
    } catch (error) {
      console.error('Failed to fetch usage stats:', error);
    }
  };

  const setUserApiKey = async () => {
    if (!apiKeyInput.trim() || !apiKeyInput.startsWith('sk-')) {
      toast.error('Invalid API key format. Must start with sk-');
      return;
    }

    const loadingToast = toast.loading('Validating API key...');

    try {
      const response = await axios.post(
        `${API_BASE}/aetherlang/api-key/set`,
        { api_key: apiKeyInput },
        { withCredentials: true }
      );

      toast.dismiss(loadingToast);
      toast.success('✅ API key set successfully! Unlimited executions enabled.');
      setUserTier(response.data.tier);
      setApiKeyInput('');
      setShowApiKeyModal(false);
      fetchUsageStats();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to set API key: ' + (error.response?.data?.detail || error.message));
    }
  };

  const removeUserApiKey = async () => {
    const loadingToast = toast.loading('Removing API key...');

    try {
      await axios.delete(`${API_BASE}/aetherlang/api-key/remove`, {
        withCredentials: true
      });

      toast.dismiss(loadingToast);
      toast.success('API key removed. Returned to free tier.');
      setUserTier('free');
      setShowApiKeyModal(false);
      fetchUsageStats();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to remove API key: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Cmd/Ctrl + K για validate
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        validateCode();
      }
      // Cmd/Ctrl + Enter για execute
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        executeFlow();
      }
      // Cmd/Ctrl + S για export
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        exportFlow();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [code, query, parsedFlow]);

  // Hardcoded examples (προσωρινή λύση για Cloudflare cache issue)
  useEffect(() => {
    setExamples([
      {
        id: "intro",
        name: "Εισαγωγικό Flow",
        description: "Βασικό flow με Guard -> Plan -> LLM"
      },
      {
        id: "analysis",
        name: "Πλήρης Ανάλυση",
        description: "Flow με ανάλυση και περίληψη"
      },
      {
        id: "extract",
        name: "Εξαγωγή Δεδομένων",
        description: "Flow για structured data extraction"
      },
      {
        id: "research",
        name: "Ερευνητικό Flow",
        description: "Πολύπλοκο flow με πολλαπλά στάδια"
      },
      {
        id: "greek_education",
        name: "Ελληνικό Εκπαιδευτικό Flow",
        description: "Ειδικό flow για ελληνικό εκπαιδευτικό υλικό"
      },
      {
        id: "enterprise",
        name: "Enterprise Document Processing",
        description: "Flow για επεξεργασία εταιρικών εγγράφων"
      },
      {
        id: "chef_recipe",
        name: "AI Chef - Συνταγή",
        description: "Culinary flow: Guard -> Plan -> Chef -> Summarize"
      },
      {
        id: "safe_chat",
        name: "Ασφαλής Συνομιλία",
        description: "Απλό flow με Guard και LLM για safe chat"
      },
      {
        id: "market_research",
        name: "Market Analysis",
        description: "Research + Consult + Market analysis pipeline"
      },
      {
        id: "molecular_lab",
        name: "Molecular Lab - APEIRON",
        description: "Molecular gastronomy with scientific precision"
      },
      {
        id: "business_apex",
        name: "APEX Business Strategy",
        description: "Nobel-level strategic analysis with ROI projections"
      },
      {
        id: "oracle_forecast",
        name: "Oracle - Predictions",
        description: "OMNI-COMPUTE adversarial forecasting engine"
      },
      {
        id: "gaia_assembly",
        name: "GAIA Brain - Assembly",
        description: "Multi-agent panel with 12 neural archetypes"
      },
      {
        id: "full_consulting",
        name: "Full Consulting Pipeline",
        description: "Research -> Consult -> Market -> APEX pipeline"
      }
    ]);
  }, []);

  const loadExample = (exampleId) => {
    // Hardcoded example flows (προσωρινή λύση για Cloudflare cache)
    const exampleCodes = {
      intro: `flow IntroFlow {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="STRICT";
  node Planner: plan steps=3;
  node LLM: llm model="gpt-4o", temp=0.7;

  Guard -> Planner -> LLM;

  output text result from LLM;
}`,
      analysis: `flow AnalysisFlow {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="STRICT";
  node Analyzer: analyze depth="comprehensive";
  node LLM: llm model="gpt-4o", temp=0.6;
  node Summarizer: summarize length="detailed";

  Guard -> Analyzer -> LLM -> Summarizer;

  output text analysis from LLM;
  output text summary from Summarizer;
}`,
      extract: `flow ExtractFlow {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="STRICT";
  node Extractor: extract type="entities";
  node Transform: transform type="json";

  Guard -> Extractor -> Transform;

  output text data from Transform;
}`,
      research: `flow ResearchFlow {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="STRICT";
  node Planner: plan steps=5;
  node RAG: rag topk=10;
  node Analyzer: analyze depth="deep";
  node LLM: llm model="gpt-4o", temp=0.6;

  Guard -> Planner;
  Planner -> RAG;
  RAG -> Analyzer;
  Analyzer -> LLM;

  output text research from LLM;
}`,
      greek_education: `flow GreekEducationFlow {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="STRICT";
  node Planner: plan steps=4;
  node LLM: llm model="gpt-4o", temp=0.7;
  node Summarizer: summarize length="medium";

  Guard -> Planner -> LLM -> Summarizer;

  output text educational_content from LLM;
  output text summary from Summarizer;
}`,
      enterprise: `flow EnterpriseFlow {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="STRICT";
  node Analyzer: analyze depth="comprehensive";
  node Extractor: extract type="structured";
  node Transform: transform type="json";

  Guard -> Analyzer;
  Analyzer -> Extractor;
  Extractor -> Transform;

  output text analysis from Analyzer;
  output text extracted_data from Transform;
}`,
      chef_recipe: `flow RecipeCreator {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="MODERATE";
  node Planner: plan steps=3;
  node Chef: chef cuisine="greek", difficulty="medium", servings=4;
  node Summary: summarize length="detailed";
  Guard -> Planner -> Chef -> Summary;
  output text recipe from Summary;
}`,
      safe_chat: `flow SafeChat {
  using target "neuroaether" version ">=0.2";
  input text message;
  node Shield: guard mode="STRICT";
  node Responder: llm model="gpt-4o", temp=0.7;
  Shield -> Responder;
  output text reply from Responder;
}`,
      market_research: `flow MarketResearch {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="STRICT";
  node Research: research depth="comprehensive";
  node Consult: consult domain="business", framework="swot";
  node Market: market scope="global", timeframe="6months";
  node Summary: summarize length="detailed";
  Guard -> Research -> Consult -> Market -> Summary;
  output text report from Summary;
}`,
    
      molecular_lab: `flow MolecularLab {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="MODERATE";
  node Chef: chef cuisine="modern", difficulty="molecular";
  node Molecular: molecular complexity="advanced";
  Guard -> Chef -> Molecular;
  output text analysis from Molecular;
}`,
      business_apex: `flow ApexStrategy {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="STRICT";
  node Research: research depth="comprehensive";
  node Apex: apex mode="standard";
  Guard -> Research -> Apex;
  output text strategy from Apex;
}`,
      oracle_forecast: `flow OracleForecast {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="MODERATE";
  node Oracle: oracle timeframe="12months";
  Guard -> Oracle;
  output text forecast from Oracle;
}`,
      gaia_assembly: `flow GaiaAssembly {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="MODERATE";
  node Assembly: assembly;
  node Balance: balance focus="both";
  Guard -> Assembly -> Balance;
  output text verdict from Balance;
}`,
      full_consulting: `flow FullConsulting {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="STRICT";
  node Research: research depth="comprehensive";
  node Consult: consult domain="business", framework="SWOT";
  node Market: market scope="global", timeframe="2026";
  node Apex: apex mode="standard";
  Guard -> Research -> Consult -> Market -> Apex;
  output text report from Apex;
}`,
};

    const exampleCode = exampleCodes[exampleId];
    if (exampleCode) {
      setCode(exampleCode);
      setQuery('Δώσε μου ένα παράδειγμα ανάλυσης.');
      setSelectedExample(exampleId);
      const exampleName = examples.find(e => e.id === exampleId)?.name || exampleId;
      toast.success(`Loaded example: ${exampleName}`);
    } else {
      toast.error('Example not found');
    }
  };

  const executeFlow = async () => {
    if (!code.trim() || !query.trim()) {
      toast.error('Please provide both code and query');
      return;
    }

    // Auto-validate before execution
    if (!parsedFlow) {
      toast.loading('Validating flow...');
      await validateCode();
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setExecuting(true);
    setResult(null);
    setExecutionStatus({});
    setExecutionProgress(0);

    const loadingToast = toast.loading('🚀 Executing flow...');

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setExecutionProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await axios.post(
        `${API_BASE}/aetherlang/execute`,
        { code, query, enable_profiling: enableProfiling, enable_debugging: enableDebugging },
        { headers: { 'X-Aether-Key': ADMIN_KEY } }
      );

      clearInterval(progressInterval);
      setExecutionProgress(100);

      // Update execution status from logs
      if (response.data.result?.execution_log) {
        const statusMap = {};
        response.data.result.execution_log.forEach(log => {
          if (log.node !== 'SYSTEM') {
            if (log.status === 'START') statusMap[log.node] = 'executing';
            if (log.status === 'SUCCESS') statusMap[log.node] = 'success';
            if (log.status === 'ERROR') statusMap[log.node] = 'error';
          }
        });
        setExecutionStatus(statusMap);
      }

      // Store profile data if profiling was enabled
      if (enableProfiling && response.data.profile) {
        setProfileData(response.data.profile);
        setShowProfileViewer(true);
      }

      // Store debug session if debugging was enabled
      if (enableDebugging && response.data.debug_session) {
        setDebugSessionId(response.data.debug_session.session_id);
        toast.success('🐛 Debug session recorded!', { duration: 3000 });
      }

      toast.dismiss(loadingToast);
      setResult(response.data);
      if (response.data.status === 'success') {
        toast.success('✨ Flow executed successfully!');
        if (enableProfiling && response.data.profile) {
          toast.success('📊 Performance profile generated!', { duration: 3000 });
        }
        // Update usage stats after successful execution
        if (response.data.usage) {
          setUsageStats(response.data.usage);
        }
        fetchUsageStats();
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      const errorDetail = error.response?.data?.detail || error.message;

      // Check if it's a rate limit error
      if (error.response?.status === 429) {
        toast.error('⏱️ Rate limit reached! Add your own API key for unlimited access.', { duration: 5000 });
      } else {
        toast.error('❌ Execution failed: ' + errorDetail);
      }

      setResult({
        status: 'error',
        error: errorDetail
      });
    } finally {
      setExecuting(false);
      setTimeout(() => setExecutionProgress(0), 1000);
    }
  };

  const validateCode = async () => {
    if (!code.trim()) {
      toast.error('Please provide code to validate');
      return;
    }

    setIsValidating(true);
    const loadingToast = toast.loading('🔍 Validating flow...');

    try {
      const response = await axios.post(
        `${API_BASE}/aetherlang/validate`,
        { code },
        { headers: { 'X-Aether-Key': ADMIN_KEY } }
      );

      toast.dismiss(loadingToast);

      if (response.data.valid) {
        toast.success('✅ Code is valid!');
        setParsedFlow(response.data.flow);
        setResult({
          status: 'success',
          message: 'Validation successful',
          report: response.data.report,
          flow: response.data.flow
        });
      } else {
        toast.error('❌ Validation failed');
        setParsedFlow(null);
        setResult({
          status: 'validation_error',
          errors: response.data.errors,
          report: response.data.report
        });
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Validation request failed');
      setParsedFlow(null);
    } finally {
      setIsValidating(false);
    }
  };

  // AI-powered flow analysis
  const analyzeFlow = async () => {
    if (!code.trim()) {
      toast.error('Please provide flow code to analyze');
      return;
    }

    setIsAnalyzing(true);
    setAiAnalysis(null);
    const loadingToast = toast.loading('🧠 Analyzing flow with AI...');

    try {
      // Build execution history from result if available
      const execution_history = result?.result?.execution_log
        ? [{
            duration_seconds: result.result.duration_seconds || 0,
            execution_log: result.result.execution_log
          }]
        : [];

      const response = await axios.post(
        `${API_BASE}/aetherlang/analyze-flow`,
        {
          code,
          execution_history
        },
        { headers: { 'X-Aether-Key': ADMIN_KEY } }
      );

      toast.dismiss(loadingToast);
      toast.success('✅ Analysis complete!');
      setAiAnalysis(response.data);
      setShowAiInsights(true);
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Analysis failed: ' + (error.response?.data?.detail || error.message));
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Apply automatic optimizations
  const applyOptimizations = async () => {
    if (!code.trim()) {
      toast.error('Please provide flow code to optimize');
      return;
    }

    setIsOptimizing(true);
    const loadingToast = toast.loading('🔧 Applying optimizations...');

    try {
      const execution_history = result?.result?.execution_log
        ? [{
            duration_seconds: result.result.duration_seconds || 0,
            execution_log: result.result.execution_log
          }]
        : [];

      const response = await axios.post(
        `${API_BASE}/aetherlang/optimize-flow`,
        {
          code,
          execution_history
        },
        { headers: { 'X-Aether-Key': ADMIN_KEY } }
      );

      toast.dismiss(loadingToast);

      if (response.data.status === 'success' && response.data.valid) {
        toast.success('✅ Optimizations applied!');
        setOptimizedCode(response.data);
        setShowDiffModal(true);
      } else {
        toast.error('Optimization failed: ' + (response.data.errors?.join(', ') || 'Invalid code'));
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Optimization failed: ' + (error.response?.data?.detail || error.message));
      console.error('Optimization error:', error);
    } finally {
      setIsOptimizing(false);
    }
  };

  // Accept optimized code
  const acceptOptimizations = () => {
    if (optimizedCode) {
      setCode(optimizedCode.optimized_code);
      setShowDiffModal(false);
      setParsedFlow(null);
      toast.success('✅ Optimized code applied! Click Validate to check it.');
    }
  };

  // Apply layout
  const applyLayout = async () => {
    if (!code.trim()) {
      toast.error('Please provide code first');
      return;
    }

    setIsApplyingLayout(true);
    const loadingToast = toast.loading(`Applying ${selectedLayout} layout...`);

    try {
      const response = await axios.post(
        `${API_BASE}/aetherlang/layout`,
        {
          code,
          layout_type: selectedLayout
        },
        { headers: { 'X-Aether-Key': ADMIN_KEY } }
      );

      toast.dismiss(loadingToast);

      if (response.data.status === 'success') {
        setLayoutPositions(response.data.positions);
        toast.success(`✨ ${response.data.layout_type} layout applied!`);
      } else {
        toast.error('Layout failed: ' + (response.data.errors?.join(', ') || 'Unknown error'));
      }
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Layout failed: ' + (error.response?.data?.detail || error.message));
      console.error('Layout error:', error);
    } finally {
      setIsApplyingLayout(false);
    }
  };

  // Info Modal Component
  const InfoModal = () => {
    if (!showInfoModal) return null;

    const content = language === 'en' ? {
      title: 'About AetherLang Ω',
      subtitle: 'Professional AI Workflow Orchestration DSL',
      sections: [
        {
          icon: <Cpu className="w-6 h-6 text-cyan-400" />,
          title: 'What is AetherLang?',
          content: 'AetherLang Ω is a production-ready Domain-Specific Language designed for building, visualizing, and executing complex AI workflows. Think of it as "Airflow meets Prefect" but with a clean, declarative syntax optimized for LLM orchestration.'
        },
        {
          icon: <Zap className="w-6 h-6 text-purple-400" />,
          title: 'Key Features',
          content: '• 28 Specialized Node Types (Guards, LLMs, RAG, caching, validation)\n• Real-time Visual Flow Designer with live execution\n• Performance Profiling & AI-Powered Optimization\n• Time-Travel Debugging with state snapshots\n• Real-time Collaboration with multi-user sessions\n• Bilingual Support (Greek & English)'
        },
        {
          icon: <Code2 className="w-6 h-6 text-green-400" />,
          title: 'Quick Start',
          content: 'Select an example from the sidebar, modify the code, add your query, and click Execute. Use Cmd/Ctrl+Enter to run, Cmd/Ctrl+K to validate, and Cmd/Ctrl+S to export.'
        },
        {
          icon: <Server className="w-6 h-6 text-orange-400" />,
          title: 'Technical Details',
          content: 'Version: 0.2.0 Pro\nEngine: NeuroAether Runtime\nBackend: FastAPI + Python 3.10\nFrontend: React + Vite + Tailwind CSS\nHosting: Hetzner Germany (EU compliance)\nDomain: neurodoc.app'
        },
        {
          icon: <Send className="w-6 h-6 text-emerald-400" />,
          title: 'AetherLang Telegram Bot — 15 AI Engines',
          content: 'Try the AetherLang Omega Bot on Telegram (@aetherlang_bot) with 15 specialized AI engines:\n\n' +
            '👨‍🍳 Chef Omega — Michelin recipes + HACCP + financials\n' +
            '📈 APEX Strategy — Nobel-level business analysis\n' +
            '🏛️ Grand Assembly — 26+ legendary archetypes + Gandalf Veto\n' +
            '💼 McKinsey Consulting — SWOT + Roadmap + KPIs\n' +
            '🔬 Deep Analysis Lab — Scientific analysis + Nobel insights\n' +
            '📣 Viral Marketing — Campaign generator\n' +
            '🎰 OPAP Oracle — LIVE lottery data + statistics\n' +
            '📊 Crypto Intelligence — LIVE prices + APEX trading analysis\n' +
            '📄 Trading Blueprint — Hedge fund-grade PDF reports\n' +
            '⚗️ Molecular Gastronomy — Spherification, foams, sous-vide\n' +
            '🔥 Chef Omega Neural — 15 Neural Agents + GAIA Brain\n' +
            '🧠 Super Brain Nobel — Breakthrough innovation analysis\n' +
            '🔒 Cyber Intelligence — Security + NIST/ISO frameworks\n' +
            '🎓 Academic Research — arXiv, PubMed + 12 sources\n' +
            '🌿 Terra Alchemica — Bio-Alchemy + Molecular + Monastic Olympus Council\n\n' +
            '→ t.me/aetherlang_bot'
        }
      ]
    } : {
      title: 'Σχετικά με το AetherLang Ω',
      subtitle: 'Επαγγελματική DSL για Ενορχήστρωση AI Workflows',
      sections: [
        {
          icon: <Cpu className="w-6 h-6 text-cyan-400" />,
          title: 'Τι είναι το AetherLang;',
          content: 'Το AetherLang Ω είναι μια έτοιμη για παραγωγή Domain-Specific Language σχεδιασμένη για την κατασκευή, οπτικοποίηση και εκτέλεση σύνθετων AI workflows. Σκεφτείτε το ως "Airflow meets Prefect" αλλά με καθαρή, δηλωτική σύνταξη βελτιστοποιημένη για ενορχήστρωση LLM.'
        },
        {
          icon: <Zap className="w-6 h-6 text-purple-400" />,
          title: 'Βασικά Χαρακτηριστικά',
          content: '• 28 Εξειδικευμένοι Τύποι Κόμβων (Guards, LLMs, RAG, caching, validation)\n• Real-time Visual Flow Designer με ζωντανή εκτέλεση\n• Performance Profiling & AI-Powered Βελτιστοποίηση\n• Time-Travel Debugging με στιγμιότυπα κατάστασης\n• Real-time Συνεργασία με multi-user sessions\n• Διγλωσσική Υποστήριξη (Ελληνικά & Αγγλικά)'
        },
        {
          icon: <Code2 className="w-6 h-6 text-green-400" />,
          title: 'Γρήγορη Εκκίνηση',
          content: 'Επιλέξτε ένα παράδειγμα από την πλευρική μπάρα, τροποποιήστε τον κώδικα, προσθέστε το ερώτημά σας και κάντε κλικ στο Execute. Χρησιμοποιήστε Cmd/Ctrl+Enter για εκτέλεση, Cmd/Ctrl+K για επικύρωση και Cmd/Ctrl+S για εξαγωγή.'
        },
        {
          icon: <Server className="w-6 h-6 text-orange-400" />,
          title: 'Τεχνικές Λεπτομέρειες',
          content: 'Έκδοση: 0.2.0 Pro\nΜηχανή: NeuroAether Runtime\nBackend: FastAPI + Python 3.10\nFrontend: React + Vite + Tailwind CSS\nΦιλοξενία: Hetzner Γερμανία (EU compliance)\nΤομέας: neurodoc.app'
        },
        {
          icon: <Send className="w-6 h-6 text-emerald-400" />,
          title: 'AetherLang Telegram Bot — 15 AI Engines',
          content: 'Δοκιμάστε το AetherLang Omega Bot στο Telegram (@aetherlang_bot) με 15 εξειδικευμένες AI μηχανές:\n\n' +
            '👨‍🍳 Chef Omega — Συνταγές Michelin + HACCP + οικονομικά\n' +
            '📈 APEX Strategy — Ανάλυση επιχειρήσεων επιπέδου Nobel\n' +
            '🏛️ Grand Assembly — 26+ αρχέτυπα + Gandalf Veto\n' +
            '💼 McKinsey Consulting — SWOT + Roadmap + KPIs\n' +
            '🔬 Deep Analysis Lab — Επιστημονική ανάλυση\n' +
            '📣 Viral Marketing — Δημιουργία καμπανιών\n' +
            '🎰 OPAP Oracle — ΖΩΝΤΑΝΑ δεδομένα κληρώσεων\n' +
            '📊 Crypto Intelligence — ΖΩΝΤΑΝΕΣ τιμές + ανάλυση\n' +
            '📄 Trading Blueprint — PDF αναφορές hedge fund\n' +
            '⚗️ Μοριακή Γαστρονομία — Σφαιροποίηση, αφροί, sous-vide\n' +
            '🔥 Chef Omega Neural — 15 Neural Agents + GAIA Brain\n' +
            '🧠 Super Brain Nobel — Ανάλυση καινοτομίας\n' +
            '🔒 Cyber Intelligence — Ασφάλεια + NIST/ISO\n' +
            '🎓 Academic Research — arXiv, PubMed + 12 πηγές\n' +
            '🌿 Terra Alchemica — Βιο-Αλχημεία + Μοριακή + Μοναστηριακό Συμβούλιο\n\n' +
            '→ t.me/aetherlang_bot'
        }
      ]
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-2xl border border-cyan-500 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
          <div className="p-6 border-b border-slate-700 bg-gradient-to-r from-cyan-900/50 to-purple-900/50">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400">
                  {content.title}
                </h2>
                <p className="text-slate-400 text-sm mt-1">{content.subtitle}</p>
              </div>
              <button
                onClick={() => setShowInfoModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {content.sections.map((section, idx) => (
              <div key={idx} className="bg-slate-900 rounded-xl p-5 border border-slate-700">
                <div className="flex items-center gap-3 mb-3">
                  {section.icon}
                  <h3 className="text-lg font-bold text-cyan-400">{section.title}</h3>
                </div>
                <p className="text-slate-300 text-sm whitespace-pre-line leading-relaxed">
                  {section.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // BYOK API Key Modal Component
  const ApiKeyModal = () => {
    if (!showApiKeyModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-2xl border border-cyan-500 max-w-2xl w-full overflow-hidden flex flex-col shadow-2xl">
          <div className="p-6 border-b border-slate-700 bg-gradient-to-r from-cyan-900/50 to-purple-900/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Server className="w-8 h-8 text-cyan-400" />
                <div>
                  <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400">
                    {language === 'en' ? 'Bring Your Own Key (BYOK)' : 'Φέρτε το Δικό σας Κλειδί (BYOK)'}
                  </h2>
                  <p className="text-slate-400 text-sm mt-1">
                    {language === 'en' ? 'Unlimited executions with your OpenAI API key' : 'Απεριόριστες εκτελέσεις με το OpenAI API key σας'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowApiKeyModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Current Tier Display */}
            <div className={`p-4 rounded-lg border ${userTier === 'unlimited' ? 'bg-green-900/20 border-green-500/50' : 'bg-orange-900/20 border-orange-500/50'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                  {language === 'en' ? 'Current Tier' : 'Τρέχον Επίπεδο'}
                </span>
                <span className={`text-lg font-bold ${userTier === 'unlimited' ? 'text-green-400' : 'text-orange-400'}`}>
                  {userTier === 'unlimited' ? (language === 'en' ? '∞ Unlimited' : '∞ Απεριόριστο') : (language === 'en' ? 'Free Tier' : 'Δωρεάν Επίπεδο')}
                </span>
              </div>
              <div className="text-sm text-slate-400">
                {userTier === 'unlimited' ? (
                  language === 'en' ? 'Using your own API key' : 'Χρήση του δικού σας API key'
                ) : (
                  <>
                    {language === 'en' ? `${usageStats.remaining} / ${usageStats.limit} executions remaining` : `${usageStats.remaining} / ${usageStats.limit} εκτελέσεις απομένουν`}
                    <br />
                    {language === 'en' ? `Resets in ${Math.floor(usageStats.reset_in_seconds / 60)} minutes` : `Επαναφορά σε ${Math.floor(usageStats.reset_in_seconds / 60)} λεπτά`}
                  </>
                )}
              </div>
            </div>

            {userTier === 'free' ? (
              <>
                {/* Add API Key Section */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      {language === 'en' ? 'OpenAI API Key' : 'OpenAI API Κλειδί'}
                    </label>
                    <input
                      type="password"
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      placeholder="sk-..."
                      className="w-full px-4 py-2 bg-slate-900 text-white rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                    <p className="text-xs text-slate-500 mt-2">
                      {language === 'en'
                        ? 'Your API key is stored locally and never sent to our servers. It\'s only used to make OpenAI API calls on your behalf.'
                        : 'Το API κλειδί σας αποθηκεύεται τοπικά και δεν αποστέλλεται ποτέ στους διακομιστές μας. Χρησιμοποιείται μόνο για κλήσεις OpenAI API εκ μέρους σας.'}
                    </p>
                  </div>

                  <button
                    onClick={setUserApiKey}
                    disabled={!apiKeyInput.trim()}
                    className="w-full py-3 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white font-bold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Zap className="w-5 h-5" />
                    {language === 'en' ? 'Enable Unlimited Access' : 'Ενεργοποίηση Απεριόριστης Πρόσβασης'}
                  </button>
                </div>

                {/* Benefits */}
                <div className="bg-slate-900/50 rounded-lg p-4 space-y-2">
                  <h3 className="text-sm font-bold text-cyan-400 mb-3">
                    {language === 'en' ? '✨ Benefits of BYOK:' : '✨ Πλεονεκτήματα BYOK:'}
                  </h3>
                  <div className="space-y-2 text-sm text-slate-300">
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      <span>{language === 'en' ? 'Unlimited flow executions' : 'Απεριόριστες εκτελέσεις flow'}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      <span>{language === 'en' ? 'No rate limits' : 'Χωρίς περιορισμούς ρυθμού'}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      <span>{language === 'en' ? 'Direct billing to your OpenAI account' : 'Άμεση χρέωση στον λογαριασμό OpenAI σας'}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      <span>{language === 'en' ? 'Full control over usage and costs' : 'Πλήρης έλεγχος χρήσης και κόστους'}</span>
                    </div>
                  </div>
                </div>

                {/* How to get API key */}
                <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                  <p className="text-sm text-slate-300">
                    <span className="font-semibold text-blue-400">
                      {language === 'en' ? "Don't have an API key?" : 'Δεν έχετε API κλειδί;'}
                    </span>
                    <br />
                    {language === 'en'
                      ? 'Get one from '
                      : 'Αποκτήστε ένα από '}
                    <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline">
                      platform.openai.com/api-keys
                    </a>
                  </p>
                </div>
              </>
            ) : (
              <>
                {/* Remove API Key Section */}
                <div className="space-y-4">
                  <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                    <p className="text-sm text-slate-300">
                      <span className="font-semibold text-green-400">
                        {language === 'en' ? '✓ BYOK Active' : '✓ BYOK Ενεργό'}
                      </span>
                      <br />
                      {language === 'en'
                        ? 'You have unlimited executions. Your API key is being used for all OpenAI calls.'
                        : 'Έχετε απεριόριστες εκτελέσεις. Το API κλειδί σας χρησιμοποιείται για όλες τις κλήσεις OpenAI.'}
                    </p>
                  </div>

                  <button
                    onClick={removeUserApiKey}
                    className="w-full py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <AlertCircle className="w-5 h-5" />
                    {language === 'en' ? 'Remove API Key & Return to Free Tier' : 'Αφαίρεση API Key & Επιστροφή στο Δωρεάν Επίπεδο'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Terms of Service Modal Component
  const TermsModal = () => {
    if (!showTermsModal) return null;

    const content = language === 'en' ? {
      title: 'Terms of Service',
      subtitle: 'Last updated: February 2026',
      sections: [
        { title: '1. Acceptance of Terms', content: 'By accessing and using AetherLang Ω ("the Service"), you accept and agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use the Service.' },
        { title: '2. Description of Service', content: 'AetherLang Ω is a Domain-Specific Language (DSL) platform for AI workflow orchestration. The Service provides code editing, flow visualization, execution, profiling, debugging, and collaboration features for educational and professional purposes.' },
        { title: '3. User Responsibilities', content: 'You are responsible for:\n• Maintaining the confidentiality of your API keys\n• All activities that occur under your session\n• Compliance with applicable laws and regulations\n• Not using the Service for illegal or unauthorized purposes\n• Not attempting to reverse engineer or exploit the Service' },
        { title: '4. Intellectual Property', content: 'The Service, including its original content, features, and functionality, is owned by NeuroDoc and protected by international copyright, trademark, and other intellectual property laws. Your code and workflows remain your property.' },
        { title: '5. Privacy & Data Processing', content: 'We process data in accordance with our Privacy Policy and EU GDPR regulations. Your code and queries may be processed by OpenAI\'s GPT-4o models. We do not store your code permanently without your explicit consent (e.g., collaboration sessions).' },
        { title: '6. Third-Party Services', content: 'The Service integrates with OpenAI APIs. Your use of these integrations is subject to their respective terms of service. We are not responsible for third-party service availability or actions.' },
        { title: '7. Disclaimers', content: 'THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED. We do not guarantee:\n• Uninterrupted or error-free operation\n• Accuracy of AI-generated results\n• Fitness for any particular purpose\n• Security of data transmission' },
        { title: '8. Limitation of Liability', content: 'To the maximum extent permitted by law, NeuroDoc shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including loss of profits, data, or use, arising from your use of the Service.' },
        { title: '9. EU User Rights', content: 'EU users have the right to:\n• Access their personal data\n• Request data correction or deletion\n• Object to data processing\n• Data portability\n• Lodge a complaint with supervisory authorities' },
        { title: '10. Changes to Terms', content: 'We reserve the right to modify these terms at any time. Continued use of the Service after changes constitutes acceptance of the modified terms. Material changes will be communicated via the platform.' }
      ]
    } : {
      title: 'Όροι Χρήσης',
      subtitle: 'Τελευταία ενημέρωση: Φεβρουάριος 2026',
      sections: [
        { title: '1. Αποδοχή Όρων', content: 'Με την πρόσβαση και χρήση του AetherLang Ω ("η Υπηρεσία"), αποδέχεστε και συμφωνείτε να δεσμεύεστε από αυτούς τους Όρους Χρήσης. Εάν δεν συμφωνείτε με αυτούς τους όρους, παρακαλούμε μην χρησιμοποιείτε την Υπηρεσία.' },
        { title: '2. Περιγραφή Υπηρεσίας', content: 'Το AetherLang Ω είναι μια πλατφόρμα Domain-Specific Language (DSL) για ενορχήστρωση AI workflows. Η Υπηρεσία παρέχει επεξεργασία κώδικα, οπτικοποίηση ροής, εκτέλεση, profiling, debugging και χαρακτηριστικά συνεργασίας για εκπαιδευτικούς και επαγγελματικούς σκοπούς.' },
        { title: '3. Ευθύνες Χρήστη', content: 'Είστε υπεύθυνοι για:\n• Τη διατήρηση της εμπιστευτικότητας των API κλειδιών σας\n• Όλες τις δραστηριότητες που συμβαίνουν στη συνεδρία σας\n• Τη συμμόρφωση με ισχύοντες νόμους και κανονισμούς\n• Να μη χρησιμοποιείτε την Υπηρεσία για παράνομους σκοπούς\n• Να μην προσπαθείτε να αντιστρέψετε ή να εκμεταλλευτείτε την Υπηρεσία' },
        { title: '4. Πνευματική Ιδιοκτησία', content: 'Η Υπηρεσία, συμπεριλαμβανομένου του αρχικού περιεχομένου, των χαρακτηριστικών και της λειτουργικότητας, ανήκει στο NeuroDoc και προστατεύεται από διεθνείς νόμους πνευματικής ιδιοκτησίας. Ο κώδικας και τα workflows σας παραμένουν δική σας ιδιοκτησία.' },
        { title: '5. Απόρρητο & Επεξεργασία Δεδομένων', content: 'Επεξεργαζόμαστε δεδομένα σύμφωνα με την Πολιτική Απορρήτου μας και τους κανονισμούς EU GDPR. Ο κώδικας και τα ερωτήματά σας μπορεί να επεξεργαστούν από τα μοντέλα GPT-4o της OpenAI. Δεν αποθηκεύουμε τον κώδικά σας μόνιμα χωρίς τη ρητή συγκατάθεσή σας (π.χ., συνεδρίες συνεργασίας).' },
        { title: '6. Υπηρεσίες Τρίτων', content: 'Η Υπηρεσία ενσωματώνεται με OpenAI APIs. Η χρήση αυτών των ενσωματώσεων υπόκειται στους αντίστοιχους όρους χρήσης τους. Δεν είμαστε υπεύθυνοι για τη διαθεσιμότητα ή τις ενέργειες υπηρεσιών τρίτων.' },
        { title: '7. Αποποιήσεις', content: 'Η ΥΠΗΡΕΣΙΑ ΠΑΡΕΧΕΤΑΙ "ΩΣ ΕΧΕΙ" ΧΩΡΙΣ ΕΓΓΥΗΣΕΙΣ ΟΠΟΙΟΥΔΗΠΟΤΕ ΕΙΔΟΥΣ. Δεν εγγυόμαστε:\n• Αδιάκοπη ή χωρίς σφάλματα λειτουργία\n• Ακρίβεια αποτελεσμάτων που δημιουργούνται από AI\n• Καταλληλότητα για οποιονδήποτε συγκεκριμένο σκοπό\n• Ασφάλεια μετάδοσης δεδομένων' },
        { title: '8. Περιορισμός Ευθύνης', content: 'Στο μέγιστο βαθμό που επιτρέπεται από το νόμο, το NeuroDoc δεν φέρει ευθύνη για οποιεσδήποτε έμμεσες, τυχαίες, ειδικές, επακόλουθες ή τιμωρητικές ζημίες, συμπεριλαμβανομένης της απώλειας κερδών, δεδομένων ή χρήσης, που προκύπτουν από τη χρήση της Υπηρεσίας.' },
        { title: '9. Δικαιώματα Χρηστών ΕΕ', content: 'Οι χρήστες της ΕΕ έχουν το δικαίωμα:\n• Πρόσβασης στα προσωπικά τους δεδομένα\n• Αίτησης διόρθωσης ή διαγραφής δεδομένων\n• Εναντίωσης στην επεξεργασία δεδομένων\n• Φορητότητας δεδομένων\n• Υποβολής καταγγελίας σε εποπτικές αρχές' },
        { title: '10. Αλλαγές στους Όρους', content: 'Διατηρούμε το δικαίωμα να τροποποιούμε αυτούς τους όρους ανά πάσα στιγμή. Η συνεχιζόμενη χρήση της Υπηρεσίας μετά από αλλαγές συνιστά αποδοχή των τροποποιημένων όρων. Οι σημαντικές αλλαγές θα ανακοινώνονται μέσω της πλατφόρμας.' }
      ]
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-2xl border border-purple-500 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
          <div className="p-6 border-b border-slate-700 bg-gradient-to-r from-purple-900/50 to-pink-900/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-8 h-8 text-purple-400" />
                <div>
                  <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                    {content.title}
                  </h2>
                  <p className="text-slate-400 text-sm mt-1">{content.subtitle}</p>
                </div>
              </div>
              <button
                onClick={() => setShowTermsModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {content.sections.map((section, idx) => (
              <div key={idx} className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                <h3 className="text-base font-bold text-purple-400 mb-2">{section.title}</h3>
                <p className="text-slate-300 text-sm whitespace-pre-line leading-relaxed">
                  {section.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Privacy Policy Modal Component
  const PrivacyModal = () => {
    if (!showPrivacyModal) return null;

    const content = language === 'en' ? {
      title: 'Privacy Policy',
      subtitle: 'GDPR Compliant - Last updated: February 2026',
      sections: [
        { title: '1. Data Controller', content: 'NeuroDoc (neurodoc.app) is the data controller responsible for your personal data. We are committed to protecting your privacy and complying with EU General Data Protection Regulation (GDPR) and applicable data protection laws.' },
        { title: '2. Data We Collect', content: 'We collect and process the following data:\n• Technical data: Session IDs, timestamps, browser information\n• Usage data: Code you write, queries you submit, execution logs\n• Collaboration data: User names, session data (when using collaboration features)\n• Performance data: Execution metrics, profiling data\n\nWe do NOT collect: Email addresses, payment information, or personal identifiers (unless voluntarily provided in collaboration features).' },
        { title: '3. Legal Basis for Processing', content: 'We process your data based on:\n• Legitimate interests: Providing and improving the Service\n• Consent: When you use collaboration features\n• Contract performance: When executing your workflows\n• Legal obligations: Compliance with EU and German law' },
        { title: '4. How We Use Your Data', content: 'Your data is used to:\n• Execute AI workflows using OpenAI GPT-4o models\n• Provide visualization, profiling, and debugging features\n• Enable real-time collaboration (when opted-in)\n• Improve service performance and reliability\n• Analyze usage patterns (anonymized)' },
        { title: '5. Data Sharing & Third Parties', content: 'We share data with:\n• OpenAI: Your code and queries are processed by GPT-4o models (subject to OpenAI\'s privacy policy)\n• Hetzner Germany: Infrastructure hosting (EU-based, GDPR compliant)\n\nWe do NOT:\n• Sell your data to third parties\n• Use your data for advertising\n• Share data with non-EU entities (except OpenAI with appropriate safeguards)' },
        { title: '6. Data Retention', content: '• Session data: Stored temporarily during your session, deleted after 24 hours\n• Collaboration sessions: Stored for 30 days or until manually deleted\n• Execution logs: Retained for 7 days for debugging purposes\n• Analytics: Anonymized metrics retained indefinitely' },
        { title: '7. Your Rights (GDPR)', content: 'You have the right to:\n• Access your personal data\n• Request correction of inaccurate data\n• Request deletion of your data ("right to be forgotten")\n• Object to data processing\n• Request data portability\n• Withdraw consent at any time\n• Lodge a complaint with your national Data Protection Authority\n\nTo exercise these rights, contact: privacy@neurodoc.app' },
        { title: '8. Data Security', content: 'We implement appropriate technical and organizational measures:\n• TLS/SSL encryption for data transmission\n• Secure session management\n• Regular security audits\n• Access controls and authentication\n• EU-based infrastructure (Hetzner Germany)\n\nHowever, no internet transmission is 100% secure. Use at your own risk.' },
        { title: '9. Cookies & Tracking', content: 'We use essential cookies for:\n• Session management\n• User preferences (dark mode, language)\n\nWe do NOT use:\n• Advertising cookies\n• Third-party tracking cookies\n• Analytics cookies without consent' },
        { title: '10. International Data Transfers', content: 'Your data is primarily processed within the EU (Hetzner Germany). When using OpenAI services, data may be transferred to the US. OpenAI complies with GDPR requirements through Standard Contractual Clauses (SCCs).' },
        { title: '11. Children\'s Privacy', content: 'The Service is not intended for children under 16. We do not knowingly collect data from children. If you believe we have inadvertently collected such data, contact us immediately for deletion.' },
        { title: '12. Changes to Privacy Policy', content: 'We may update this policy to reflect changes in our practices or legal requirements. Material changes will be communicated via the platform. Continued use after changes constitutes acceptance.' }
      ],
      contact: 'Contact: privacy@neurodoc.app\nData Protection Officer: dpo@neurodoc.app\nHosting: Hetzner Online GmbH, Germany (EU)'
    } : {
      title: 'Πολιτική Απορρήτου',
      subtitle: 'Συμμόρφωση με GDPR - Τελευταία ενημέρωση: Φεβρουάριος 2026',
      sections: [
        { title: '1. Υπεύθυνος Επεξεργασίας Δεδομένων', content: 'Το NeuroDoc (neurodoc.app) είναι ο υπεύθυνος επεξεργασίας δεδομένων για τα προσωπικά σας δεδομένα. Δεσμευόμαστε να προστατεύουμε το απόρρητό σας και να συμμορφωνόμαστε με τον Γενικό Κανονισμό Προστασίας Δεδομένων της ΕΕ (GDPR) και τους ισχύοντες νόμους προστασίας δεδομένων.' },
        { title: '2. Δεδομένα που Συλλέγουμε', content: 'Συλλέγουμε και επεξεργαζόμαστε τα ακόλουθα δεδομένα:\n• Τεχνικά δεδομένα: Session IDs, χρονικές σημάνσεις, πληροφορίες browser\n• Δεδομένα χρήσης: Κώδικας που γράφετε, ερωτήματα που υποβάλλετε, execution logs\n• Δεδομένα συνεργασίας: Ονόματα χρηστών, δεδομένα συνεδρίας (όταν χρησιμοποιείτε χαρακτηριστικά συνεργασίας)\n• Δεδομένα απόδοσης: Μετρήσεις εκτέλεσης, δεδομένα profiling\n\nΔΕΝ συλλέγουμε: Διευθύνσεις email, πληροφορίες πληρωμής ή προσωπικά αναγνωριστικά (εκτός εάν παρέχονται εθελοντικά σε χαρακτηριστικά συνεργασίας).' },
        { title: '3. Νομική Βάση Επεξεργασίας', content: 'Επεξεργαζόμαστε τα δεδομένα σας με βάση:\n• Έννομα συμφέροντα: Παροχή και βελτίωση της Υπηρεσίας\n• Συγκατάθεση: Όταν χρησιμοποιείτε χαρακτηριστικά συνεργασίας\n• Εκτέλεση σύμβασης: Όταν εκτελούνται τα workflows σας\n• Νομικές υποχρεώσεις: Συμμόρφωση με την ΕΕ και τον γερμανικό νόμο' },
        { title: '4. Πώς Χρησιμοποιούμε τα Δεδομένα σας', content: 'Τα δεδομένα σας χρησιμοποιούνται για:\n• Εκτέλεση AI workflows χρησιμοποιώντας μοντέλα OpenAI GPT-4o\n• Παροχή χαρακτηριστικών οπτικοποίησης, profiling και debugging\n• Ενεργοποίηση real-time συνεργασίας (όταν επιλέγεται)\n• Βελτίωση απόδοσης και αξιοπιστίας της υπηρεσίας\n• Ανάλυση προτύπων χρήσης (ανωνυμοποιημένα)' },
        { title: '5. Κοινοποίηση Δεδομένων & Τρίτοι', content: 'Κοινοποιούμε δεδομένα με:\n• OpenAI: Ο κώδικας και τα ερωτήματά σας επεξεργάζονται από μοντέλα GPT-4o (υπόκεινται στην πολιτική απορρήτου της OpenAI)\n• Hetzner Germany: Φιλοξενία υποδομής (με έδρα την ΕΕ, συμμόρφωση με GDPR)\n\nΔΕΝ:\n• Πουλάμε τα δεδομένα σας σε τρίτους\n• Χρησιμοποιούμε τα δεδομένα σας για διαφήμιση\n• Κοινοποιούμε δεδομένα με μη-ΕΕ οντότητες (εκτός από OpenAI με κατάλληλες διασφαλίσεις)' },
        { title: '6. Διατήρηση Δεδομένων', content: '• Δεδομένα συνεδρίας: Αποθηκεύονται προσωρινά κατά τη διάρκεια της συνεδρίας σας, διαγράφονται μετά από 24 ώρες\n• Συνεδρίες συνεργασίας: Αποθηκεύονται για 30 ημέρες ή έως ότου διαγραφούν χειροκίνητα\n• Execution logs: Διατηρούνται για 7 ημέρες για σκοπούς debugging\n• Analytics: Ανωνυμοποιημένες μετρήσεις διατηρούνται επ\' αόριστον' },
        { title: '7. Τα Δικαιώματά σας (GDPR)', content: 'Έχετε το δικαίωμα:\n• Πρόσβασης στα προσωπικά σας δεδομένα\n• Αίτησης διόρθωσης ανακριβών δεδομένων\n• Αίτησης διαγραφής των δεδομένων σας ("δικαίωμα στη λήθη")\n• Εναντίωσης στην επεξεργασία δεδομένων\n• Αίτησης φορητότητας δεδομένων\n• Ανάκλησης συγκατάθεσης ανά πάσα στιγμή\n• Υποβολής καταγγελίας στην εθνική Αρχή Προστασίας Δεδομένων σας\n\nΓια να ασκήσετε αυτά τα δικαιώματα, επικοινωνήστε: privacy@neurodoc.app' },
        { title: '8. Ασφάλεια Δεδομένων', content: 'Εφαρμόζουμε κατάλληλα τεχνικά και οργανωτικά μέτρα:\n• Κρυπτογράφηση TLS/SSL για μετάδοση δεδομένων\n• Ασφαλής διαχείριση συνεδρίας\n• Τακτικοί έλεγχοι ασφαλείας\n• Έλεγχοι πρόσβασης και πιστοποίηση\n• Υποδομή με έδρα την ΕΕ (Hetzner Germany)\n\nΩστόσο, καμία μετάδοση στο διαδίκτυο δεν είναι 100% ασφαλής. Χρησιμοποιείτε με δική σας ευθύνη.' },
        { title: '9. Cookies & Παρακολούθηση', content: 'Χρησιμοποιούμε απαραίτητα cookies για:\n• Διαχείριση συνεδρίας\n• Προτιμήσεις χρήστη (dark mode, γλώσσα)\n\nΔΕΝ χρησιμοποιούμε:\n• Cookies διαφήμισης\n• Cookies παρακολούθησης τρίτων\n• Cookies analytics χωρίς συγκατάθεση' },
        { title: '10. Διεθνείς Μεταφορές Δεδομένων', content: 'Τα δεδομένα σας επεξεργάζονται κυρίως εντός της ΕΕ (Hetzner Germany). Όταν χρησιμοποιείτε υπηρεσίες OpenAI, τα δεδομένα μπορεί να μεταφερθούν στις ΗΠΑ. Η OpenAI συμμορφώνεται με τις απαιτήσεις GDPR μέσω Τυποποιημένων Συμβατικών Ρητρών (SCCs).' },
        { title: '11. Απόρρητο Παιδιών', content: 'Η Υπηρεσία δεν προορίζεται για παιδιά κάτω των 16 ετών. Δεν συλλέγουμε εν γνώσει μας δεδομένα από παιδιά. Εάν πιστεύετε ότι έχουμε συλλέξει εκ παραδρομής τέτοια δεδομένα, επικοινωνήστε μαζί μας αμέσως για διαγραφή.' },
        { title: '12. Αλλαγές στην Πολιτική Απορρήτου', content: 'Μπορούμε να ενημερώσουμε αυτήν την πολιτική για να αντικατοπτρίζουμε αλλαγές στις πρακτικές μας ή τις νομικές απαιτήσεις. Οι σημαντικές αλλαγές θα ανακοινώνονται μέσω της πλατφόρμας. Η συνεχιζόμενη χρήση μετά από αλλαγές συνιστά αποδοχή.' }
      ],
      contact: 'Επικοινωνία: privacy@neurodoc.app\nΥπεύθυνος Προστασίας Δεδομένων: dpo@neurodoc.app\nΦιλοξενία: Hetzner Online GmbH, Germany (EU)'
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-2xl border border-green-500 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
          <div className="p-6 border-b border-slate-700 bg-gradient-to-r from-green-900/50 to-cyan-900/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-8 h-8 text-green-400" />
                <div>
                  <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-cyan-400">
                    {content.title}
                  </h2>
                  <p className="text-slate-400 text-sm mt-1">{content.subtitle}</p>
                </div>
              </div>
              <button
                onClick={() => setShowPrivacyModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {content.sections.map((section, idx) => (
              <div key={idx} className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                <h3 className="text-base font-bold text-green-400 mb-2">{section.title}</h3>
                <p className="text-slate-300 text-sm whitespace-pre-line leading-relaxed">
                  {section.content}
                </p>
              </div>
            ))}
            <div className="bg-gradient-to-r from-green-900/30 to-cyan-900/30 rounded-lg p-4 border border-green-700/50 mt-6">
              <p className="text-slate-300 text-sm whitespace-pre-line leading-relaxed">
                {content.contact}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Main application screen
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-slate-800 rounded-2xl shadow-2xl p-6 mb-6 border border-purple-500">
          <div className="flex flex-col md:flex-row items-center md:justify-between gap-3">
            <div className="flex items-center gap-4">
              <Cpu className="w-10 h-10 text-cyan-400" />
              <div>
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400">
                  AetherLang Ω
                </h1>
                <p className="text-slate-400 text-sm">
                  DSL Orchestration Engine v0.2.0 Pro - Elite Access Mode
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2 justify-center md:justify-end">
              {/* BYOK Tier Button */}
              <button
                onClick={() => setShowApiKeyModal(true)}
                className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${
                  userTier === 'unlimited'
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-orange-600 hover:bg-orange-700 text-white'
                }`}
                title={userTier === 'unlimited' ? 'BYOK Active - Unlimited' : `Free Tier: ${usageStats.remaining}/${usageStats.limit} left`}
              >
                <Server className="w-4 h-4" />
                {userTier === 'unlimited' ? (
                  <span className="font-bold">∞ BYOK</span>
                ) : (
                  <span className="font-bold">{usageStats.remaining}/{usageStats.limit}</span>
                )}
              </button>

              {/* GitHub Sponsor Button */}
              <a
                href="https://github.com/sponsors/contrario"
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-2 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 rounded-lg text-white transition-all hover:scale-105 flex items-center gap-2 font-medium"
                title={language === 'en' ? 'Support AetherLang' : 'Στηρίξτε το AetherLang'}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
                  <path fillRule="evenodd" d="M4.25 2.5c-1.336 0-2.75 1.164-2.75 3 0 2.15 1.58 4.144 3.365 5.682A20.565 20.565 0 008 13.393a20.561 20.561 0 003.135-2.211C12.92 9.644 14.5 7.65 14.5 5.5c0-1.836-1.414-3-2.75-3-1.373 0-2.609.986-3.029 2.456a.75.75 0 01-1.442 0C6.859 3.486 5.623 2.5 4.25 2.5z"/>
                </svg>
                <span className="hidden sm:inline">{language === 'en' ? 'Sponsor' : 'Στήριξη'}</span>
              </a>

              {/* Telegram Bot Button */}
              <a
                href="https://t.me/aetherlang_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-lg text-white transition-all hover:scale-105 flex items-center gap-2 font-medium"
                title={language === 'en' ? 'Try AetherLang Bot — 15 AI Engines on Telegram' : 'Δοκιμάστε το AetherLang Bot — 15 AI Engines στο Telegram'}
              >
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">{language === 'en' ? 'Bot' : 'Bot'}</span>
              </a>

              <button
                onClick={() => setShowInfoModal(true)}
                className="px-3 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors flex items-center gap-2"
                title="Information & Help"
              >
                <Info className="w-4 h-4" />
                Info
              </button>
              <button
                onClick={() => setLanguage(language === 'en' ? 'el' : 'en')}
                className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
                title="Toggle Language"
              >
                <Globe className="w-4 h-4" />
                {language === 'en' ? '🇺🇸 EN' : '🇬🇷 EL'}
              </button>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                title="Toggle Dark Mode"
              >
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button
                onClick={exportFlow}
                className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              <label className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg transition-colors flex items-center gap-2 cursor-pointer">
                <Upload className="w-4 h-4" />
                Import
                <input type="file" accept=".json" onChange={importFlow} className="hidden" />
              </label>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6">
          {/* Sidebar - Examples */}
          <div className="col-span-1 md:col-span-3">
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center gap-2 mb-4">
                <ListTree className="w-5 h-5 text-cyan-400" />
                <h2 className="text-lg font-bold text-cyan-400">{language === "en" ? "Examples" : "Παραδείγματα"}</h2>
              </div>
              <div className="space-y-2">
                {examples.map((example) => (
                  <button
                    key={example.id}
                    onClick={() => loadExample(example.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedExample === example.id
                        ? 'bg-purple-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    <div className="font-semibold text-sm">{t(example.name, language)}</div>
                    <div className="text-xs opacity-75 mt-1">{t(example.description, language)}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Stats Panel */}
            {result && (
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mt-4">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart3 className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-lg font-bold text-cyan-400">Stats</h2>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-sm flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Duration
                    </span>
                    <span className="text-white font-bold">
                      {result.result?.duration_seconds?.toFixed(2)}s
                    </span>
                  </div>
                  {result.result?.execution_log && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-sm flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        Steps
                      </span>
                      <span className="text-white font-bold">
                        {result.result.execution_log.filter(log => log.node !== 'SYSTEM').length}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-sm flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Status
                    </span>
                    <span className={`font-bold ${
                      result.status === 'success' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {result.status === 'success' ? 'Success' : 'Failed'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="col-span-1 md:col-span-9 space-y-6">
            {/* Code Editor */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-lg font-bold text-cyan-400">Flow Definition</h2>
                </div>
                <button
                  onClick={validateCode}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg
                           transition-colors flex items-center gap-2 text-sm"
                >
                  <CheckCircle className="w-4 h-4" />
                  Validate
                </button>
              </div>
              <SimpleCodeEditor value={code} onChange={setCode} />
            </div>

            {/* Flow Visualization */}
            {parsedFlow && showVisualization && (
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
                  <div className="flex items-center gap-2">
                    <Eye className="w-5 h-5 text-cyan-400" />
                    <h2 className="text-lg font-bold text-cyan-400">Flow Visualization</h2>
                  </div>

                  {/* Layout Controls */}
                  <div className="flex items-center gap-2">
                    <select
                      value={selectedLayout}
                      onChange={(e) => setSelectedLayout(e.target.value)}
                      className="px-3 py-1 bg-slate-700 text-white text-sm rounded border border-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    >
                      <option value="auto">Auto Layout</option>
                      <option value="hierarchical">Hierarchical</option>
                      <option value="circular">Circular</option>
                      <option value="grid">Grid</option>
                      <option value="tree">Tree</option>
                      <option value="force">Physics</option>
                    </select>

                    <button
                      onClick={applyLayout}
                      disabled={isApplyingLayout}
                      className="px-3 py-1 bg-cyan-600 hover:bg-cyan-700 text-white text-sm rounded transition-colors disabled:opacity-50"
                      title="Apply selected layout"
                    >
                      {isApplyingLayout ? '...' : 'Apply'}
                    </button>

                    <button
                      onClick={() => setShowVisualization(!showVisualization)}
                      className="text-sm text-slate-400 hover:text-slate-200"
                    >
                      Hide
                    </button>
                  </div>
                </div>
                <ErrorBoundary>
                  <FlowVisualization
                    flowData={parsedFlow}
                    executionStatus={executionStatus}
                    bottlenecks={aiAnalysis?.issues?.bottlenecks || []}
                    layoutPositions={layoutPositions}
                  />
                </ErrorBoundary>
              </div>
            )}

            {/* Query Input */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center gap-2 mb-3">
                <Terminal className="w-5 h-5 text-cyan-400" />
                <h2 className="text-lg font-bold text-cyan-400">Query Input</h2>
              </div>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Εισάγετε το ερώτημά σας εδώ..."
                className="w-full p-3 bg-slate-900 text-green-400 font-mono text-sm
                         rounded-lg border border-slate-700 focus:outline-none focus:ring-2
                         focus:ring-cyan-500 resize-none"
                rows={3}
              />

              {/* Profiling Toggle */}
              <div className="mt-3 flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enableProfiling"
                  checked={enableProfiling}
                  onChange={(e) => setEnableProfiling(e.target.checked)}
                  className="w-4 h-4 text-cyan-500 bg-slate-700 border-slate-600 rounded focus:ring-cyan-500"
                />
                <label htmlFor="enableProfiling" className="text-sm text-slate-300 flex items-center gap-2 cursor-pointer">
                  <BarChart3 className="w-4 h-4 text-cyan-400" />
                  Enable Performance Profiling
                  <span className="text-xs text-slate-500">(adds ~100ms overhead)</span>
                </label>
              </div>

              {/* Debugging Toggle */}
              <div className="mt-2 flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enableDebugging"
                  checked={enableDebugging}
                  onChange={(e) => setEnableDebugging(e.target.checked)}
                  className="w-4 h-4 text-purple-500 bg-slate-700 border-slate-600 rounded focus:ring-purple-500"
                />
                <label htmlFor="enableDebugging" className="text-sm text-slate-300 flex items-center gap-2 cursor-pointer">
                  <Clock className="w-4 h-4 text-purple-400" />
                  Enable Time-Travel Debugging
                  <span className="text-xs text-slate-500">(records execution history)</span>
                </label>
              </div>

              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                <button
                  onClick={executeFlow}
                  disabled={executing}
                  className={`py-3 bg-gradient-to-r from-cyan-500 to-purple-500
                           text-white font-bold rounded-lg transition-all duration-200
                           flex items-center justify-center gap-2 ${
                             executing ? 'opacity-50 cursor-not-allowed' : 'hover:from-cyan-600 hover:to-purple-600'
                           }`}
                >
                  {executing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" />
                      Execute Flow
                    </>
                  )}
                </button>

                <button
                  onClick={analyzeFlow}
                  disabled={isAnalyzing}
                  className={`py-3 bg-gradient-to-r from-orange-500 to-pink-500
                           text-white font-bold rounded-lg transition-all duration-200
                           flex items-center justify-center gap-2 ${
                             isAnalyzing ? 'opacity-50 cursor-not-allowed' : 'hover:from-orange-600 hover:to-pink-600'
                           }`}
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="w-5 h-5" />
                      Analyze Performance
                    </>
                  )}
                </button>
              </div>

              {/* Execution Progress Bar */}
              {executing && executionProgress > 0 && (
                <div className="mt-3">
                  <div className="flex items-center justify-between text-xs text-cyan-400 mb-1">
                    <span>Progress</span>
                    <span>{executionProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-purple-500 h-full rounded-full transition-all duration-300"
                      style={{ width: `${executionProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Keyboard Shortcuts Hint */}
              <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                <Keyboard className="w-3 h-3" />
                <span>Shortcuts: Ctrl+K (Validate) • Ctrl+Enter (Execute) • Ctrl+S (Export)</span>
              </div>
            </div>

            {/* Results */}
            {result && (
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-cyan-400" />
                    <h2 className="text-lg font-bold text-cyan-400">Execution Results</h2>
                  </div>
                  <div className="flex items-center gap-2">
                    {profileData && (
                      <button
                        onClick={() => setShowProfileViewer(true)}
                        className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
                      >
                        <BarChart3 className="w-4 h-4" />
                        View Profile
                      </button>
                    )}
                    {debugSessionId && (
                      <button
                        onClick={() => setShowDebugger(true)}
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
                      >
                        <Clock className="w-4 h-4" />
                        Open Debugger
                      </button>
                    )}
                  </div>
                </div>
                <ResultPanel result={result} />
              </div>
            )}

            {/* AI Insights Panel */}
            {aiAnalysis && showAiInsights && (
              <div className="bg-slate-800 rounded-xl p-4 border border-pink-500 shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-pink-400" />
                    <h2 className="text-lg font-bold text-pink-400">🧠 AI Performance Insights</h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={applyOptimizations}
                      disabled={isOptimizing}
                      className={`px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500
                               hover:from-green-600 hover:to-emerald-600 text-white font-bold
                               rounded-lg transition-colors flex items-center gap-2 text-sm ${
                                 isOptimizing ? 'opacity-50 cursor-not-allowed' : ''
                               }`}
                    >
                      {isOptimizing ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Applying...
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4" />
                          Apply All Fixes
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => setShowAiInsights(false)}
                      className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      Hide
                    </button>
                  </div>
                </div>
                <ErrorBoundary>
                  <AIInsightsPanel analysis={aiAnalysis} />
                </ErrorBoundary>
              </div>
            )}

            {/* Diff Modal */}
            <DiffModal
              isOpen={showDiffModal}
              onClose={() => setShowDiffModal(false)}
              diffData={optimizedCode}
              onAccept={acceptOptimizations}
            />

            {/* Profile Viewer */}
            {showProfileViewer && profileData && (
              <ProfileViewer
                profile={profileData}
                onClose={() => setShowProfileViewer(false)}
              />
            )}

            {/* Debugger Panel */}
            {showDebugger && debugSessionId && (
              <DebuggerPanel
                sessionId={debugSessionId}
                onClose={() => setShowDebugger(false)}
                apiBase={API_BASE}
                authKey={ADMIN_KEY}
              />
            )}

            {/* Collaboration Panel */}
            {showCollaboration && (
              <CollaborationPanel
                sessionId={collaborationSessionId}
                userId={currentUserId}
                userName={currentUserName}
                onSessionChange={(session) => {
                  setCollaborationSessionId(session.session_id);
                  if (session.code) setCode(session.code);
                  if (session.query) setQuery(session.query);
                }}
                onClose={() => setShowCollaboration(false)}
                apiBase={API_BASE}
                authKey={ADMIN_KEY}
              />
            )}

            {/* Legal Compliance Modals */}
            <InfoModal />
            <TermsModal />
            <PrivacyModal />
            <ApiKeyModal />

            {/* Floating Collaboration Button */}
            <button
              onClick={() => setShowCollaboration(true)}
              className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 rounded-full shadow-2xl flex items-center justify-center text-white transition-all duration-200 hover:scale-110 z-40"
              title="Open Collaboration"
            >
              <Users className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Professional Footer */}
        <footer className="mt-16 bg-gradient-to-b from-slate-800 to-slate-900 rounded-3xl border border-slate-700/50 shadow-2xl overflow-hidden">
          {/* Top Gradient Accent */}
          <div className="h-1 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500"></div>

          <div className="px-10 py-12">
            {/* Main Grid */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-12 mb-12">

              {/* Column 1: About - Spans 4 columns */}
              <div className="md:col-span-4">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-cyan-500/10 rounded-xl border border-cyan-500/20">
                    <Cpu className="w-6 h-6 text-cyan-400" />
                  </div>
                  <h3 className="text-xl font-bold tracking-tight text-white">
                    {language === 'en' ? 'About AetherLang Ω' : 'Σχετικά με το AetherLang Ω'}
                  </h3>
                </div>

                <p className="text-slate-300 text-[15px] leading-[1.75] mb-6 font-light">
                  {language === 'en'
                    ? 'Professional AI Workflow Orchestration DSL with 28 specialized node types, real-time collaboration, and AI-powered optimization.'
                    : 'Επαγγελματική DSL Ενορχήστρωσης AI Workflows με 28 εξειδικευμένους τύπους κόμβων, real-time συνεργασία και AI-powered βελτιστοποίηση.'}
                </p>

                {/* Meta Information */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-slate-400 text-sm group">
                    <CheckCircle className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                    <span className="group-hover:text-slate-300 transition-colors">
                      {language === 'en' ? 'Version 0.2.0 Pro' : 'Έκδοση 0.2.0 Pro'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-400 text-sm group">
                    <Server className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                    <span className="group-hover:text-slate-300 transition-colors">
                      {language === 'en' ? 'Hosted: Hetzner Germany (EU)' : 'Φιλοξενία: Hetzner Γερμανία (ΕΕ)'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-400 text-sm group">
                    <Shield className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                    <span className="group-hover:text-slate-300 transition-colors">
                      {language === 'en' ? 'GDPR Compliant' : 'Συμμόρφωση GDPR'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Column 2: Legal - Spans 3 columns */}
              <div className="md:col-span-3">
                <div className="flex items-center gap-3 mb-6">
                  <Shield className="w-5 h-5 text-purple-400" />
                  <h3 className="text-base font-bold tracking-tight text-white uppercase text-xs letter-spacing-wider">
                    {language === 'en' ? 'Legal' : 'Νομικά'}
                  </h3>
                </div>

                <nav className="space-y-3">
                  <button
                    onClick={() => setShowTermsModal(true)}
                    className="group flex items-center gap-2 text-slate-400 hover:text-cyan-400 text-[15px] transition-all duration-200 w-full text-left"
                  >
                    <span className="text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                    <span className="group-hover:translate-x-1 transition-transform duration-200">
                      {language === 'en' ? 'Terms of Service' : 'Όροι Χρήσης'}
                    </span>
                  </button>

                  <button
                    onClick={() => setShowPrivacyModal(true)}
                    className="group flex items-center gap-2 text-slate-400 hover:text-cyan-400 text-[15px] transition-all duration-200 w-full text-left"
                  >
                    <span className="text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                    <span className="group-hover:translate-x-1 transition-transform duration-200">
                      {language === 'en' ? 'Privacy Policy' : 'Πολιτική Απορρήτου'}
                    </span>
                  </button>

                  <button
                    onClick={() => setShowInfoModal(true)}
                    className="group flex items-center gap-2 text-slate-400 hover:text-cyan-400 text-[15px] transition-all duration-200 w-full text-left"
                  >
                    <span className="text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                    <span className="group-hover:translate-x-1 transition-transform duration-200">
                      {language === 'en' ? 'About & Help' : 'Σχετικά & Βοήθεια'}
                    </span>
                  </button>
                </nav>

                {/* EU Badge */}
                <div className="mt-6 p-4 bg-slate-950/50 rounded-xl border border-slate-700/50 backdrop-blur-sm">
                  <div className="flex items-start gap-2">
                    <span className="text-lg">🇪🇺</span>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {language === 'en'
                        ? 'EU Data Protection compliant. GDPR certified.'
                        : 'Συμμόρφωση με την Προστασία Δεδομένων της ΕΕ. Πιστοποίηση GDPR.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Column 3: Resources - Spans 3 columns */}
              <div className="md:col-span-3">
                <div className="flex items-center gap-3 mb-6">
                  <Code2 className="w-5 h-5 text-green-400" />
                  <h3 className="text-base font-bold tracking-tight text-white uppercase text-xs letter-spacing-wider">
                    {language === 'en' ? 'Resources' : 'Πόροι'}
                  </h3>
                </div>

                <nav className="space-y-3 mb-6">
                  <a
                    href="https://github.com/contrario/aetherlang"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex items-center gap-2 text-slate-400 hover:text-cyan-400 text-[15px] transition-all duration-200"
                  >
                    <span className="text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                    <span className="group-hover:translate-x-1 transition-transform duration-200">
                      {language === 'en' ? 'GitHub Repository' : 'Αποθετήριο GitHub'}
                    </span>
                  </a>

                  <a
                    href="https://github.com/contrario/aetherlang#-quick-start"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex items-center gap-2 text-slate-400 hover:text-cyan-400 text-[15px] transition-all duration-200"
                  >
                    <span className="text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                    <span className="group-hover:translate-x-1 transition-transform duration-200">
                      {language === 'en' ? 'Documentation' : 'Τεκμηρίωση'}
                    </span>
                  </a>

                  <a
                    href="https://github.com/contrario/aetherlang/tree/main/examples"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex items-center gap-2 text-slate-400 hover:text-cyan-400 text-[15px] transition-all duration-200"
                  >
                    <span className="text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                    <span className="group-hover:translate-x-1 transition-transform duration-200">
                      {language === 'en' ? 'Code Examples' : 'Παραδείγματα Κώδικα'}
                    </span>
                  </a>
                </nav>

                {/* Open Source Badge */}
                <div className="relative p-5 bg-gradient-to-br from-cyan-900/20 via-purple-900/20 to-pink-900/20 rounded-xl border border-cyan-500/20 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-purple-500/5"></div>
                  <div className="relative">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">🚀</span>
                      <p className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
                        {language === 'en' ? 'Open Source' : 'Ανοιχτός Κώδικας'}
                      </p>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {language === 'en'
                        ? 'MIT License. Contributions welcome!'
                        : 'Άδεια MIT. Οι συνεισφορές είναι ευπρόσδεκτες!'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Column 4: Support - Spans 2 columns */}
              <div className="md:col-span-2">
                <h4 className="text-white font-semibold mb-3 text-sm">
                  {language === 'en' ? 'Support' : 'Υποστήριξη'}
                </h4>
                <div className="space-y-2">
                  <a
                    href="https://github.com/sponsors/contrario"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 rounded-lg text-white text-sm font-medium transition-all hover:scale-105 w-fit"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
                      <path fillRule="evenodd" d="M4.25 2.5c-1.336 0-2.75 1.164-2.75 3 0 2.15 1.58 4.144 3.365 5.682A20.565 20.565 0 008 13.393a20.561 20.561 0 003.135-2.211C12.92 9.644 14.5 7.65 14.5 5.5c0-1.836-1.414-3-2.75-3-1.373 0-2.609.986-3.029 2.456a.75.75 0 01-1.442 0C6.859 3.486 5.623 2.5 4.25 2.5z"/>
                    </svg>
                    {language === 'en' ? 'Sponsor on GitHub' : 'Στηρίξτε το Έργο'}
                  </a>

                  <a
                    href="https://github.com/contrario/aetherlang"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-slate-400 hover:text-yellow-400 text-sm transition-colors"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/>
                    </svg>
                    {language === 'en' ? 'Star on GitHub' : 'Αστέρι στο GitHub'}
                  </a>
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="relative h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent mb-8"></div>

            {/* Copyright Bar */}
            <div className="space-y-3">
              <div className="flex flex-col md:flex-row items-center justify-center gap-2 text-slate-500 text-sm">
                <span className="flex items-center gap-2">
                  © 2025-2026 <span className="text-cyan-400 font-semibold">AetherLang Ω</span>
                </span>
                <span className="hidden md:inline text-slate-700">•</span>
                <span>NeuroDoc Platform</span>
                <span className="hidden md:inline text-slate-700">•</span>
                <span className="flex items-center gap-1">
                  {language === 'en' ? 'Made with' : 'Δημιουργήθηκε με'}
                  <span className="text-red-400 animate-pulse">❤️</span>
                  {language === 'en' ? 'for AI Engineers' : 'για AI Engineers'}
                </span>
                <span className="hidden md:inline text-slate-700">•</span>
                <a
                  href="https://github.com/sponsors/contrario"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-pink-400 hover:text-pink-300 transition-colors text-xs"
                >
                  ❤️ {language === 'en' ? 'Sponsor this project' : 'Στηρίξτε μας'}
                </a>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-2 text-slate-600 text-xs">
                <span className="px-2 py-1 bg-slate-800/50 rounded-md">OpenAI GPT-4o</span>
                <span className="text-slate-700">•</span>
                <span className="px-2 py-1 bg-slate-800/50 rounded-md">FastAPI</span>
                <span className="text-slate-700">•</span>
                <span className="px-2 py-1 bg-slate-800/50 rounded-md">React</span>
                <span className="text-slate-700">•</span>
                <span className="px-2 py-1 bg-slate-800/50 rounded-md">Tailwind CSS</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
