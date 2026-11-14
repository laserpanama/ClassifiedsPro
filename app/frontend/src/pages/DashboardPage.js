import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import accountService from '../services/accountService';
import adService from '../services/adService';
import scheduleService from '../services/scheduleService';

const StatCard = ({ label, value, to }) => (
  <Link to={to} className="block p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow">
    <p className="text-sm text-muted-foreground">{label}</p>
    <p className="text-3xl font-bold mt-1">{value}</p>
  </Link>
);

const DashboardPage = () => {
  const [stats, setStats] = useState({ accounts: '…', activeAccounts: '…', ads: '…', activeSchedules: '…' });
  const [nextRun, setNextRun] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [accountsRes, adsRes, schedulesRes] = await Promise.all([
          accountService.getAccounts(),
          adService.getAds(),
          scheduleService.getSchedules(),
        ]);
        const accounts = accountsRes.data;
        const schedules = schedulesRes.data;
        const upcoming = schedules
          .filter((s) => s.is_active && s.next_republish_at)
          .map((s) => new Date(s.next_republish_at))
          .sort((a, b) => a - b)[0] || null;

        setStats({
          accounts: accounts.length,
          activeAccounts: accounts.filter((a) => a.is_active).length,
          ads: adsRes.data.length,
          activeSchedules: schedules.filter((s) => s.is_active).length,
        });
        setNextRun(upcoming);
      } catch (err) {
        console.error('Error loading dashboard:', err);
        setError('Could not load dashboard data. Is the backend running?');
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Dashboard</h2>
      {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Accounts" value={stats.accounts} to="/accounts" />
        <StatCard label="Active accounts" value={stats.activeAccounts} to="/accounts" />
        <StatCard label="Ads" value={stats.ads} to="/ads" />
        <StatCard label="Active schedules" value={stats.activeSchedules} to="/schedules" />
      </div>

      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold mb-2">Next scheduled republish</h3>
        <p className="text-muted-foreground">
          {nextRun ? nextRun.toLocaleString() : 'No active schedules yet.'}
        </p>
      </div>
    </div>
  );
};

export default DashboardPage;
