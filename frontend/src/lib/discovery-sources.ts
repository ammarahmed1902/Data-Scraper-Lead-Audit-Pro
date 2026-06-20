/**
 * Lead discovery data source configuration and search URL builders.
 */

export type DiscoverySourceCategory =
  | "google_business"
  | "yelp"
  | "business_directory";

export interface DiscoveryWebsiteOption {
  id: string;
  label: string;
  description: string;
}

export interface DiscoverySourceCategoryOption {
  id: DiscoverySourceCategory;
  label: string;
  description: string;
  websites: DiscoveryWebsiteOption[];
}

export const DISCOVERY_SOURCE_CATEGORIES: DiscoverySourceCategoryOption[] = [
  {
    id: "google_business",
    label: "Google Business Profile",
    description: "Search Google Maps for local businesses.",
    websites: [
      {
        id: "google_maps",
        label: "Google Maps",
        description: "Primary Google Business Profile search.",
      },
      {
        id: "google_search",
        label: "Google Search",
        description: "Web search focused on business listings.",
      },
    ],
  },
  {
    id: "yelp",
    label: "Yelp",
    description: "Discover businesses from Yelp listings.",
    websites: [
      {
        id: "yelp",
        label: "Yelp.com",
        description: "Yelp business search results.",
      },
      {
        id: "yelp_mobile",
        label: "Yelp Mobile Web",
        description: "Mobile-optimized Yelp search.",
      },
    ],
  },
  {
    id: "business_directory",
    label: "Business Directory",
    description: "Search established online business directories.",
    websites: [
      {
        id: "yellow_pages",
        label: "Yellow Pages",
        description: "YellowPages.com business listings.",
      },
      {
        id: "manta",
        label: "Manta",
        description: "Manta small-business directory.",
      },
      {
        id: "superpages",
        label: "SuperPages",
        description: "SuperPages local listings.",
      },
      {
        id: "bbb",
        label: "Better Business Bureau",
        description: "BBB accredited business search.",
      },
    ],
  },
];

export interface DiscoverySearchParams {
  industry_keyword: string;
  country: string;
  state?: string;
  city?: string;
}

function buildLocation(params: DiscoverySearchParams): string {
  return [params.city, params.state, params.country].filter(Boolean).join(", ");
}

export function getWebsitesForCategory(
  categoryId: DiscoverySourceCategory,
): DiscoveryWebsiteOption[] {
  return (
    DISCOVERY_SOURCE_CATEGORIES.find((c) => c.id === categoryId)?.websites ?? []
  );
}

export function getCategoryLabel(categoryId: string): string {
  return (
    DISCOVERY_SOURCE_CATEGORIES.find((c) => c.id === categoryId)?.label ?? categoryId
  );
}

export function getWebsiteLabel(categoryId: string, websiteId: string): string {
  const category = DISCOVERY_SOURCE_CATEGORIES.find((c) => c.id === categoryId);
  return category?.websites.find((w) => w.id === websiteId)?.label ?? websiteId;
}

export function buildSourceSearchUrl(
  categoryId: DiscoverySourceCategory,
  websiteId: string,
  params: DiscoverySearchParams,
): string {
  const industry = encodeURIComponent(params.industry_keyword.trim());
  const location = encodeURIComponent(buildLocation(params));

  if (categoryId === "google_business") {
    const query = encodeURIComponent(
      `${params.industry_keyword.trim()} in ${buildLocation(params)}`,
    );
    if (websiteId === "google_search") {
      return `https://www.google.com/search?q=${query}&tbm=lcl`;
    }
    return `https://www.google.com/maps/search/${query}`;
  }

  if (categoryId === "yelp") {
    return `https://www.yelp.com/search?find_desc=${industry}&find_loc=${location}`;
  }

  const directoryUrls: Record<string, string> = {
    yellow_pages: `https://www.yellowpages.com/search?search_terms=${industry}&geo_location_terms=${location}`,
    manta: `https://www.manta.com/search?search=${industry}&city=${location}`,
    superpages: `https://www.superpages.com/search?C=${location}&T=${industry}`,
    bbb: `https://www.bbb.org/search?find_text=${industry}&find_loc=${location}`,
  };

  return (
    directoryUrls[websiteId] ??
    `https://www.google.com/search?q=${encodeURIComponent(
      `${params.industry_keyword} ${buildLocation(params)} business directory`,
    )}`
  );
}
