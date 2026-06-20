"use client";

import { useAuth } from "@/hooks/use-auth";
import { useLogout } from "@/hooks/use-auth-mutations";
import { PageHeader } from "@/components/dashboard/page-header";
import { ThemeSelector } from "@/components/theme/theme-selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/animations/fade-in";

export default function SettingsPage() {
  const { user } = useAuth();
  const logout = useLogout();

  return (
    <>
      <FadeIn>
        <PageHeader
          title="Settings"
          description="Account, appearance, and application preferences"
          actions={
            <Button
              variant="outline"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
            >
              {logout.isPending ? "Signing out..." : "Sign Out"}
            </Button>
          }
        />
      </FadeIn>

      <div className="grid max-w-4xl gap-6">
        <ThemeSelector />

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {user ? (
              <dl className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-border/60 bg-muted/20 p-4">
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Name
                  </dt>
                  <dd className="mt-1 font-medium">{user.full_name}</dd>
                </div>
                <div className="rounded-lg border border-border/60 bg-muted/20 p-4">
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Email
                  </dt>
                  <dd className="mt-1 font-medium">{user.email}</dd>
                </div>
                <div className="rounded-lg border border-border/60 bg-muted/20 p-4">
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Role
                  </dt>
                  <dd className="mt-1 font-medium capitalize">
                    {user.role.replace("_", " ")}
                  </dd>
                </div>
                <div className="rounded-lg border border-border/60 bg-muted/20 p-4">
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Timezone
                  </dt>
                  <dd className="mt-1 font-medium">{user.timezone}</dd>
                </div>
              </dl>
            ) : (
              <p className="text-sm text-muted-foreground">Loading profile...</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Configure audit completion and export notifications.
            </p>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
