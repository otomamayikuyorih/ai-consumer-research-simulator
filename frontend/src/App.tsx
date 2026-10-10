import React, { useState, useEffect } from 'react';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { PersonaGeneratorView } from './components/PersonaGeneratorView';
import { SurveyBuilderView } from './components/SurveyBuilderView';
import { SurveyRunnerView } from './components/SurveyRunnerView';
import { AnalysisView } from './components/AnalysisView';
import { InterviewView } from './components/InterviewView';
import { ConceptEvaluationView } from './components/ConceptEvaluationView';
import { VirtualABView } from './components/VirtualABView';
import { ValidationView } from './components/ValidationView';
import { Cohort, Survey, Persona } from './types';
import { fetchCohorts, fetchSurveys, fetchSystemStatus } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [activeCohort, setActiveCohort] = useState<Cohort | null>(null);
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [activeSurvey, setActiveSurvey] = useState<Survey | null>(null);
  const [targetPersona, setTargetPersona] = useState<Persona | null>(null);
  const [systemStatus, setSystemStatus] = useState<{ has_gemini_key: boolean; mode: string } | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [status, cohortsList, surveysList] = await Promise.all([
        fetchSystemStatus(),
        fetchCohorts(),
        fetchSurveys(),
      ]);

      setSystemStatus(status);
      setCohorts(cohortsList);
      if (cohortsList.length > 0) {
        setActiveCohort(cohortsList[0]);
      }

      setSurveys(surveysList);
      if (surveysList.length > 0) {
        setActiveSurvey(surveysList[0]);
      }
    } catch (err) {
      console.error('Initial data load error:', err);
    }
  };

  const handleCohortCreated = (newCohort: Cohort) => {
    setCohorts((prev) => [newCohort, ...prev]);
    setActiveCohort(newCohort);
  };

  const handleSurveyCreated = (newSurvey: Survey) => {
    setSurveys((prev) => [newSurvey, ...prev]);
    setActiveSurvey(newSurvey);
  };

  const handleStartInterviewWithPersona = (persona: Persona) => {
    setTargetPersona(persona);
    setCurrentTab('interview');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-['Noto_Sans_JP',sans-serif]">
      {/* Simulation Disclaimer Banner */}
      <DisclaimerBanner />

      {/* Main Top Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        systemStatus={systemStatus}
        activeCohortName={activeCohort?.name}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'dashboard' && (
          <DashboardView
            cohorts={cohorts}
            surveys={surveys}
            onNavigate={setCurrentTab}
            onSelectCohort={(c) => setActiveCohort(c)}
            onSelectSurvey={(s) => setActiveSurvey(s)}
          />
        )}

        {currentTab === 'personas' && (
          <PersonaGeneratorView
            cohorts={cohorts}
            activeCohort={activeCohort}
            onCohortCreated={handleCohortCreated}
            onSelectCohort={(c) => setActiveCohort(c)}
            onStartInterviewWithPersona={handleStartInterviewWithPersona}
          />
        )}

        {currentTab === 'builder' && (
          <SurveyBuilderView
            cohorts={cohorts}
            activeCohort={activeCohort}
            onSurveyCreated={handleSurveyCreated}
            onNavigateToRunner={(s) => {
              setActiveSurvey(s);
              setCurrentTab('runner');
            }}
          />
        )}

        {currentTab === 'runner' && (
          <SurveyRunnerView
            surveys={surveys}
            cohorts={cohorts}
            activeSurvey={activeSurvey}
            onSelectSurvey={(s) => setActiveSurvey(s)}
            onNavigateToAnalysis={(s) => {
              setActiveSurvey(s);
              setCurrentTab('analytics');
            }}
            systemStatus={systemStatus}
          />
        )}

        {currentTab === 'analytics' && (
          <AnalysisView
            surveys={surveys}
            activeSurvey={activeSurvey}
            onSelectSurvey={(s) => setActiveSurvey(s)}
          />
        )}

        {currentTab === 'ab_test' && (
          <VirtualABView
            cohorts={cohorts}
            activeCohort={activeCohort}
            onSelectCohort={(c) => setActiveCohort(c)}
          />
        )}

        {currentTab === 'validation' && (
          <ValidationView
            surveys={surveys}
            activeSurvey={activeSurvey}
            onSelectSurvey={(s) => setActiveSurvey(s)}
          />
        )}

        {currentTab === 'interview' && (
          <InterviewView
            cohorts={cohorts}
            activeCohort={activeCohort}
            targetPersona={targetPersona}
            onSelectPersona={(p) => setTargetPersona(p)}
          />
        )}

        {currentTab === 'concept' && (
          <ConceptEvaluationView
            cohorts={cohorts}
            activeCohort={activeCohort}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© 2026 AI Consumer Research Simulator - 統計的合成生活者調査基盤</p>
          <p className="text-[11px] text-slate-400">
            Powered by FastAPI, React, pandas, scikit-learn & Google Gemini API
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;
