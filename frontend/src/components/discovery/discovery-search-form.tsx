"use client";

import { useEffect, useMemo, useState } from "react";
import { ExternalLink, Search } from "lucide-react";

import { ApiError } from "@/lib/api-client";
import { formatDiscoveryError } from "@/lib/format-api-error";
import {
  buildSourceSearchUrl,
  DISCOVERY_SOURCE_CATEGORIES,
  type DiscoverySourceCategory,
  getWebsitesForCategory,
} from "@/lib/discovery-sources";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDiscoveryTab } from "@/hooks/use-discovery-tab";
import { useCreateDiscoverySearch } from "@/hooks/use-discovery";

interface DiscoverySearchFormProps {
  onSearchStarted: (searchId: string) => void;
}

export function DiscoverySearchForm({ onSearchStarted }: DiscoverySearchFormProps) {
  const createSearch = useCreateDiscoverySearch();
  const { openSourceTab, watchSearchAndCloseTab } = useDiscoveryTab();

  const [sourceCategory, setSourceCategory] = useState<DiscoverySourceCategory>(
    "google_business",
  );
  const [sourceWebsite, setSourceWebsite] = useState("google_maps");
  const [industry, setIndustry] = useState("");
  const [country, setCountry] = useState("USA");
  const [state, setState] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const websiteOptions = useMemo(
    () => getWebsitesForCategory(sourceCategory),
    [sourceCategory],
  );

  const previewUrl = useMemo(() => {
    if (!industry.trim() || !country.trim()) return null;
    return buildSourceSearchUrl(sourceCategory, sourceWebsite, {
      industry_keyword: industry.trim(),
      country: country.trim(),
      state: state.trim() || undefined,
      city: city.trim() || undefined,
    });
  }, [sourceCategory, sourceWebsite, industry, country, state, city]);

  useEffect(() => {
    const websites = getWebsitesForCategory(sourceCategory);
    if (!websites.some((w) => w.id === sourceWebsite)) {
      setSourceWebsite(websites[0]?.id ?? "");
    }
  }, [sourceCategory, sourceWebsite]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setStatusMessage(null);

    const payload = {
      industry_keyword: industry.trim(),
      country: country.trim(),
      state: state.trim() || undefined,
      city: city.trim() || undefined,
      data_source_category: sourceCategory,
      data_source_website: sourceWebsite,
    };

    try {
      if (previewUrl) {
        const opened = openSourceTab(previewUrl);
        if (!opened) {
          setStatusMessage(
            "Popup blocked — allow popups for this site to open the source page automatically.",
          );
        } else {
          setStatusMessage("Source page opened in a new tab. Importing results…");
        }
      }

      const result = await createSearch.mutateAsync(payload);
      onSearchStarted(result.id);

      watchSearchAndCloseTab(result.id, (search) => {
        if (search?.status === "completed") {
          setStatusMessage(
            `Discovery complete — ${search.total_new} new leads, ${search.total_duplicates} duplicates, ${search.total_found} total found.`,
          );
        } else if (search?.status === "failed") {
          setError(
            search.error_message
              ? `Lead discovery failed: ${search.error_message}`
              : "Lead discovery failed. Please check logs for details.",
          );
          setStatusMessage(null);
        }
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(formatDiscoveryError(err.status, err.detail ?? { detail: err.message }));
      } else {
        setError(
          err instanceof Error
            ? err.message
            : "Lead discovery failed. Please check logs for details.",
        );
      }
    }
  }

  const selectedCategory = DISCOVERY_SOURCE_CATEGORIES.find((c) => c.id === sourceCategory);

  return (
    <form onSubmit={handleSubmit} className="glass-card rounded-lg border border-border p-6">
      <div className="mb-4 flex items-center gap-2">
        <Search className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Discover Leads</h2>
      </div>
      <p className="mb-4 text-sm text-muted-foreground">
        Select a data source, choose a directory website, enter search parameters, then start
        discovery. The source opens in a new tab while results are scraped and imported here.
      </p>

      {error && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}
      {statusMessage && (
        <p className="mb-4 rounded-md bg-primary/10 px-3 py-2 text-sm text-primary">
          {statusMessage}
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="source-category">Data Source *</Label>
          <Select
            value={sourceCategory}
            onValueChange={(v) => setSourceCategory(v as DiscoverySourceCategory)}
          >
            <SelectTrigger id="source-category">
              <SelectValue placeholder="Select data source" />
            </SelectTrigger>
            <SelectContent>
              {DISCOVERY_SOURCE_CATEGORIES.map((category) => (
                <SelectItem key={category.id} value={category.id}>
                  {category.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedCategory && (
            <p className="text-xs text-muted-foreground">{selectedCategory.description}</p>
          )}
        </div>

        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="source-website">Website *</Label>
          <Select value={sourceWebsite} onValueChange={setSourceWebsite}>
            <SelectTrigger id="source-website">
              <SelectValue placeholder="Select website" />
            </SelectTrigger>
            <SelectContent>
              {websiteOptions.map((website) => (
                <SelectItem key={website.id} value={website.id}>
                  {website.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {websiteOptions.find((w) => w.id === sourceWebsite)?.description}
          </p>
        </div>

        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="industry">Industry Keyword *</Label>
          <Input
            id="industry"
            placeholder="e.g. Dentist, Restaurant, Plumber"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            required
            minLength={2}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="country">Country *</Label>
          <Input
            id="country"
            placeholder="USA"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="state">State / Province</Label>
          <Input
            id="state"
            placeholder="California"
            value={state}
            onChange={(e) => setState(e.target.value)}
          />
        </div>
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="city">City</Label>
          <Input
            id="city"
            placeholder="Los Angeles"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />
        </div>
      </div>

      {previewUrl && (
        <div className="mt-4 flex items-center gap-2 rounded-md border border-border/60 bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
          <ExternalLink className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate">Preview: {previewUrl}</span>
        </div>
      )}

      <Button className="mt-6" type="submit" disabled={createSearch.isPending}>
        {createSearch.isPending ? "Starting discovery..." : "Start Discovery"}
      </Button>
    </form>
  );
}
