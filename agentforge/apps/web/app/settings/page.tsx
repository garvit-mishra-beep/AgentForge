"use client";

import { Key, User, Bell } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground text-sm">Manage your account and API keys</p>
      </div>

      <div className="rounded-xl border bg-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <User className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">Profile</h2>
        </div>
        <p className="text-sm text-muted-foreground">Account management coming soon.</p>
      </div>

      <div className="rounded-xl border bg-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <Key className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">API Keys</h2>
        </div>
        <p className="text-sm text-muted-foreground">API key management coming soon.</p>
      </div>

      <div className="rounded-xl border bg-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">Notifications</h2>
        </div>
        <p className="text-sm text-muted-foreground">Notification preferences coming soon.</p>
      </div>
    </div>
  );
}
