/**
 * Onboarding Wizard Component
 * Phase 2.5: Advanced Features & Polish
 *
 * First-time user onboarding flow with welcome, health check, and sample queries.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Check,
  ChevronRight,
  Database,
  FileSearch,
  MessageSquare,
  Server,
  Sparkles,
  X,
} from 'lucide-react';
import { api } from '../../api/client';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import type { HealthStatus } from '../../types';

interface OnboardingWizardProps {
  onComplete: () => void;
  onSkip: () => void;
}

// Status indicator component - defined outside to prevent recreation on each render
interface StatusIndicatorProps {
  status: string;
}

function StatusIndicator({ status }: StatusIndicatorProps) {
  const colors: Record<string, string> = {
    healthy: 'bg-green-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-yellow-500',
  };
  return (
    <div
      className={`h-3 w-3 rounded-full ${colors[status] || colors.unknown}`}
    />
  );
}

export function OnboardingWizard({ onComplete, onSkip }: OnboardingWizardProps) {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health'),
    enabled: step === 1,
  });

  const steps = [
    { id: 'welcome', title: 'Welcome', icon: Sparkles },
    { id: 'health', title: 'System Check', icon: Server },
    { id: 'explore', title: 'Explore', icon: FileSearch },
    { id: 'ready', title: 'Ready!', icon: Check },
  ];

  const sampleQueries = [
    {
      title: 'List all tables',
      description: 'See all available tables in your database',
      query: 'What tables are available in the database?',
    },
    {
      title: 'Top researchers',
      description: 'Find the most productive researchers',
      query: 'Show me the top 5 researchers by publication count',
    },
    {
      title: 'Active projects',
      description: 'View all currently active projects',
      query: 'List all active projects with their budgets',
    },
    {
      title: 'Department overview',
      description: 'Get a summary of all departments',
      query: 'Give me an overview of all departments and their researcher counts',
    },
  ];

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    } else {
      onComplete();
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const handleTryQuery = (query: string) => {
    // Navigate to chat with the query
    navigate(`/chat?query=${encodeURIComponent(query)}`);
    onComplete();
  };

  const getServiceStatus = (serviceName: string) => {
    const service = health?.services.find((s) => s.name === serviceName);
    return service?.status || 'unknown';
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {(() => {
              const Icon = steps[step].icon;
              return <Icon className="h-5 w-5" />;
            })()}
            {steps[step].title}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onSkip}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Progress Indicators */}
          <div className="flex gap-2 justify-center">
            {steps.map((s, i) => (
              <div
                key={s.id}
                className={`h-2 w-12 rounded-full transition-colors ${
                  i <= step ? 'bg-primary' : 'bg-muted'
                }`}
              />
            ))}
          </div>

          {/* Step Content */}
          {step === 0 && (
            <div className="text-center space-y-4 py-6">
              <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold">Welcome to Local LLM Research Agent</h2>
              <p className="text-muted-foreground max-w-md mx-auto">
                A powerful 100% local AI assistant for SQL Server data analytics.
                All processing happens on your machine - your data stays private.
              </p>
              <div className="grid grid-cols-3 gap-4 pt-4">
                <div className="text-center">
                  <MessageSquare className="h-8 w-8 mx-auto text-primary mb-2" />
                  <p className="text-sm font-medium">Natural Language</p>
                  <p className="text-xs text-muted-foreground">Ask questions in plain English</p>
                </div>
                <div className="text-center">
                  <Database className="h-8 w-8 mx-auto text-primary mb-2" />
                  <p className="text-sm font-medium">SQL Server</p>
                  <p className="text-xs text-muted-foreground">Query your databases directly</p>
                </div>
                <div className="text-center">
                  <Server className="h-8 w-8 mx-auto text-primary mb-2" />
                  <p className="text-sm font-medium">100% Local</p>
                  <p className="text-xs text-muted-foreground">Privacy-first design</p>
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <p className="text-muted-foreground">
                Let's check that all services are running properly.
              </p>

              {healthLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-lg border">
                    <div className="flex items-center gap-3">
                      <Server className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Ollama (LLM)</p>
                        <p className="text-xs text-muted-foreground">Local language model</p>
                      </div>
                    </div>
                    <StatusIndicator status={getServiceStatus('ollama')} />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg border">
                    <div className="flex items-center gap-3">
                      <Database className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">SQL Server</p>
                        <p className="text-xs text-muted-foreground">Database connection</p>
                      </div>
                    </div>
                    <StatusIndicator status={getServiceStatus('sql_server')} />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg border">
                    <div className="flex items-center gap-3">
                      <Server className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">Redis</p>
                        <p className="text-xs text-muted-foreground">Vector store & caching</p>
                      </div>
                    </div>
                    <StatusIndicator status={getServiceStatus('redis')} />
                  </div>
                </div>
              )}

              {health && health.services.some((s) => s.status !== 'healthy') && (
                <p className="text-sm text-amber-500">
                  Some services are not healthy. The app will still work, but some features may be limited.
                </p>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <p className="text-muted-foreground">
                Try one of these sample queries to explore your data:
              </p>

              <div className="grid gap-3">
                {sampleQueries.map((sq) => (
                  <button
                    key={sq.title}
                    onClick={() => handleTryQuery(sq.query)}
                    className="flex items-center justify-between p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors text-left"
                  >
                    <div>
                      <p className="font-medium">{sq.title}</p>
                      <p className="text-sm text-muted-foreground">{sq.description}</p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="text-center space-y-4 py-6">
              <div className="mx-auto w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
                <Check className="h-8 w-8 text-green-500" />
              </div>
              <h2 className="text-2xl font-bold">You're all set!</h2>
              <p className="text-muted-foreground max-w-md mx-auto">
                Start asking questions about your data. The AI will help you explore,
                analyze, and visualize your SQL Server databases.
              </p>
              <div className="pt-4">
                <p className="text-sm text-muted-foreground">
                  Pro tip: Use keyboard shortcuts for faster navigation.
                  Press <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">?</kbd> to see all shortcuts.
                </p>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="ghost" onClick={handleBack} disabled={step === 0}>
              Back
            </Button>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={onSkip}>
                Skip
              </Button>
              <Button onClick={handleNext}>
                {step === steps.length - 1 ? 'Get Started' : 'Next'}
                {step < steps.length - 1 && <ChevronRight className="h-4 w-4 ml-1" />}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default OnboardingWizard;
