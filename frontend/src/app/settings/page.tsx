"use client";

import { useAuth } from "@/hooks/use-auth";
import { useLogout } from "@/hooks/use-auth-mutations";
import { PageHeader } from "@/components/dashboard/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const { user } = useAuth();
  const logout = useLogout();

  return (
    <>
      <PageHeader
        title="Settings"
        description="Account, team, and application preferences"
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
      <div className="grid max-w-2xl gap-6">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {user ? (
              <>
                <div>
                  <p className="text-sm text-muted-foreground">Name</p>
                  <p className="font-medium">{user.full_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-medium">{user.email}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Role</p>
                  <p className="font-medium capitalize">
                    {user.role.replace("_", " ")}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Timezone</p>
                  <p className="font-medium">{user.timezone}</p>
                </div>
              </>
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
