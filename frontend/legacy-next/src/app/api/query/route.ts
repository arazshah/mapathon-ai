import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const getBackendURL = (): string => {
  const baseURL =
    process.env.MAPATHON_API_URL?.trim() ||
    "http://127.0.0.1:8000";

  return `${baseURL.replace(/\/+$/, "")}/api/v1/query`;
};

export async function POST(request: NextRequest) {
  let requestBody: unknown;

  try {
    requestBody = await request.json();
  } catch {
    return NextResponse.json(
      {
        success: false,
        message: "بدنه درخواست JSON معتبر نیست.",
      },
      {
        status: 400,
      },
    );
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000);

  try {
    const backendResponse = await fetch(getBackendURL(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(requestBody),
      cache: "no-store",
      signal: controller.signal,
    });

    const rawBody = await backendResponse.text();

    let responseBody: unknown;

    try {
      responseBody = JSON.parse(rawBody);
    } catch {
      responseBody = {
        success: false,
        message: "پاسخ Backend از نوع JSON معتبر نیست.",
        detail: rawBody.slice(0, 1000),
      };
    }

    return NextResponse.json(responseBody, {
      status: backendResponse.status,
    });
  } catch (error) {
    const isTimeout =
      error instanceof Error && error.name === "AbortError";

    return NextResponse.json(
      {
        success: false,
        message: isTimeout
          ? "زمان پاسخ‌گویی Backend بیش از حد طولانی شد."
          : "اتصال به Backend برقرار نشد.",
        detail:
          process.env.NODE_ENV === "development" &&
          error instanceof Error
            ? error.message
            : undefined,
      },
      {
        status: isTimeout ? 504 : 502,
      },
    );
  } finally {
    clearTimeout(timeout);
  }
}
