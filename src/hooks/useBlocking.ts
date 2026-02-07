/**
 * Hook for managing blocking rules, categories, and schedules
 */

import { useState, useCallback } from 'react';
import { blocking } from '@/lib/api';
import type { BlockRule, BlockCategory, Schedule } from '@/types';

interface UseBlockingState {
  rules: BlockRule[];
  categories: BlockCategory[];
  schedules: Schedule[];
  isLoading: boolean;
  error: string | null;
}

export function useBlocking() {
  const [state, setState] = useState<UseBlockingState>({
    rules: [],
    categories: [],
    schedules: [],
    isLoading: false,
    error: null,
  });

  // Fetch all blocking data
  const fetchAll = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const [rules, categories, schedules] = await Promise.all([
        blocking.getRules(),
        blocking.getCategories(),
        blocking.getSchedules(),
      ]);
      setState({
        rules,
        categories,
        schedules,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch blocking data';
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
      throw error;
    }
  }, []);

  // Add a new block rule
  const addRule = useCallback(async (
    ruleType: BlockRule['type'],
    value: string,
    deviceIds?: string[]
  ) => {
    try {
      const newRule = await blocking.addRule(ruleType, value, deviceIds);
      setState((prev) => ({
        ...prev,
        rules: [...prev.rules, newRule],
      }));
      return newRule;
    } catch (error) {
      console.error('Failed to add block rule:', error);
      throw error;
    }
  }, []);

  // Remove a block rule
  const removeRule = useCallback(async (ruleId: string) => {
    try {
      await blocking.removeRule(ruleId);
      setState((prev) => ({
        ...prev,
        rules: prev.rules.filter((r) => r.id !== ruleId),
      }));
    } catch (error) {
      console.error('Failed to remove block rule:', error);
      throw error;
    }
  }, []);

  // Toggle a block rule
  const toggleRule = useCallback(async (ruleId: string, enabled: boolean) => {
    try {
      await blocking.toggleRule(ruleId, enabled);
      setState((prev) => ({
        ...prev,
        rules: prev.rules.map((r) =>
          r.id === ruleId ? { ...r, isEnabled: enabled } : r
        ),
      }));
    } catch (error) {
      console.error('Failed to toggle block rule:', error);
      throw error;
    }
  }, []);

  // Toggle a category
  const toggleCategory = useCallback(async (categoryId: string, enabled: boolean) => {
    try {
      await blocking.toggleCategory(categoryId, enabled);
      setState((prev) => ({
        ...prev,
        categories: prev.categories.map((c) =>
          c.id === categoryId ? { ...c, isEnabled: enabled } : c
        ),
      }));
    } catch (error) {
      console.error('Failed to toggle category:', error);
      throw error;
    }
  }, []);

  // Save schedule (create or update)
  const saveSchedule = useCallback(async (schedule: Omit<Schedule, 'id'> | Schedule) => {
    try {
      const savedSchedule = await blocking.saveSchedule(schedule);
      setState((prev) => {
        const existingIndex = prev.schedules.findIndex((s) => s.id === (schedule as Schedule).id);
        if (existingIndex >= 0) {
          // Update existing
          const updated = [...prev.schedules];
          updated[existingIndex] = savedSchedule;
          return { ...prev, schedules: updated };
        } else {
          // Add new
          return { ...prev, schedules: [...prev.schedules, savedSchedule] };
        }
      });
      return savedSchedule;
    } catch (error) {
      console.error('Failed to save schedule:', error);
      throw error;
    }
  }, []);

  // Delete schedule
  const deleteSchedule = useCallback(async (scheduleId: string) => {
    try {
      await blocking.deleteSchedule(scheduleId);
      setState((prev) => ({
        ...prev,
        schedules: prev.schedules.filter((s) => s.id !== scheduleId),
      }));
    } catch (error) {
      console.error('Failed to delete schedule:', error);
      throw error;
    }
  }, []);

  // Toggle schedule
  const toggleSchedule = useCallback(async (scheduleId: string, enabled: boolean) => {
    const schedule = state.schedules.find((s) => s.id === scheduleId);
    if (schedule) {
      await saveSchedule({ ...schedule, isEnabled: enabled });
    }
  }, [state.schedules, saveSchedule]);

  // Get active rules (enabled and not scheduled, or scheduled and in time window)
  const getActiveRules = useCallback(() => {
    return state.rules.filter((rule) => {
      if (!rule.isEnabled) return false;
      if (!rule.scheduleId) return true;

      const schedule = state.schedules.find((s) => s.id === rule.scheduleId);
      if (!schedule || !schedule.isEnabled) return true;

      // Check if current time is within schedule
      const now = new Date();
      const currentDay = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][now.getDay()];
      if (!schedule.days.includes(currentDay)) return true;

      const currentTime = now.toTimeString().slice(0, 5); // HH:MM format
      return currentTime >= schedule.startTime && currentTime <= schedule.endTime;
    });
  }, [state.rules, state.schedules]);

  // Get enabled categories
  const enabledCategories = state.categories.filter((c) => c.isEnabled);

  // Get enabled schedules
  const enabledSchedules = state.schedules.filter((s) => s.isEnabled);

  return {
    rules: state.rules,
    categories: state.categories,
    schedules: state.schedules,
    enabledCategories,
    enabledSchedules,
    isLoading: state.isLoading,
    error: state.error,
    fetchAll,
    addRule,
    removeRule,
    toggleRule,
    toggleCategory,
    saveSchedule,
    deleteSchedule,
    toggleSchedule,
    getActiveRules,
  };
}
