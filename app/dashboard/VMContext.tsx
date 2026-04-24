"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { vmService } from '@/services/vms';
import { useAuth } from '../../context/AuthContext';

export interface VM {
  id: string;
  proxmox_vmid: number;
  name: string;
  description?: string;
  vcpu: number;
  ram_gb: number;
  storage_gb: number;
  status: string;
  lease_start: string;
  lease_end: string;
  ip_address?: string;
  ssh_public_key?: string;
  // UI helpers (calculated or mocked)
  cpu_usage?: number;
  ram_usage?: number;
}

export interface Reservation {
  id: string;
  name: string;
  os: string;
  cpu: number;
  ram: string;
  storage: string;
  status: 'pending' | 'approved' | 'rejected';
  date: string;
}

interface VMContextType {
  vms: VM[];
  loading: boolean;
  reservations: Reservation[];
  clusterStatus: any;
  refreshVMs: () => Promise<void>;
  refreshClusterStatus: () => Promise<void>;
  addVM: (data: any) => Promise<any>;
  deleteVM: (vmid: string) => Promise<void>;
  startVM: (vmid: string) => Promise<void>;
  stopVM: (vmid: string) => Promise<void>;
  rebootVM: (vmid: string) => Promise<void>;
  pauseVM: (vmid: string) => Promise<void>;
  extendVM: (vmid: string, hours: number) => Promise<void>;
  updateVM: (vmid: string, data: any) => Promise<void>;
}

export const VMContext = createContext<VMContextType | null>(null);

export const useVMs = () => {
  const context = useContext(VMContext);
  if (!context) throw new Error('useVMs must be used within VMProvider');
  return context;
};

export const VMProvider = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  const [vms, setVMs] = useState<VM[]>([]);
  const [loading, setLoading] = useState(false);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [clusterStatus, setClusterStatus] = useState<any>(null);

  const refreshVMs = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await vmService.listVms();
      setVMs(data.items || []);
    } catch (error) {
      console.error("Failed to fetch VMs:", error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  const refreshClusterStatus = useCallback(async () => {
    if (!user) return;
    try {
      const data = await vmService.getClusterStatus();
      setClusterStatus(data);
    } catch (error) {
      console.error("Failed to fetch cluster status:", error);
    }
  }, [user]);

  useEffect(() => {
    refreshVMs();
    refreshClusterStatus();
    
    // Interval pour le statut du cluster (toutes les 30s)
    const interval = setInterval(refreshClusterStatus, 30000);
    return () => clearInterval(interval);
  }, [refreshVMs, refreshClusterStatus]);

  const addVM = async (data: any) => {
    const newVM = await vmService.createVm(data);
    await refreshVMs();
    return newVM;
  };

  const deleteVM = async (vmid: string) => {
    await vmService.deleteVm(vmid);
    await refreshVMs();
  };

  const startVM = async (vmid: string) => {
    await vmService.startVm(vmid);
    await refreshVMs();
  };

  const stopVM = async (vmid: string) => {
    await vmService.stopVm(vmid);
    await refreshVMs();
  };

  const rebootVM = async (vmid: string) => {
    await vmService.rebootVm(vmid);
    await refreshVMs();
  };

  const pauseVM = async (vmid: string) => {
    await vmService.pauseVm(vmid);
    await refreshVMs();
  };

  const extendVM = async (vmid: string, hours: number) => {
    await vmService.extendVm(vmid, hours);
    await refreshVMs();
  };

  const updateVM = async (vmid: string, data: any) => {
    const backendData: any = {};
    if (data.cpu !== undefined) backendData.vcpu = data.cpu;
    if (data.ram) backendData.ram_gb = parseFloat(data.ram);
    if (data.storage) backendData.storage_gb = parseFloat(data.storage);

    await vmService.updateVm(vmid, backendData);
    await refreshVMs();
  };

  return (
    <VMContext.Provider value={{
      vms,
      loading,
      reservations,
      clusterStatus,
      refreshVMs,
      refreshClusterStatus,
      addVM,
      deleteVM,
      startVM,
      stopVM,
      rebootVM,
      pauseVM,
      extendVM,
      updateVM
    }}>
      {children}
    </VMContext.Provider>
  );
};
