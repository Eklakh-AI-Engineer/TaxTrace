'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Settings, SettingsUpdate } from '@/lib/types';
import { User, Bell, Mail, Moon, Sun, Monitor, Shield, Key, Save, Loader2 } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'security' | 'appearance'>('profile');
  const [formData, setFormData] = useState<Partial<SettingsUpdate>>({});

  const queryClient = useQueryClient();

  const { data: settings, isLoading, error, refetch } = useQuery({
    queryKey: ['settings'],
    queryFn: () => api.settings.get(),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: SettingsUpdate) => api.settings.update(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      alert('Settings saved successfully');
    },
    onError: () => alert('Failed to save settings'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData as SettingsUpdate);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type, checked } = e.target as HTMLInputElement;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin" />
        <span className="ml-3 text-slate-500">Loading settings...</span>
      </div>
    );
  }

  if (error || !settings) {
    return <div className="p-8 text-red-500">Failed to load settings.</div>;
  }

  return (
    <div className="p-8 space-y-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-indigo-600" />
            Settings
          </h1>
          <p className="mt-2 text-sm text-slate-700">
            Manage your account settings, preferences, and security.
          </p>
        </div>
      </div>

      <div className="border-b border-slate-200 mb-8">
        <nav className="flex gap-8" aria-label="Settings tabs">
          {(['profile', 'notifications', 'security', 'appearance'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
          {activeTab === 'profile' && (
            <>
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <User className="w-5 h-5 text-indigo-600" />
                Profile
              </h2>
              <p className="text-sm text-slate-500">Update your personal information.</p>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name || settings.name}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={settings.email}
                    disabled
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">User ID</label>
                  <input
                    type="text"
                    value={settings.user_id}
                    disabled
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-slate-50 font-mono text-xs"
                  />
                </div>
              </div>
            </>
          )}

          {activeTab === 'notifications' && (
            <>
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Bell className="w-5 h-5 text-indigo-600" />
                Notifications
              </h2>
              <p className="text-sm text-slate-500">Configure how you receive notifications.</p>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-t border-slate-100">
                  <div>
                    <label className="block text-sm font-medium text-slate-900">In-App Notifications</label>
                    <p className="text-sm text-slate-500">Receive notifications within the application.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="notifications_enabled"
                      checked={formData.notifications_enabled ?? settings.notifications_enabled}
                      onChange={(e) => setFormData({ ...formData, notifications_enabled: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between py-3 border-t border-slate-100">
                  <div>
                    <label className="block text-sm font-medium text-slate-900">Email Notifications</label>
                    <p className="text-sm text-slate-500">Receive email notifications for important updates.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="email_notifications"
                      checked={formData.email_notifications ?? settings.email_notifications}
                      onChange={(e) => setFormData({ ...formData, email_notifications: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
                  </label>
                </div>
              </div>
            </>
          )}

          {activeTab === 'security' && (
            <>
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Key className="w-5 h-5 text-indigo-600" />
                Security
              </h2>
              <p className="text-sm text-slate-500">Manage your account security settings.</p>
              <div className="space-y-4">
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-amber-800 flex items-center gap-1">
                        <Shield className="w-4 h-4" /> Two-Factor Authentication
                      </h3>
                      <p className="text-sm text-amber-700 mt-1">Add an extra layer of security to your account.</p>
                    </div>
                    <button className="px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700">
                      Enable 2FA
                    </button>
                  </div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-slate-900">Change Password</h3>
                      <p className="text-sm text-slate-500">Update your account password.</p>
                    </div>
                    <button className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50">
                      Change Password
                    </button>
                  </div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-slate-900">Active Sessions</h3>
                      <p className="text-sm text-slate-500">Manage your active login sessions.</p>
                    </div>
                    <button className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50">
                      View Sessions
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'appearance' && (
            <>
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Monitor className="w-5 h-5 text-indigo-600" />
                Appearance
              </h2>
              <p className="text-sm text-slate-500">Customize how TaxTrace looks on your device.</p>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-900 mb-2">Theme</label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['light', 'dark', 'system'] as const).map((theme) => (
                      <label
                        key={theme}
                        className={`relative cursor-pointer p-4 rounded-lg border-2 transition-all ${
                          formData.theme === theme || settings.theme === theme
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="theme"
                          value={theme}
                          checked={formData.theme === theme || settings.theme === theme}
                          onChange={(e) => setFormData({ ...formData, theme: e.target.value as any })}
                          className="sr-only peer"
                        />
                        <div className={`text-center ${formData.theme === theme || settings.theme === theme ? 'peer-checked:text-indigo-600' : 'text-slate-600'}`}>
                          <div className={`w-10 h-10 mx-auto mb-2 rounded-lg ${
                            theme === 'light' ? 'bg-white border border-slate-200' :
                            theme === 'dark' ? 'bg-slate-900' :
                            'bg-gradient-to-br from-white to-slate-900 border border-slate-300'
                          }`} />
                          <span className="block text-sm font-medium capitalize">{theme}</span>
                          <span className="block text-xs text-slate-500 mt-1">
                            {theme === 'light' ? 'Always light' : theme === 'dark' ? 'Always dark' : 'Match system'}
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </form>

        <div className="mt-8 pt-6 border-t border-slate-200 flex justify-end">
          <button
            type="submit"
            form="settings-form"
            disabled={updateMutation.isPending}
            className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving…
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}