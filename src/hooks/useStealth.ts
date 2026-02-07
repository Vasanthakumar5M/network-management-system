/**
 * Hook for managing stealth mode settings
 */

import { useState, useCallback } from 'react';
import { stealth, type DeviceProfile } from '@/lib/api';
import { useMonitoringStore } from '@/stores';

interface StealthStatus {
  isActive: boolean;
  currentProfile: string;
  originalMac: string;
  currentMac: string;
  originalHostname: string;
  currentHostname: string;
}

interface UseStealthState {
  profiles: DeviceProfile[];
  status: StealthStatus | null;
  isLoading: boolean;
  isApplying: boolean;
  error: string | null;
}

export function useStealth() {
  const [state, setState] = useState<UseStealthState>({
    profiles: [],
    status: null,
    isLoading: false,
    isApplying: false,
    error: null,
  });

  const { setStatus } = useMonitoringStore();

  // Fetch profiles and status
  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const [profiles, status] = await Promise.all([
        stealth.getProfiles(),
        stealth.getStatus(),
      ]);
      setState({
        profiles,
        status,
        isLoading: false,
        isApplying: false,
        error: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch stealth data';
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
    }
  }, []);

  // Change profile
  const changeProfile = useCallback(async (profileId: string) => {
    setState((prev) => ({ ...prev, isApplying: true, error: null }));
    try {
      await stealth.changeProfile(profileId);
      const status = await stealth.getStatus();
      setState((prev) => ({
        ...prev,
        status,
        isApplying: false,
      }));
      setStatus({ currentProfile: profileId });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to change profile';
      setState((prev) => ({ ...prev, isApplying: false, error: message }));
      throw error;
    }
  }, [setStatus]);

  // Apply stealth settings
  const applySettings = useCallback(async () => {
    setState((prev) => ({ ...prev, isApplying: true, error: null }));
    try {
      await stealth.apply();
      const status = await stealth.getStatus();
      setState((prev) => ({
        ...prev,
        status,
        isApplying: false,
      }));
      setStatus({ stealthMode: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to apply stealth settings';
      setState((prev) => ({ ...prev, isApplying: false, error: message }));
      throw error;
    }
  }, [setStatus]);

  // Restore original settings
  const restoreSettings = useCallback(async () => {
    setState((prev) => ({ ...prev, isApplying: true, error: null }));
    try {
      await stealth.restore();
      const status = await stealth.getStatus();
      setState((prev) => ({
        ...prev,
        status,
        isApplying: false,
      }));
      setStatus({ stealthMode: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to restore settings';
      setState((prev) => ({ ...prev, isApplying: false, error: message }));
      throw error;
    }
  }, [setStatus]);

  // Get current profile details
  const getCurrentProfile = useCallback((): DeviceProfile | undefined => {
    if (!state.status) return undefined;
    return state.profiles.find((p) => p.id === state.status!.currentProfile);
  }, [state.profiles, state.status]);

  // Get profile by ID
  const getProfile = useCallback((profileId: string): DeviceProfile | undefined => {
    return state.profiles.find((p) => p.id === profileId);
  }, [state.profiles]);

  // Group profiles by type
  const profilesByType = state.profiles.reduce<Record<string, DeviceProfile[]>>(
    (acc, profile) => {
      if (!acc[profile.type]) {
        acc[profile.type] = [];
      }
      acc[profile.type].push(profile);
      return acc;
    },
    {}
  );

  return {
    profiles: state.profiles,
    profilesByType,
    status: state.status,
    isActive: state.status?.isActive ?? false,
    currentProfile: getCurrentProfile(),
    isLoading: state.isLoading,
    isApplying: state.isApplying,
    error: state.error,
    fetchData,
    changeProfile,
    applySettings,
    restoreSettings,
    getProfile,
  };
}
