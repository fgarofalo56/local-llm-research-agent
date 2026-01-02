/**
 * Onboarding Status Hook
 * Manages onboarding completion state in localStorage
 */

import { useState } from 'react';

const ONBOARDING_COMPLETE_KEY = 'onboardingComplete';

export function useOnboardingStatus() {
  const [showOnboarding, setShowOnboarding] = useState(() => {
    // Initialize state from localStorage synchronously to avoid flash
    if (typeof window !== 'undefined') {
      return !localStorage.getItem(ONBOARDING_COMPLETE_KEY);
    }
    return false;
  });

  const completeOnboarding = () => {
    localStorage.setItem(ONBOARDING_COMPLETE_KEY, 'true');
    setShowOnboarding(false);
  };

  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_COMPLETE_KEY);
    setShowOnboarding(true);
  };

  return { showOnboarding, completeOnboarding, resetOnboarding };
}
