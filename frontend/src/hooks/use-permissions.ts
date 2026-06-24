"use client";

import { useMemo } from "react";

import { useAuth } from "@/hooks/use-auth";
import type { UserRole } from "@/types";

export type Permission =
  | "users:list"
  | "users:read"
  | "users:create"
  | "users:update"
  | "users:delete"
  | "websites:list"
  | "websites:create"
  | "websites:update"
  | "websites:delete"
  | "audits:run"
  | "audits:view"
  | "audits:cancel"
  | "reports:generate"
  | "reports:download"
  | "exports:create"
  | "analytics:view"
  | "discovery:search"
  | "discovery:view"
  | "discovery:import"
  | "enrichment:run"
  | "enrichment:view"
  | "scoring:run"
  | "scoring:view"
  | "system:admin";

const ALL_PERMISSIONS = new Set<Permission>([
  "users:list",
  "users:read",
  "users:create",
  "users:update",
  "users:delete",
  "websites:list",
  "websites:create",
  "websites:update",
  "websites:delete",
  "audits:run",
  "audits:view",
  "audits:cancel",
  "reports:generate",
  "reports:download",
  "exports:create",
  "analytics:view",
  "discovery:search",
  "discovery:view",
  "discovery:import",
  "enrichment:run",
  "enrichment:view",
  "scoring:run",
  "scoring:view",
  "system:admin",
]);

const ROLE_PERMISSIONS: Record<UserRole, ReadonlySet<Permission>> = {
  super_admin: ALL_PERMISSIONS,
  admin: new Set([
    "users:list",
    "users:read",
    "users:create",
    "users:update",
    "users:delete",
    "websites:list",
    "websites:create",
    "websites:update",
    "websites:delete",
    "audits:run",
    "audits:view",
    "audits:cancel",
    "reports:generate",
    "reports:download",
    "exports:create",
    "analytics:view",
    "discovery:search",
    "discovery:view",
    "discovery:import",
    "enrichment:run",
    "enrichment:view",
    "scoring:run",
    "scoring:view",
  ]),
  manager: new Set([
    "users:read",
    "websites:list",
    "websites:create",
    "websites:update",
    "websites:delete",
    "audits:run",
    "audits:view",
    "audits:cancel",
    "reports:generate",
    "reports:download",
    "exports:create",
    "analytics:view",
    "discovery:search",
    "discovery:view",
    "discovery:import",
    "enrichment:run",
    "enrichment:view",
    "scoring:run",
    "scoring:view",
  ]),
  analyst: new Set([
    "websites:list",
    "websites:create",
    "audits:run",
    "audits:view",
    "reports:generate",
    "reports:download",
    "exports:create",
    "analytics:view",
    "discovery:search",
    "discovery:view",
    "discovery:import",
    "enrichment:run",
    "enrichment:view",
    "scoring:run",
    "scoring:view",
  ]),
  viewer: new Set([
    "websites:list",
    "audits:view",
    "reports:download",
    "analytics:view",
    "discovery:view",
    "enrichment:view",
    "scoring:view",
  ]),
};

export function usePermissions() {
  const { user } = useAuth();

  return useMemo(() => {
    const role = user?.role;
    const permissions = role ? ROLE_PERMISSIONS[role] : new Set<Permission>();

    return {
      role,
      hasPermission: (permission: Permission) => permissions.has(permission),
      canCreateWebsite: permissions.has("websites:create"),
      canUpdateWebsite: permissions.has("websites:update"),
      canDeleteWebsite: permissions.has("websites:delete"),
      canRunAudit: permissions.has("audits:run"),
      canImportDiscovery: permissions.has("discovery:import"),
      canRunEnrichment: permissions.has("enrichment:run"),
      canRunScoring: permissions.has("scoring:run"),
    };
  }, [user?.role]);
}
