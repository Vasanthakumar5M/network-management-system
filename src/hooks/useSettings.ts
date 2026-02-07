/**
 * Hook for managing application settings
 */

import { useState, useCallback, useEffect } from 'react';
import { settings } from '@/lib/api';
import type { AppSettings } from '@/types';

const defaultSettings: AppSettings = {
  theme: 'dark',
  language: 'en',
  refreshInterval: 5000,
  showRawData: false,
  blurPasswords: true,
  hidesSensitiveData: true,
  notifications: {
    desktop: true,
    sound: true,
    email: false,
  },
  stealth: {
    enabled: true,
    deviceProfile: 'hp_printer',
    changeMac: true,
    changeHostname: true,
  },
};

interface UseSettingsState {
  settings: AppSettings;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  hasChanges: boolean;
}

export function useSettings() {
  const [state, setState] = useState<UseSettingsState>({
    settings: defaultSettings,
    isLoading: true,
    isSaving: false,
    error: null,
    hasChanges: false,
  });

  const [originalSettings, setOriginalSettings] = useState<AppSettings>(defaultSettings);

  // Fetch settings
  const fetchSettings = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const data = await settings.get();
      setState({
        settings: data,
        isLoading: false,
        isSaving: false,
        error: null,
        hasChanges: false,
      });
      setOriginalSettings(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch settings';
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
    }
  }, []);

  // Update a single setting
  const updateSetting = useCallback(<K extends keyof AppSettings>(
    key: K,
    value: AppSettings[K]
  ) => {
    setState((prev) => ({
      ...prev,
      settings: { ...prev.settings, [key]: value },
      hasChanges: true,
    }));
  }, []);

  // Update nested notification settings
  const updateNotificationSetting = useCallback(<K extends keyof AppSettings['notifications']>(
    key: K,
    value: AppSettings['notifications'][K]
  ) => {
    setState((prev) => ({
      ...prev,
      settings: {
        ...prev.settings,
        notifications: { ...prev.settings.notifications, [key]: value },
      },
      hasChanges: true,
    }));
  }, []);

  // Update nested stealth settings
  const updateStealthSetting = useCallback(<K extends keyof AppSettings['stealth']>(
    key: K,
    value: AppSettings['stealth'][K]
  ) => {
    setState((prev) => ({
      ...prev,
      settings: {
        ...prev.settings,
        stealth: { ...prev.settings.stealth, [key]: value },
      },
      hasChanges: true,
    }));
  }, []);

  // Save settings
  const saveSettings = useCallback(async () => {
    setState((prev) => ({ ...prev, isSaving: true, error: null }));
    try {
      await settings.update(state.settings);
      setOriginalSettings(state.settings);
      setState((prev) => ({
        ...prev,
        isSaving: false,
        hasChanges: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save settings';
      setState((prev) => ({ ...prev, isSaving: false, error: message }));
      throw error;
    }
  }, [state.settings]);

  // Reset to defaults
  const resetToDefaults = useCallback(async () => {
    setState((prev) => ({ ...prev, isSaving: true, error: null }));
    try {
      await settings.reset();
      setState({
        settings: defaultSettings,
        isLoading: false,
        isSaving: false,
        error: null,
        hasChanges: false,
      });
      setOriginalSettings(defaultSettings);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to reset settings';
      setState((prev) => ({ ...prev, isSaving: false, error: message }));
      throw error;
    }
  }, []);

  // Discard changes
  const discardChanges = useCallback(() => {
    setState((prev) => ({
      ...prev,
      settings: originalSettings,
      hasChanges: false,
    }));
  }, [originalSettings]);

  // Apply theme
  useEffect(() => {
    const theme = state.settings.theme;
    if (theme === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.classList.toggle('dark', isDark);
    } else {
      document.documentElement.classList.toggle('dark', theme === 'dark');
    }
  }, [state.settings.theme]);

  return {
    settings: state.settings,
    isLoading: state.isLoading,
    isSaving: state.isSaving,
    error: state.error,
    hasChanges: state.hasChanges,
    fetchSettings,
    updateSetting,
    updateNotificationSetting,
    updateStealthSetting,
    saveSettings,
    resetToDefaults,
    discardChanges,
  };
}
