/**
 * Hook for managing device data
 */

import { useCallback, useMemo } from 'react';
import { useDevicesStore } from '@/stores';
import { devices } from '@/lib/api';
import type { Device } from '@/types';

export function useDevices() {
  const {
    devices: deviceList,
    selectedDeviceId,
    isLoading,
    setDevices,
    addDevice,
    updateDevice,
    selectDevice,
  } = useDevicesStore();

  // Fetch all devices
  const fetchDevices = useCallback(async () => {
    try {
      const data = await devices.getAll();
      setDevices(data);
      return data;
    } catch (error) {
      console.error('Failed to fetch devices:', error);
      throw error;
    }
  }, [setDevices]);

  // Scan for new devices
  const scanDevices = useCallback(async () => {
    try {
      const data = await devices.scan();
      setDevices(data);
      return data;
    } catch (error) {
      console.error('Failed to scan devices:', error);
      throw error;
    }
  }, [setDevices]);

  // Toggle device monitoring
  const toggleMonitoring = useCallback(async (deviceId: string, enabled: boolean) => {
    try {
      await devices.setMonitoring(deviceId, enabled);
      updateDevice(deviceId, { isMonitored: enabled });
    } catch (error) {
      console.error('Failed to toggle device monitoring:', error);
      throw error;
    }
  }, [updateDevice]);

  // Get online devices
  const onlineDevices = useMemo(() => {
    return deviceList.filter((d) => d.isOnline);
  }, [deviceList]);

  // Get monitored devices
  const monitoredDevices = useMemo(() => {
    return deviceList.filter((d) => d.isMonitored);
  }, [deviceList]);

  // Get selected device
  const selectedDevice = useMemo(() => {
    if (!selectedDeviceId) return null;
    return deviceList.find((d) => d.id === selectedDeviceId) || null;
  }, [deviceList, selectedDeviceId]);

  // Get device by ID
  const getDevice = useCallback((id: string): Device | undefined => {
    return deviceList.find((d) => d.id === id);
  }, [deviceList]);

  // Get device by IP
  const getDeviceByIp = useCallback((ip: string): Device | undefined => {
    return deviceList.find((d) => d.ip === ip);
  }, [deviceList]);

  // Get device by MAC
  const getDeviceByMac = useCallback((mac: string): Device | undefined => {
    const normalizedMac = mac.toUpperCase().replace(/[:-]/g, ':');
    return deviceList.find((d) => d.mac.toUpperCase().replace(/[:-]/g, ':') === normalizedMac);
  }, [deviceList]);

  // Device stats
  const stats = useMemo(() => ({
    total: deviceList.length,
    online: onlineDevices.length,
    offline: deviceList.length - onlineDevices.length,
    monitored: monitoredDevices.length,
  }), [deviceList, onlineDevices, monitoredDevices]);

  return {
    devices: deviceList,
    onlineDevices,
    monitoredDevices,
    selectedDevice,
    isLoading,
    stats,
    fetchDevices,
    scanDevices,
    toggleMonitoring,
    selectDevice,
    getDevice,
    getDeviceByIp,
    getDeviceByMac,
    addDevice,
    updateDevice,
  };
}
