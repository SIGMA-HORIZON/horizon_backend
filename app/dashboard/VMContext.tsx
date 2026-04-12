"use client";

import React, { createContext, useContext, useState } from 'react';

export interface VM {
  id: string; // The VMID 
  name: string; // Internal name, e.g. vm-ml-ornella-01
  os: string; // e.g. Ubuntu 22.04
  cpu: number; // e.g. 8 (total vCPU)
  cpuVal: number; // e.g. 64 (percentage)
  ram: string; // e.g. 16 Go
  ramVal: number; // e.g. 58 (percentage)
  storage: string; // e.g. 50 Go
  ip: string; // e.g. 10.0.1.1
  status: 'on' | 'warn' | 'off';
  statusText: string;
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
  reservations: Reservation[];
  addVM: (vm: Omit<VM, 'id' | 'cpuVal' | 'ramVal' | 'ip' | 'status' | 'statusText'>) => void;
  deleteVM: (vmid: string) => void;
  updateVM: (vmid: string, updates: Partial<VM>) => void;
  addReservation: (res: Omit<Reservation, 'id' | 'status' | 'date'>) => void;
}

export const VMContext = createContext<VMContextType | null>(null);

export const useVMs = () => {
  const context = useContext(VMContext);
  if (!context) throw new Error('useVMs must be used within VMProvider');
  return context;
};

export const VMProvider = ({ children }: { children: React.ReactNode }) => {
  const [vms, setVMs] = useState<VM[]>([
    { id: '101', name: 'vm-ml-ornella-01', os: 'Ubuntu 22.04', cpu: 8, cpuVal: 64, ram: '16 Go', ramVal: 58, storage: '50 Go', ip: '10.0.1.1', status: 'on', statusText: 'Running' },
    { id: '102', name: 'vm-dev-ornella-02', os: 'Debian 12', cpu: 4, cpuVal: 22, ram: '8 Go', ramVal: 34, storage: '20 Go', ip: '10.0.1.2', status: 'on', statusText: 'Running' },
    { id: '103', name: 'vm-gpu-ornella-03', os: 'Ubuntu 22.04', cpu: 16, cpuVal: 91, ram: '64 Go', ramVal: 80, storage: '100 Go', ip: '10.0.1.3', status: 'warn', statusText: 'High CPU' }
  ]);

  const [reservations, setReservations] = useState<Reservation[]>([]);

  const addVM = (vm: Omit<VM, 'id' | 'cpuVal' | 'ramVal' | 'ip' | 'status' | 'statusText'>) => {
    const newId = String(100 + vms.length + 1);
    
    const newVM: VM = {
      ...vm,
      id: newId,
      cpuVal: 5,
      ramVal: 12,
      ip: `10.0.2.${newId}`,
      status: 'on',
      statusText: 'Booting'
    };
    
    setVMs([...vms, newVM]);
  };

  const addReservation = (res: Omit<Reservation, 'id' | 'status' | 'date'>) => {
    const newId = `REQ-${Date.now().toString().slice(-4)}`;
    const newRes: Reservation = {
      ...res,
      id: newId,
      status: 'pending',
      date: new Date().toLocaleDateString('fr-FR')
    };
    setReservations([...reservations, newRes]);
  };

  const deleteVM = (vmid: string) => {
    setVMs(vms.filter(v => v.id !== vmid));
  };

  const updateVM = (vmid: string, updates: Partial<VM>) => {
    setVMs(vms.map(v => v.id === vmid ? { ...v, ...updates } : v));
  };

  return <VMContext.Provider value={{ vms, reservations, addVM, deleteVM, updateVM, addReservation }}>{children}</VMContext.Provider>;
};
