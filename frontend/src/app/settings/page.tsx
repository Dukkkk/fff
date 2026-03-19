"use client";

import { useEffect, useState } from "react";

import { Button, Card, CardTitle, Input, Muted, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { clearLocalUser, getLocalUserId, getLocalUserName } from "@/lib/session";

export default function SettingsPage() {
  const userId = getLocalUserId();
  const [name, setName] = useState(getLocalUserName() ?? "");
  const [currency, setCurrency] = useState("USD");
  const [theme, setTheme] = useState("light");
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    async function check() {
      if (!userId) return;
      try {
        await api.getUser(userId);
        setApiOk(true);
      } catch {
        setApiOk(false);
      }
    }
    check();
  }, [userId]);

  if (!userId) {
    return (
      <Card>
        <CardTitle>You're not onboarded</CardTitle>
        <Muted>Go to onboarding first.</Muted>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <CardTitle>Profile</CardTitle>
        <div className="space-y-1">
          <Muted>Name (stored locally for MVP)</Muted>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Muted>Currency</Muted>
            <Select value={currency} onChange={(e) => setCurrency(e.target.value)}>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
            </Select>
          </div>
          <div className="space-y-1">
            <Muted>Theme</Muted>
            <Select value={theme} onChange={(e) => setTheme(e.target.value)}>
              <option value="light">Light</option>
              <option value="dark">Dark (MVP placeholder)</option>
            </Select>
          </div>
        </div>
        <Muted>API connectivity: {apiOk === null ? "Checking…" : apiOk ? "OK" : "Not reachable"}</Muted>
      </Card>

      <Card className="space-y-2">
        <CardTitle>Notifications</CardTitle>
        <Muted>MVP note: nudges are generated on demand; push notifications can be added later.</Muted>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Danger zone</CardTitle>
        <Muted>Clears your local user id and returns to onboarding.</Muted>
        <Button
          variant="ghost"
          className="border border-ink-200/60"
          onClick={() => {
            clearLocalUser();
            window.location.href = "/onboarding";
          }}
        >
          Reset onboarding
        </Button>
      </Card>
    </div>
  );
}

