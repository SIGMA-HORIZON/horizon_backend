"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { vmService } from '../../services/vms';
import { useAuth } from '../../context/AuthContext';

export interface VM {
  id: string; // The UUID or ID from DB
  proxmox_vmid?: number;
  name: string;
  os: string;
  cpu: number;
  cpu_usage?: number;
  ram: string; // e.g. "16GB"
  ram_usage?: number;
  storage: string;
  ip_address?: string;
  status: 'on' | 'off' | 'warn';
  created_at: string;
  expires_at: string;
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
  refreshVMs: () => Promise<void>;
  addVM: (data: any) => Promise<any>;
  deleteVM: (vmid: string) => Promise<void>;
  stopVM: (vmid: string) => Promise<void>;
  extendVM: (vmid: string, hours: number) => Promise<void>;
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

  const refreshVMs = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await vmService.listVms();
      // Map API data to our expected UI format if needed
      setVMs(data.items || []);
    } catch (error) {
      console.error("Failed to fetch VMs:", error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refreshVMs();
  }, [refreshVMs]);

  const addVM = async (data: any) => {
    const newVM = await vmService.createVm(data);
    await refreshVMs();
    return newVM;
  };

  const deleteVM = async (vmid: string) => {
    await vmService.deleteVm(vmid);
    await refreshVMs();
  };

  const stopVM = async (vmid: string) => {
    await vmService.stopVm(vmid);
    await refreshVMs();
  };

  const extendVM = async (vmid: string, hours: number) => {
    await vmService.extendVm(vmid, hours);
    await refreshVMs();
  };

  return (
    <VMContext.Provider value={{
      vms,
      loading,
      reservations,
      refreshVMs,
      addVM,
      deleteVM,
      stopVM,
      extendVM
    }}>
      {children}
    </VMContext.Provider>
  );
};
