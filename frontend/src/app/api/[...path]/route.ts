/**
 * Server-side API proxy with request logging.
 * Handles /api/* → FastAPI backend (replaces fragile rewrite-only proxy).
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000/api/v1";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

function log(step: string, detail: Record<string, unknown>) {
  if (process.env.NODE_ENV === "development") {
    console.warn(`[API Proxy] ${step}`, detail);
  }
}

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
): Promise<NextResponse> {
  const path = pathSegments.join("/");
  const query = request.nextUrl.search;
  const targetUrl = `${BACKEND_BASE}/${path}${query}`;
  const started = Date.now();

  log("request_start", {
    method: request.method,
    path,
    targetUrl,
    backendBase: BACKEND_BASE,
  });

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  let body: string | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.text();
    log("request_body", { path, bodyLength: body.length });
  }

  try {
    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
    });

    const responseBody = await backendResponse.arrayBuffer();
    const durationMs = Date.now() - started;

    log("response", {
      path,
      status: backendResponse.status,
      durationMs,
      bodyLength: responseBody.byteLength,
    });

    const responseHeaders = new Headers();
    const contentType = backendResponse.headers.get("content-type");
    if (contentType) {
      responseHeaders.set("content-type", contentType);
    }

    return new NextResponse(responseBody, {
      status: backendResponse.status,
      headers: responseHeaders,
    });
  } catch (error) {
    const durationMs = Date.now() - started;
    const message = error instanceof Error ? error.message : String(error);

    log("backend_unreachable", {
      path,
      targetUrl,
      durationMs,
      error: message,
    });

    return NextResponse.json(
      {
        detail: `Backend unreachable at ${BACKEND_BASE}. Start the API server: uvicorn app.main:app --host 127.0.0.1 --port 8000`,
        proxy_error: message,
      },
      { status: 502 },
    );
  }
}

type RouteContext = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}
